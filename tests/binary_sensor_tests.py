""" Module for unittesting the binary sensor-stream loader and the gps1m raw feature

These tests never talk to a LAMP server: every HTTP call goes to an in-memory
fake, and the golden vectors come from LAMP-protocol
(``test-vectors/sensor-stream/``, copied into ``tests/fixtures/sensor_stream``).
"""
import os
# `import cortex` connects to LAMP and needs credentials; dummy values are enough.
os.environ.setdefault('LAMP_ACCESS_KEY', 'x')
os.environ.setdefault('LAMP_SECRET_KEY', 'x')

# pylint: disable=wrong-import-position
import hashlib
import inspect
import json
import logging
import shutil
import sys
import tempfile
import unittest
from unittest import mock

import compress_pickle
import numpy as np
import requests
import zstandard

import LAMP
import cortex
import cortex.feature_types
import cortex.raw
import cortex.raw.accelerometer
import cortex.raw.gps
from cortex.utils import sensor_stream
from cortex.utils.sensor_stream import (ACCEL_DTYPE, SensorStreamError, decode_frame,
                                        load_sensor_stream)

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'sensor_stream')
SPEC = 'lamp.accelerometer50hz'


def setUpModule():
    """ Silence cortex's DEBUG logging for the whole module. """
    logging.disable(logging.CRITICAL)


def tearDownModule():
    """ Restore logging. """
    logging.disable(logging.NOTSET)


def _read(name):
    with open(os.path.join(FIXTURES, name), 'rb') as f:
        return f.read()


def _meta(name):
    with open(os.path.join(FIXTURES, 'meta.json'), encoding='utf-8') as f:
        return json.load(f)[name]


def _records():
    with open(os.path.join(FIXTURES, 'records.json'), encoding='utf-8') as f:
        return json.load(f)


def _decode_kwargs(meta):
    return {'sample_count': meta['sample_count'],
            'codec_format_version': meta['codec_format_version'],
            'start_timestamp': meta['start_timestamp'],
            'end_timestamp': meta['end_timestamp']}


def _zstd_frame(records):
    """ Packs and zstd-compresses (timestamp, x, y, z) tuples; returns (blob, meta). """
    arr = np.array(records, dtype=ACCEL_DTYPE)
    blob = zstandard.ZstdCompressor(level=3, write_content_size=True).compress(arr.tobytes())
    meta = {'sensor_spec': SPEC,
            'start_timestamp': int(arr['timestamp'][0]),
            'end_timestamp': int(arr['timestamp'][-1]),
            'sample_count': len(arr), 'codec': 'zstd', 'codec_format_version': 0,
            'platform': 'android', 'unit': 'm/s^2', 'byte_length': len(blob),
            'sha256': hashlib.sha256(blob).hexdigest()}
    return blob, meta


class FakeResponse:
    """ The parts of `requests.Response` the loader uses. """

    def __init__(self, status_code=200, json_body=None, content=b'', chunk_size=1000):
        self.status_code = status_code
        self._json = json_body
        self._content = content
        self._chunk_size = chunk_size
        self.closed = False

    def json(self):
        """ Returns the JSON body. """
        return self._json

    def raise_for_status(self):
        """ Raises `requests.HTTPError` for 4xx and 5xx. """
        if self.status_code >= 400:
            raise requests.HTTPError(f'{self.status_code} error', response=self)

    def iter_content(self, chunk_size=1):
        """ Yields the body in small chunks, like a streamed download. """
        del chunk_size
        for i in range(0, len(self._content), self._chunk_size):
            yield self._content[i:i + self._chunk_size]

    def close(self):
        """ Marks the response closed. """
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class FakeServer:
    """ An in-memory sensor-stream server that records every GET. """

    def __init__(self, frames, page_size=1000, list_status=200):
        # frames: list of (file_id, meta, blob), listed in this order.
        self.frames = [(fid, dict(meta, id=fid), blob) for fid, meta, blob in frames]
        self.page_size = page_size
        self.list_status = list_status
        self.calls = []
        self.responses = []

    def get(self, url, **kwargs):
        """ Serves the list and download routes. """
        self.calls.append((url, kwargs))
        path = url.split('/participant/', 1)[1]
        participant, rest = path.split('/', 1)
        assert participant == 'U1', participant
        if rest == 'sensor-stream':
            params = kwargs.get('params') or {}
            cursor = str(params.get('cursor') or '0')
            offset = int(cursor) if cursor.isdigit() else 0
            page = self.frames[offset:offset + self.page_size]
            nxt = offset + self.page_size
            body = {'data': [m for _, m, _ in page],
                    'next': str(nxt) if nxt < len(self.frames) else None}
            resp = FakeResponse(self.list_status, json_body=body)
        else:
            file_id = rest.split('/', 1)[1]
            blob = next(b for fid, _, b in self.frames if fid == file_id)
            resp = FakeResponse(200, content=blob)
        self.responses.append(resp)
        return resp

    def list_calls(self):
        """ Returns the calls to the list route. """
        return [c for c in self.calls if c[0].endswith('/sensor-stream')]

    def download_calls(self):
        """ Returns the calls to the download route. """
        return [c for c in self.calls if not c[0].endswith('/sensor-stream')]

    def session(self):
        """ Returns a mock `requests.Session` routed to this server. """
        sess = mock.Mock(spec=requests.Session)
        sess.get.side_effect = self.get
        return sess


