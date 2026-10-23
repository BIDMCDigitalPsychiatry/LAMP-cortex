""" Module for reading binary sensor-stream frames (high-rate accelerometer)

The high-rate accelerometer specs (``lamp.accelerometer10hz`` through
``lamp.accelerometer100hz``) don't use ``sensor_event``. Clients upload
compressed binary frames to ``/participant/{id}/sensor-stream`` instead. This
module downloads those frames, checks them against the LAMP-protocol
sensor-stream contract (``docs/sensor-stream.md``), and returns the records as
a DataFrame.

It lives in ``cortex.utils``, not ``cortex.raw``, because ``cortex.run`` probes
every module in ``cortex.raw`` as a ``sensor_event`` feature.
"""
import numpy as np

__all__ = ['ACCEL_DTYPE', 'SENSOR_STREAM_SPECS', 'SensorStreamError',
           'decode_frame', 'load_sensor_stream']

# One 20-byte little-endian record: epoch ms, then x, y, z in m/s^2.
ACCEL_DTYPE = np.dtype([('timestamp', '<i8'), ('x', '<f4'), ('y', '<f4'), ('z', '<f4')])

SENSOR_STREAM_SPECS = ('lamp.accelerometer10hz', 'lamp.accelerometer20hz',
                       'lamp.accelerometer50hz', 'lamp.accelerometer100hz')


class SensorStreamError(ValueError):
    """ Raised when a sensor-stream frame fails a decoder or integrity check. """


def decode_frame(blob, codec, *, sample_count, codec_format_version,
                 start_timestamp=None, end_timestamp=None):
    """ Decompresses one sensor-stream frame and checks it against its metadata.

    Args:
        blob (bytes): The compressed frame bytes.
        codec (str): ``'openzl'`` or ``'zstd'``.
        sample_count (int): The number of records the metadata declares.
        codec_format_version (int): The OpenZL format version the metadata
            declares (``24``); ``0`` for zstd.
        start_timestamp (int): The first record's timestamp (epoch ms). Optional.
        end_timestamp (int): The last record's timestamp (epoch ms). Optional.

    Returns:
        A NumPy structured array with dtype ``ACCEL_DTYPE``.

    Raises:
        SensorStreamError: The frame fails a decoder check.
        ImportError: The codec's package isn't installed.
    """
    raise NotImplementedError


def load_sensor_stream(participant_id, sensor_spec, start, end, *, ascending=False,
                       session=None, server_address=None, api_key=None):
    """ Downloads and decodes a participant's sensor-stream frames.

    Args:
        participant_id (str): The participant's LAMP id.
        sensor_spec (str): One of ``SENSOR_STREAM_SPECS``.
        start (int): The first timestamp to return, epoch ms (inclusive).
        end (int): The last timestamp to return, epoch ms (inclusive).
        ascending (bool): If True, sort oldest first; else newest first.
        session (requests.Session): The session to send requests with. Optional.
        server_address (str): The LAMP server. Defaults to ``LAMP_SERVER_ADDRESS``.
        api_key (str): The API key. Defaults to ``LAMP_API_KEY``.

    Returns:
        A DataFrame with the columns ``timestamp`` (int64), ``x``, ``y`` and
        ``z`` (float32).
    """
    raise NotImplementedError
