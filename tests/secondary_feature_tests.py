""" Module for unittesting primary features """
import unittest
import sys
import os
import math
import pandas as pd
import logging
import cortex
import cortex.secondary as secondary
import LAMP
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
            os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))


class TestSecondary(unittest.TestCase):
    # pylint: disable=invalid-sequence-index
    """ Class for testing secondary features """
    MS_IN_DAY = 60 * 60 * 24 * 1000
    TEST_PARTICIPANT = "U26468383"
    EMPTY_PARTICIPANT = "U5704591513"
    TEST_END_TIME = 1583532324130 + 30 * MS_IN_DAY
    TEST_START_TIME_JERK = 1584137124130

    def setUp(self):
        """ Setup the tests """
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)

    # 0. bluetooth_device_count
    def test_device_count_no_data(self):
        # Test if the participant has no data
        ret0 = secondary.bluetooth_device_count.bluetooth_device_count(id=self.EMPTY_PARTICIPANT,
                                           start=self.TEST_END_TIME - 3 * self.MS_IN_DAY,
                                           end=self.TEST_END_TIME,
                                           resolution=self.MS_IN_DAY)
        for x in ret0['data']:
            self.assertEqual(x['value'], None)

    # 1. data_quality
    def test_data_quality_no_data(self):
        # Test if the participant has no data
        ret0 = secondary.data_quality.data_quality(id=self.EMPTY_PARTICIPANT,
                                           start=self.TEST_END_TIME - 3 * self.MS_IN_DAY,
                                           end=self.TEST_END_TIME,
                                           resolution=self.MS_IN_DAY,
                                           feature="gps")
        for x in ret0['data']:
            self.assertEqual(x['value'], 0)

    def test_data_quality_undefined_feature(self):
        # Test that None is returned for a feature that does not exist
        ret0 = secondary.data_quality.data_quality(id=self.EMPTY_PARTICIPANT,
                                           start=self.TEST_END_TIME - 3 * self.MS_IN_DAY,
                                           end=self.TEST_END_TIME,
                                           resolution=self.MS_IN_DAY,
                                           feature="abcdef")
        for x in ret0['data']:
            self.assertEqual(x['value'], None)

    def test_data_quality_gps(self):
        # Test that gps data quality works
        ret0 = secondary.data_quality.data_quality(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_START_TIME_JERK,
                                           end=self.TEST_START_TIME_JERK + 2 * self.MS_IN_DAY + 1,
                                           resolution=self.MS_IN_DAY,
                                           feature="gps")
        self.assertEqual(ret0['data'][0]['value'], 0.9166666666666666)
        self.assertEqual(ret0['data'][1]['value'], 0.7222222222222222)

    def test_data_quality_bin_size(self):
        # Test that bin size works
        ret0 = secondary.data_quality.data_quality(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_START_TIME_JERK,
                                           end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1,
                                           resolution=self.MS_IN_DAY,
                                           feature="gps",
                                           bin_size=10000)
        self.assertEqual(ret0['data'][0]['value'], 0.05775462962962963)

    def test_data_quality_acc(self):
        # test that acc works
        ret0 = secondary.data_quality.data_quality(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_START_TIME_JERK,
                                           end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1,
                                           resolution=self.MS_IN_DAY,
                                           feature="accelerometer")
        self.assertEqual(ret0['data'][0]['value'], 0.001412037037037037)

if __name__ == '__main__':
    unittest.main()