class TestDecodeFrame(unittest.TestCase):
    """ Golden-vector decoding and the contract's decoder checks. """

    def assert_equals_records(self, arr):
        """ Asserts that a decoded array equals records.json bit for bit. """
        recs = _records()
        self.assertEqual(arr.dtype, ACCEL_DTYPE)
        self.assertEqual(len(arr), len(recs))
        np.testing.assert_array_equal(arr['timestamp'],
                                      np.array([r['timestamp'] for r in recs], dtype='<i8'))
        for axis in ('x', 'y', 'z'):
            np.testing.assert_array_equal(arr[axis],
                                          np.array([r[axis] for r in recs], dtype='<f4'))
        self.assertEqual(arr.tobytes(), _read('frame.bin'))

    def test_accel_dtype_is_20_bytes(self):
        self.assertEqual(ACCEL_DTYPE.itemsize, 20)
        self.assertEqual(ACCEL_DTYPE.names, ('timestamp', 'x', 'y', 'z'))

    def test_decodes_golden_openzl(self):
        meta = _meta('frame.openzl')
        arr = decode_frame(_read('frame.openzl'), 'openzl', **_decode_kwargs(meta))
        self.assert_equals_records(arr)

    def test_decodes_golden_zstd(self):
        meta = _meta('frame.zstd')
        arr = decode_frame(_read('frame.zstd'), 'zstd', **_decode_kwargs(meta))
        self.assert_equals_records(arr)

    def test_decodes_zstd_without_content_size(self):
        meta = _meta('frame_nosize.zstd')
        arr = decode_frame(_read('frame_nosize.zstd'), 'zstd', **_decode_kwargs(meta))
        self.assert_equals_records(arr)

    def test_decodes_single_record_openzl(self):
        meta = _meta('frame_single.openzl')
        arr = decode_frame(_read('frame_single.openzl'), 'openzl', **_decode_kwargs(meta))
        self.assertEqual(arr.tobytes(), _read('frame_single.bin'))
        self.assertEqual(int(arr['timestamp'][0]), meta['start_timestamp'])

    def test_timestamps_are_optional(self):
        arr = decode_frame(_read('frame.openzl'), 'openzl', sample_count=500,
                           codec_format_version=24)
        self.assertEqual(len(arr), 500)

    def test_rejects_truncated_openzl(self):
        meta = _meta('frame.openzl')
        with self.assertRaises(SensorStreamError):
            decode_frame(_read('frame.openzl')[:-10], 'openzl', **_decode_kwargs(meta))

    def test_rejects_truncated_zstd(self):
        meta = _meta('frame.zstd')
        with self.assertRaises(SensorStreamError):
            decode_frame(_read('frame.zstd')[:-10], 'zstd', **_decode_kwargs(meta))

    def test_rejects_length_not_multiple_of_20(self):
        blob = zstandard.ZstdCompressor().compress(_read('frame.bin')[:-1])
        with self.assertRaisesRegex(SensorStreamError, 'multiple of 20'):
            decode_frame(blob, 'zstd', sample_count=500, codec_format_version=0)

    def test_rejects_wrong_sample_count_openzl(self):
        kwargs = dict(_decode_kwargs(_meta('frame.openzl')), sample_count=499)
        with self.assertRaisesRegex(SensorStreamError, 'sample_count'):
            decode_frame(_read('frame.openzl'), 'openzl', **kwargs)

    def test_rejects_wrong_sample_count_zstd(self):
        for name in ('frame.zstd', 'frame_nosize.zstd'):
            for count in (499, 501):
                with self.subTest(name=name, count=count):
                    kwargs = dict(_decode_kwargs(_meta(name)), sample_count=count)
                    with self.assertRaises(SensorStreamError):
                        decode_frame(_read(name), 'zstd', **kwargs)

    def test_rejects_non_positive_sample_count(self):
        with self.assertRaises(SensorStreamError):
            decode_frame(_read('frame.zstd'), 'zstd', sample_count=0, codec_format_version=0)

    def test_rejects_wrong_format_version(self):
        kwargs = dict(_decode_kwargs(_meta('frame.openzl')), codec_format_version=23)
        with self.assertRaisesRegex(SensorStreamError, 'format version'):
            decode_frame(_read('frame.openzl'), 'openzl', **kwargs)

    def test_rejects_mismatched_start_timestamp(self):
        kwargs = dict(_decode_kwargs(_meta('frame.openzl')), start_timestamp=1790000100001)
        with self.assertRaisesRegex(SensorStreamError, 'start_timestamp'):
            decode_frame(_read('frame.openzl'), 'openzl', **kwargs)

    def test_rejects_mismatched_end_timestamp(self):
        kwargs = dict(_decode_kwargs(_meta('frame.zstd')), end_timestamp=1790000109981)
        with self.assertRaisesRegex(SensorStreamError, 'end_timestamp'):
            decode_frame(_read('frame.zstd'), 'zstd', **kwargs)

    def test_checks_run_in_contract_order(self):
        # Length (2) before count (3).
        blob = zstandard.ZstdCompressor().compress(_read('frame.bin')[:-1])
        with self.assertRaisesRegex(SensorStreamError, 'multiple of 20'):
            decode_frame(blob, 'zstd', sample_count=7, codec_format_version=0)
        # Count (3) before format version (4) and timestamps (5).
        with self.assertRaisesRegex(SensorStreamError, 'sample_count'):
            decode_frame(_read('frame.openzl'), 'openzl', sample_count=499,
                         codec_format_version=23, start_timestamp=1, end_timestamp=2)
        # Format version (4) before timestamps (5).
        with self.assertRaisesRegex(SensorStreamError, 'format version'):
            decode_frame(_read('frame.openzl'), 'openzl', sample_count=500,
                         codec_format_version=23, start_timestamp=1, end_timestamp=2)

    def test_rejects_garbage_zstd(self):
        with self.assertRaises(SensorStreamError):
            decode_frame(b'not a zstd frame', 'zstd', sample_count=1, codec_format_version=0)

    def test_rejects_unknown_codec(self):
        with self.assertRaisesRegex(SensorStreamError, 'codec'):
            decode_frame(_read('frame.bin'), 'lz4', sample_count=500, codec_format_version=0)

    def test_missing_openzl_points_to_binary_extra(self):
        with mock.patch.dict(sys.modules, {'openzl': None, 'openzl.ext': None}):
            with self.assertRaisesRegex(ImportError, 'binary'):
                decode_frame(_read('frame.openzl'), 'openzl', sample_count=500,
                             codec_format_version=24)

    def test_missing_zstandard_points_to_binary_extra(self):
        with mock.patch.dict(sys.modules, {'zstandard': None}):
            with self.assertRaisesRegex(ImportError, 'binary'):
                decode_frame(_read('frame.zstd'), 'zstd', sample_count=500,
                             codec_format_version=0)


