""" Module for reading binary sensor-stream frames (high-rate accelerometer)

The high-rate accelerometer specs (``lamp.accelerometer10hz`` through
``lamp.accelerometer100hz``) don't use ``sensor_event``. Clients upload
compressed binary frames to ``/participant/{id}/sensor-stream`` instead. This
module downloads those frames, checks them against the LAMP-protocol
sensor-stream contract (``docs/sensor-stream.md``), and returns the records as
a DataFrame.

It lives in ``cortex.utils``, not ``cortex.raw``, because ``cortex.run`` probes
every module in ``cortex.raw`` as a ``sensor_event`` feature.

Decoding needs the optional ``binary`` extra (``openzl`` and ``zstandard``).
"""
import hashlib
import os
import struct
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests

__all__ = ['ACCEL_DTYPE', 'SENSOR_STREAM_SPECS', 'SensorStreamError',
           'decode_frame', 'load_sensor_stream']

# One 20-byte little-endian record: epoch ms, then x, y, z in m/s^2.
ACCEL_DTYPE = np.dtype([('timestamp', '<i8'), ('x', '<f4'), ('y', '<f4'), ('z', '<f4')])
RECORD_SIZE = ACCEL_DTYPE.itemsize

SENSOR_STREAM_SPECS = ('lamp.accelerometer10hz', 'lamp.accelerometer20hz',
                       'lamp.accelerometer50hz', 'lamp.accelerometer100hz')

# An OpenZL frame starts with a little-endian uint32 magic number that encodes
# the format version; the Python binding doesn't expose it otherwise.
OPENZL_MAGIC_BASE = 0xD7B1A5C0

DEFAULT_SERVER_ADDRESS = 'api.lamp.digital'
LIST_PAGE_LIMIT = 1000
DOWNLOAD_CHUNK_SIZE = 64 * 1024
REQUEST_TIMEOUT = 60

_COLUMNS = ['timestamp', 'x', 'y', 'z']
_EXTRA_HINT = ("Install the 'binary' extra to read sensor-stream frames: "
               "pip install 'LAMP-cortex[binary]'")


class SensorStreamError(ValueError):
    """ Raised when a sensor-stream frame fails a decoder or integrity check. """


def _import_openzl():
    """ Imports ``openzl.ext`` on first use. """
    try:
        import openzl.ext as zl  # pylint: disable=import-outside-toplevel
    except ImportError as err:
        raise ImportError(f"Decoding codec 'openzl' needs the openzl package. {_EXTRA_HINT}") \
            from err
    return zl


def _import_zstandard():
    """ Imports ``zstandard`` on first use. """
    try:
        import zstandard  # pylint: disable=import-outside-toplevel
    except ImportError as err:
        raise ImportError(f"Decoding codec 'zstd' needs the zstandard package. {_EXTRA_HINT}") \
            from err
    return zstandard


def _check_length(n_bytes, sample_count):
    """ Applies decoder checks 2 and 3 to a decompressed length. """
    if n_bytes % RECORD_SIZE != 0:
        raise SensorStreamError(f"Decompressed length {n_bytes} is not a multiple of "
                                f"{RECORD_SIZE}.")
    if n_bytes // RECORD_SIZE != sample_count:
        raise SensorStreamError(f"Frame holds {n_bytes // RECORD_SIZE} records, but "
                                f"sample_count is {sample_count}.")


def _decompress_openzl(blob):
    """ Decompresses an OpenZL frame and applies decoder check 1. """
    zl = _import_openzl()
    try:
        outputs = zl.DCtx().decompress(blob)
    except Exception as err:  # the binding raises RuntimeError for corrupt input
        raise SensorStreamError(f"OpenZL couldn't decode the frame: {err}") from err
    if len(outputs) != 1:
        raise SensorStreamError(f"OpenZL frame has {len(outputs)} outputs; expected 1.")
    return outputs[0].content.as_bytes()


def _decompress_zstd(blob, sample_count):
    """ Decompresses a zstd frame, with or without a content size. """
    zstandard = _import_zstandard()
    max_size = sample_count * RECORD_SIZE
    try:
        declared = zstandard.get_frame_parameters(blob).content_size
    except zstandard.ZstdError as err:
        raise SensorStreamError(f"zstd couldn't read the frame header: {err}") from err
    # Check a declared size before allocating it, so a bad header can't
    # trigger a large allocation.
    if declared != zstandard.CONTENTSIZE_UNKNOWN:
        _check_length(declared, sample_count)
    try:
        raw = zstandard.ZstdDecompressor().decompress(blob, max_output_size=max_size)
        # decompress() reads only the first zstd frame and ignores what follows
        # it. Decode again, now bounded by the size above, to find where that
        # frame ends, and reject a blob with anything after it.
        dobj = zstandard.ZstdDecompressor().decompressobj()
        dobj.decompress(blob)
    except zstandard.ZstdError as err:
        raise SensorStreamError(f"zstd couldn't decode the frame within sample_count * "
                                f"{RECORD_SIZE} bytes: {err}") from err
    if not dobj.eof:
        raise SensorStreamError("The zstd frame is incomplete.")
    if dobj.unused_data:
        raise SensorStreamError(f"The blob has {len(dobj.unused_data)} bytes after the zstd "
                                f"frame; expected exactly one frame.")
    return raw