class TestLoadSensorStream(unittest.TestCase):
    """ The HTTP loader, run against an in-memory fake server. """

    START = 1790000100000
    END = 1790000109980

    def setUp(self):
        env = {k: v for k, v in os.environ.items()
               if k not in ('LAMP_API_KEY', 'LAMP_SERVER_ADDRESS')}
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def golden_server(**kwargs):
        """ A server holding the golden OpenZL frame. """
        return FakeServer([('f1', _meta('frame.openzl'), _read('frame.openzl'))], **kwargs)

    def load(self, server, **kwargs):
        """ Calls the loader with a mock session and explicit credentials. """
        kwargs.setdefault('server_address', 'localhost:3000')
        kwargs.setdefault('api_key', 'test-key')
        return load_sensor_stream('U1', SPEC, kwargs.pop('start', self.START),
                                  kwargs.pop('end', self.END),
                                  session=server.session(), **kwargs)

    def test_returns_records_with_exact_columns_and_dtypes(self):
        df = self.load(self.golden_server(), ascending=True)
        self.assertEqual(list(df.columns), ['timestamp', 'x', 'y', 'z'])
        self.assertEqual([str(t) for t in df.dtypes], ['int64', 'float32', 'float32', 'float32'])
        recs = _records()
        self.assertEqual(df['timestamp'].tolist(), [r['timestamp'] for r in recs])
        np.testing.assert_array_equal(df['x'].to_numpy(),
                                      np.array([r['x'] for r in recs], dtype='<f4'))
        self.assertEqual(list(df.index), list(range(len(recs))))

    def test_default_order_is_newest_first(self):
        df = self.load(self.golden_server())
        ts = df['timestamp'].tolist()
        self.assertEqual(ts, sorted(ts, reverse=True))
        self.assertEqual(ts[0], self.END)
        self.assertEqual(list(df.index), list(range(len(ts))))

    def test_ascending_true_is_oldest_first(self):
        df = self.load(self.golden_server(), ascending=True)
        ts = df['timestamp'].tolist()
        self.assertEqual(ts, sorted(ts))
        self.assertEqual(ts[0], self.START)

    def test_sends_api_key_header_and_adds_https(self):
        server = self.golden_server()
        self.load(server, server_address='localhost:3000', api_key='secret-key')
        self.assertTrue(server.calls)
        for url, kwargs in server.calls:
            self.assertTrue(url.startswith('https://localhost:3000/participant/U1/sensor-stream'),
                            url)
            self.assertEqual(kwargs['headers']['x-api-key'], 'secret-key')
            self.assertNotIn('Authorization', kwargs['headers'])

    def test_reads_key_and_address_from_environment(self):
        server = self.golden_server()
        with mock.patch.dict(os.environ, {'LAMP_API_KEY': 'env-key',
                                          'LAMP_SERVER_ADDRESS': 'lamp.example.org/'}):
            load_sensor_stream('U1', SPEC, self.START, self.END, session=server.session())
        for url, kwargs in server.calls:
            self.assertTrue(url.startswith('https://lamp.example.org/participant/U1/'), url)
            self.assertEqual(kwargs['headers']['x-api-key'], 'env-key')

    def test_keeps_an_explicit_scheme(self):
        server = self.golden_server()
        self.load(server, server_address='http://127.0.0.1:3000')
        for url, _ in server.calls:
            self.assertTrue(url.startswith('http://127.0.0.1:3000/participant/U1/'), url)

    def test_missing_api_key_raises_before_any_request(self):
        server = self.golden_server()
        session = server.session()
        with self.assertRaisesRegex(ValueError, 'LAMP_API_KEY'):
            load_sensor_stream('U1', SPEC, self.START, self.END, session=session,
                               server_address='localhost:3000')
        session.get.assert_not_called()

    def test_rejects_unknown_sensor_spec(self):
        with self.assertRaises(ValueError):
            load_sensor_stream('U1', 'lamp.gps', self.START, self.END,
                               session=self.golden_server().session(),
                               server_address='localhost:3000', api_key='k')

    def test_list_query_parameters(self):
        server = self.golden_server()
        self.load(server)
        (url, kwargs), = server.list_calls()
        self.assertEqual(url, 'https://localhost:3000/participant/U1/sensor-stream')
        params = kwargs['params']
        self.assertEqual(params['sensor_spec'], SPEC)
        self.assertEqual(int(params['from']), self.START)
        # `end` is inclusive; the server's `to` is exclusive.
        self.assertEqual(int(params['to']), self.END + 1)
        self.assertNotIn('cursor', params)

    def test_pages_through_next(self):
        blob_b, meta_b = _zstd_frame([(1790000400000, 1.0, 2.0, 3.0)])
        blob_c, meta_c = _zstd_frame([(1790000700000, 4.0, 5.0, 6.0)])
        server = FakeServer([('f1', _meta('frame.openzl'), _read('frame.openzl')),
                             ('f2', meta_b, blob_b), ('f3', meta_c, blob_c)], page_size=1)
        df = self.load(server, end=1790000700000, ascending=True)
        cursors = [kw['params'].get('cursor') for _, kw in server.list_calls()]
        self.assertEqual(cursors, [None, '1', '2'])
        self.assertEqual(len(df), 502)
        self.assertEqual(df['timestamp'].iloc[-1], 1790000700000)

    def test_downloads_each_frame_streamed(self):
        server = self.golden_server()
        self.load(server)
        (url, kwargs), = server.download_calls()
        self.assertEqual(url, 'https://localhost:3000/participant/U1/sensor-stream/f1')
        self.assertIs(kwargs.get('stream'), True)
        self.assertTrue(all(r.closed for r in server.responses))

    def test_sha256_mismatch_raises(self):
        meta = dict(_meta('frame.openzl'), sha256='0' * 64)
        server = FakeServer([('f1', meta, _read('frame.openzl'))])
        with self.assertRaisesRegex(SensorStreamError, 'sha256'):
            self.load(server)

    def test_byte_length_mismatch_raises(self):
        meta = dict(_meta('frame.openzl'), byte_length=4187)
        server = FakeServer([('f1', meta, _read('frame.openzl'))])
        with self.assertRaisesRegex(SensorStreamError, 'byte_length'):
            self.load(server)

    def test_repeated_cursor_raises_instead_of_looping(self):
        server = self.golden_server(page_size=1)
        original = server.get

        def stuck_get(url, **kwargs):
            resp = original(url, **kwargs)
            if url.endswith('/sensor-stream'):
                resp._json['next'] = 'same'  # pylint: disable=protected-access
            return resp

        server.get = stuck_get
        with self.assertRaisesRegex(SensorStreamError, 'cursor'):
            self.load(server)

    def test_start_after_end_raises(self):
        with self.assertRaises(ValueError):
            self.load(self.golden_server(), start=self.END, end=self.START)

    def test_decoder_check_failure_raises(self):
        meta = dict(_meta('frame.openzl'), sample_count=499)
        server = FakeServer([('f1', meta, _read('frame.openzl'))])
        with self.assertRaises(SensorStreamError):
            self.load(server)

    def test_http_error_propagates(self):
        server = self.golden_server(list_status=403)
        with self.assertRaises(requests.HTTPError):
            self.load(server)

    def test_merges_frames_in_one_window_and_drops_cross_frame_duplicates(self):
        recs = _records()
        first, last = recs[0], recs[-1]
        # A third frame in the same window: one record that shares a timestamp
        # with record 0 but differs in x (kept), one exact copy of the last
        # record (dropped), and one new record (kept).
        extra = [(first['timestamp'], first['x'] + 1.0, first['y'], first['z']),
                 (last['timestamp'], last['x'], last['y'], last['z']),
                 (last['timestamp'] + 10, 0.5, 0.25, 9.75)]
        blob_c, meta_c = _zstd_frame(extra)
        server = FakeServer([
            ('f1', _meta('frame.openzl'), _read('frame.openzl')),
            # The same 500 records again, as a zstd frame (a re-upload).
            ('f2', _meta('frame.zstd'), _read('frame.zstd')),
            ('f3', meta_c, blob_c)])
        df = self.load(server, end=last['timestamp'] + 10, ascending=True)
        self.assertEqual(len(df), 502)
        self.assertFalse(df.duplicated().any())
        at_first = df[df['timestamp'] == first['timestamp']]
        self.assertEqual(len(at_first), 2)
        self.assertEqual(sorted(at_first['x'].tolist()),
                         sorted([np.float32(first['x']), np.float32(first['x'] + 1.0)]))
        self.assertEqual((df['timestamp'] == last['timestamp']).sum(), 1)
        self.assertEqual(df['timestamp'].tolist(), sorted(df['timestamp'].tolist()))

    def test_keeps_identical_records_within_one_frame(self):
        # Two identical readings in one ms (a device at rest at 100 Hz) are
        # real samples; the contract's "Merging frames" rule keeps both.
        rest = (1790000100010, 0.0, 0.0, 9.80665)
        blob, meta = _zstd_frame([(1790000100000, 0.0, 0.0, 9.80665), rest, rest,
                                  (1790000100020, 0.0, 0.0, 9.80665)])
        df = self.load(FakeServer([('f1', meta, blob)]), start=1790000100000,
                       end=1790000100020, ascending=True)
        self.assertEqual(len(df), 4)
        self.assertEqual(df['timestamp'].tolist(),
                         [1790000100000, 1790000100010, 1790000100010, 1790000100020])

    def test_cross_frame_duplicates_keep_the_largest_in_frame_count(self):
        rec = (1790000100010, 0.5, 0.25, 9.75)
        other = (1790000100020, 1.0, 2.0, 3.0)
        blob_a, meta_a = _zstd_frame([rec, rec])
        blob_b, meta_b = _zstd_frame([rec])
        blob_c, meta_c = _zstd_frame([rec, rec, rec, other])
        cases = {'A=[r,r] then B=[r]': ([('a', meta_a, blob_a), ('b', meta_b, blob_b)], 2),
                 'B=[r] then A=[r,r]': ([('b', meta_b, blob_b), ('a', meta_a, blob_a)], 2),
                 'A, B, then C=[r,r,r,o]': ([('a', meta_a, blob_a), ('b', meta_b, blob_b),
                                             ('c', meta_c, blob_c)], 3)}
        for name, (frames, copies) in cases.items():
            with self.subTest(name):
                df = self.load(FakeServer(frames), start=1790000100000,
                               end=1790000100020, ascending=True)
                self.assertEqual((df['timestamp'] == rec[0]).sum(), copies)
                self.assertEqual(len(df), copies + (len(frames) == 3))

    def test_trims_records_to_the_inclusive_range(self):
        start, end = self.START + 1000, self.START + 2000
        df = self.load(self.golden_server(), start=start, end=end, ascending=True)
        self.assertEqual(df['timestamp'].iloc[0], start)
        self.assertEqual(df['timestamp'].iloc[-1], end)
        self.assertEqual(len(df), 51)

    def test_empty_result_has_the_right_dtypes(self):
        df = self.load(FakeServer([]))
        self.assertEqual(len(df), 0)
        self.assertEqual(list(df.columns), ['timestamp', 'x', 'y', 'z'])
        self.assertEqual([str(t) for t in df.dtypes], ['int64', 'float32', 'float32', 'float32'])

    def test_default_session_uses_requests_session_get(self):
        server = self.golden_server()

        def fake_get(_session, url, **kwargs):
            return server.get(url, **kwargs)

        with mock.patch.object(requests.Session, 'get', autospec=True,
                               side_effect=fake_get) as patched:
            df = load_sensor_stream('U1', SPEC, self.START, self.END,
                                    server_address='localhost:3000', api_key='k')
        self.assertEqual(patched.call_count, 2)
        self.assertEqual(len(df), 500)
        self.assertEqual(server.calls[0][1]['headers']['x-api-key'], 'k')


class TestRawRegistration(unittest.TestCase):
    """ The gps1m raw feature and the location of the binary loader. """

    def test_gps1m_is_registered_as_a_raw_feature(self):
        features = {f['name']: f for f in cortex.feature_types.all_features()}
        self.assertIn('lamp.gps1m', features)
        self.assertEqual(features['lamp.gps1m']['type'], 'raw')
        self.assertEqual(features['lamp.gps1m']['callable'].__name__, 'gps1m')
        self.assertIn('lamp.gps1m', features['lamp.gps1m']['dependencies'])

    def test_gps1m_is_visible_to_the_run_probe(self):
        # cortex.run calls getattr(mod, mod_name) for every module in cortex.raw.
        modules = dict(inspect.getmembers(cortex.raw, inspect.ismodule))
        self.assertIn('gps1m', modules)
        self.assertTrue(callable(getattr(modules['gps1m'], 'gps1m', None)))

    def test_sensor_stream_is_not_a_raw_module(self):
        modules = dict(inspect.getmembers(cortex.raw, inspect.ismodule))
        self.assertNotIn('sensor_stream', modules)
        self.assertIs(sensor_stream.load_sensor_stream, load_sensor_stream)


class TestCachePrefix(unittest.TestCase):
    """ Regression: a raw feature's cache lookup must not match a longer name. """

    API_DATA = {'data': [{'timestamp': 400,
                          'data': {'latitude': 1.0, 'longitude': 2.0, 'altitude': 3.0,
                                   'accuracy': 4.0, 'x': 0.1, 'y': 0.2, 'z': 0.3}}]}

    def setUp(self):
        self.cache_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.cache_dir)
        patcher = mock.patch.dict(os.environ, {'CORTEX_CACHE_DIR': self.cache_dir})
        patcher.start()
        self.addCleanup(patcher.stop)
        api = mock.patch.object(LAMP.SensorEvent, 'all_by_participant',
                                return_value=self.API_DATA)
        self.api = api.start()
        self.addCleanup(api.stop)

    def write_cache(self, prefix, data):
        """ Writes a cache file the way raw_feature does. """
        path = os.path.join(self.cache_dir, f'{prefix}_U1_0_1000.cortex')
        compress_pickle.dump(data, path, compression=None, set_default_extension=False)

    @staticmethod
    def raw_callable(name):
        """ Returns the registered callable for a raw feature, or None. """
        for feature in cortex.feature_types.all_features():
            if feature['name'] == name and feature['type'] == 'raw':
                return feature['callable']
        return None

    def test_gps_ignores_a_gps1m_cache_file(self):
        self.write_cache('gps1m', [{'timestamp': 500, 'latitude': 9.9}])
        result = cortex.raw.gps.gps(id='U1', start=0, end=1000, cache=True)
        self.assertEqual([r['timestamp'] for r in result['data']], [400])
        self.assertEqual(self.api.call_args.kwargs['origin'], 'lamp.gps')

    def test_accelerometer_ignores_an_accelerometer100hz_cache_file(self):
        self.write_cache('accelerometer100hz', [{'timestamp': 500, 'x': 9.9}])
        result = cortex.raw.accelerometer.accelerometer(id='U1', start=0, end=1000, cache=True)
        self.assertEqual([r['timestamp'] for r in result['data']], [400])
        self.assertEqual(self.api.call_args.kwargs['origin'], 'lamp.accelerometer')

    def test_gps_still_uses_its_own_cache_file(self):
        self.write_cache('gps1m', [{'timestamp': 500, 'latitude': 9.9}])
        self.write_cache('gps', [{'timestamp': 600, 'latitude': 8.8}])
        result = cortex.raw.gps.gps(id='U1', start=0, end=1000, cache=True)
        self.assertEqual([r['timestamp'] for r in result['data']], [600])
        self.api.assert_not_called()

    def test_gps1m_ignores_a_gps_cache_file(self):
        gps1m = self.raw_callable('lamp.gps1m')
        self.assertIsNotNone(gps1m, 'lamp.gps1m is not registered')
        self.write_cache('gps', [{'timestamp': 600, 'latitude': 8.8}])
        result = gps1m(id='U1', start=0, end=1000, cache=True)
        self.assertEqual([r['timestamp'] for r in result['data']], [400])
        self.assertEqual(self.api.call_args.kwargs['origin'], 'lamp.gps1m')


if __name__ == '__main__':
    unittest.main()