def decode_frame(blob, codec, *, sample_count, codec_format_version,  # pylint: disable=too-many-arguments
                 start_timestamp=None, end_timestamp=None):
    """ Decompresses one sensor-stream frame and checks it against its metadata.

    The checks run in the contract's order, and the first failure raises:
    one OpenZL output, a length that's a multiple of 20, ``sample_count``
    records, the OpenZL format version, then the first and last timestamps.
    A zstd blob must hold exactly one frame, with no bytes after it.

    Args:
        blob (bytes): The compressed frame bytes.
        codec (str): ``'openzl'`` or ``'zstd'``.
        sample_count (int): The number of records the metadata declares.
        codec_format_version (int): The OpenZL format version the metadata
            declares (``24``); ``0`` for zstd.
        start_timestamp (int): The first record's timestamp (epoch ms). Optional;
            skipped when None.
        end_timestamp (int): The last record's timestamp (epoch ms). Optional;
            skipped when None.

    Returns:
        A NumPy structured array with dtype ``ACCEL_DTYPE``.
        Example:

        array([(1790000100000, 0., 0.2, 9.80665), ...], dtype=ACCEL_DTYPE)

    Raises:
        SensorStreamError: The frame fails a decoder check, or the codec is
            unknown.
        ImportError: The codec's package isn't installed.
    """
    blob = bytes(blob)
    sample_count = int(sample_count)
    if sample_count < 1:
        raise SensorStreamError(f"sample_count must be at least 1, not {sample_count}.")

    if codec == 'openzl':
        raw = _decompress_openzl(blob)
    elif codec == 'zstd':
        raw = _decompress_zstd(blob, sample_count)
    else:
        raise SensorStreamError(f"Unknown codec {codec!r}; expected 'openzl' or 'zstd'.")

    _check_length(len(raw), sample_count)

    if codec == 'openzl':
        version = struct.unpack('<I', blob[:4])[0] - OPENZL_MAGIC_BASE
        if version != int(codec_format_version):
            raise SensorStreamError(f"OpenZL format version {version} doesn't match "
                                    f"codec_format_version {codec_format_version}.")

    records = np.frombuffer(raw, dtype=ACCEL_DTYPE).copy()
    first, last = int(records['timestamp'][0]), int(records['timestamp'][-1])
    if start_timestamp is not None and first != int(start_timestamp):
        raise SensorStreamError(f"First record is at {first}, but start_timestamp is "
                                f"{start_timestamp}.")
    if end_timestamp is not None and last != int(end_timestamp):
        raise SensorStreamError(f"Last record is at {last}, but end_timestamp is "
                                f"{end_timestamp}.")
    return records


def _base_url(server_address):
    """ Returns the server's base URL, adding ``https://`` when there's no scheme. """
    address = (server_address or os.getenv('LAMP_SERVER_ADDRESS')
               or DEFAULT_SERVER_ADDRESS).strip().rstrip('/')
    if '://' not in address:
        address = 'https://' + address
    return address


def _list_frames(session, url, headers, params):
    """ Yields frame metadata from every page of the list endpoint. """
    seen = set()
    while True:
        response = session.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        try:
            response.raise_for_status()
            body = response.json()
        finally:
            response.close()
        yield from body.get('data') or []
        cursor = body.get('next')
        if not cursor:
            return
        if cursor in seen:
            raise SensorStreamError(f"The server repeated the paging cursor {cursor!r}.")
        seen.add(cursor)
        params = dict(params, cursor=cursor)


def _download_frame(session, url, headers, meta):
    """ Streams one frame's bytes and checks its length and sha256. """
    digest = hashlib.sha256()
    data = bytearray()
    response = session.get(url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT)
    try:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
            if chunk:
                digest.update(chunk)
                data.extend(chunk)
    finally:
        response.close()
    expected_length = meta.get('byte_length')
    if expected_length is not None and len(data) != int(expected_length):
        raise SensorStreamError(f"Frame {meta.get('id')} has {len(data)} bytes, but "
                                f"byte_length is {expected_length}.")
    if digest.hexdigest() != str(meta.get('sha256', '')).lower():
        raise SensorStreamError(f"Frame {meta.get('id')} failed the sha256 check.")
    return bytes(data)


def _empty_frame():
    """ Returns an empty DataFrame with the loader's columns and dtypes. """
    return pd.DataFrame({'timestamp': pd.Series(dtype='int64'),
                         'x': pd.Series(dtype='float32'),
                         'y': pd.Series(dtype='float32'),
                         'z': pd.Series(dtype='float32')})


def _merge(arrays, start, end, ascending):
    """ Merges decoded frames into one DataFrame trimmed to ``[start, end]``. """
    if not arrays:
        return _empty_frame()
    frames = []
    for records in arrays:
        records = records[(records['timestamp'] >= int(start))
                          & (records['timestamp'] <= int(end))]
        frame = pd.DataFrame({name: records[name] for name in _COLUMNS})
        # Number each copy of a record within its frame: 0, 1, 2, ...
        frame['_occurrence'] = frame.groupby(_COLUMNS, sort=False, dropna=False).cumcount()
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True)
    # Frames of one window can repeat records (a re-upload or an overlapping
    # partial frame). Drop a record only when the same copy of it appeared in
    # an earlier frame, so identical records inside one frame stay: a record
    # keeps as many copies as the frame that holds the most.
    df = df.drop_duplicates(keep='first').drop(columns='_occurrence')
    df = df.sort_values('timestamp', kind='mergesort')
    if not ascending:
        df = df.iloc[::-1]
    return df.reset_index(drop=True).astype({'timestamp': 'int64', 'x': 'float32',
                                             'y': 'float32', 'z': 'float32'})


def load_sensor_stream(participant_id, sensor_spec, start, end, *,  # pylint: disable=too-many-arguments
                       ascending=False, session=None, server_address=None, api_key=None):
    """ Downloads and decodes a participant's sensor-stream frames.

    Lists every frame that overlaps ``[start, end]``, downloads each one,
    checks its sha256 and the contract's decoder checks, and merges the
    records. A window can hold several frames (after a restart or a late
    batch), so a record is dropped when an identical record (all four
    fields equal) appears in a different frame. Identical records inside one
    frame are real samples that share a millisecond, so they're kept, and
    records that share a timestamp but differ are kept.

    Args:
        participant_id (str): The participant's LAMP id.
        sensor_spec (str): One of ``SENSOR_STREAM_SPECS``.
        start (int): The first timestamp to return, epoch ms (inclusive).
        end (int): The last timestamp to return, epoch ms (inclusive).
        ascending (bool): If True, sort oldest first; else newest first (the
            order of ``cortex.raw`` features). Records with equal timestamps
            keep their stored order when ascending; descending is the exact
            reverse.
        session (requests.Session): The session to send requests with. If None,
            a new session is opened and closed.
        server_address (str): The LAMP server, with or without a scheme.
            Defaults to ``LAMP_SERVER_ADDRESS``, then ``api.lamp.digital``.
            ``https://`` is added when there's no scheme. For a server
            without TLS, pass ``'http://...'`` here; don't put a scheme in
            ``LAMP_SERVER_ADDRESS``, because ``LAMP.connect`` always adds
            ``https://`` to it.
        api_key (str): The API key, sent as ``x-api-key``. Defaults to
            ``LAMP_API_KEY``.

    Returns:
        A DataFrame with the columns ``timestamp`` (int64, epoch ms), ``x``,
        ``y`` and ``z`` (float32, m/s^2), and a 0-based index.
        Example:

               timestamp         x    y         z
        0  1790000109980  0.012345  0.2  9.806650
        1  1790000109960  0.045678  0.2  9.816584

    Raises:
        ValueError: ``sensor_spec`` isn't a sensor-stream spec, ``start`` is
            after ``end``, or there's no API key.
        SensorStreamError: A frame fails its sha256 or a decoder check.
        requests.HTTPError: The server returns an error status.
        ImportError: The ``binary`` extra isn't installed.
    """
    if sensor_spec not in SENSOR_STREAM_SPECS:
        raise ValueError(f"sensor_spec must be one of {SENSOR_STREAM_SPECS}, "
                         f"not {sensor_spec!r}.")
    if int(start) > int(end):
        raise ValueError("'start' must not be after 'end'.")
    api_key = api_key or os.getenv('LAMP_API_KEY')
    if not api_key:
        raise ValueError("Set `LAMP_API_KEY` (or pass api_key) to read sensor-stream frames.")

    headers = {'x-api-key': api_key}
    list_url = (f"{_base_url(server_address)}/participant/"
                f"{quote(str(participant_id), safe='')}/sensor-stream")
    params = {'sensor_spec': sensor_spec, 'from': int(start), 'to': int(end) + 1,
              'limit': LIST_PAGE_LIMIT}
    own_session = session is None
    if own_session:
        session = requests.Session()
    arrays = []
    try:
        for meta in _list_frames(session, list_url, headers, params):
            blob = _download_frame(session, f"{list_url}/{quote(str(meta['id']), safe='')}",
                                   headers, meta)
            arrays.append(decode_frame(blob, meta['codec'],
                                       sample_count=meta['sample_count'],
                                       codec_format_version=meta['codec_format_version'],
                                       start_timestamp=meta['start_timestamp'],
                                       end_timestamp=meta['end_timestamp']))
    finally:
        if own_session:
            session.close()
    return _merge(arrays, start, end, ascending)
