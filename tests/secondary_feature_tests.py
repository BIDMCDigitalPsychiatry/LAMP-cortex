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
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
            os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))


class TestSecondary(unittest.TestCase):
    # pylint: disable=invalid-sequence-index
    """ Class for testing secondary features """
    MS_IN_DAY = 60 * 60 * 24 * 1000
    TEST_PARTICIPANT = "U26468383"
    TEST_PARTICIPANT_ANDROID = "U1771421483"
    TEST_PARTICIPANT_IOS = "U3826134542"
    EMPTY_PARTICIPANT = "U5704591513"
    TEST_PARTICIPANT_STEPS = "U5946075691"
    TEST_END_TIME = 1583532324130 + 30 * MS_IN_DAY
    TEST_START_TIME_JERK = 1584137124130
    TEST_START_TIME_STEPS = 1651161331270 - 5 * MS_IN_DAY
    TEST_PARTICIPANT_CALLS = "U7955172051"
    TEST_PARTICIPANT_NEARBY_DEVICES = "U1753020007"
    NEARBY_TEST_START = 1646485947205
    NEARBY_TEST_END = 1647003793838
    CALLS_TEST_START = 1654781897000 + 10 * MS_IN_DAY
    CALLS_TEST_END = 1654781897001 + 11 * MS_IN_DAY

    def setUp(self):
        """ Setup the tests """
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)

    # 0. nearby_device_count
    def test_device_count_no_data(self):
        # Test if the participant has no data
        ret0 = secondary.nearby_device_count.nearby_device_count(id=self.EMPTY_PARTICIPANT,
                                           start=self.TEST_END_TIME - 3 * self.MS_IN_DAY,
                                           end=self.TEST_END_TIME,
                                           resolution=self.MS_IN_DAY)
        for x in ret0['data']:
            self.assertEqual(x['value'], None)

    def test_device_count_data(self):
        # Test that nearby device count works
        ret0 = secondary.nearby_device_count.nearby_device_count(id=self.TEST_PARTICIPANT_NEARBY_DEVICES,
                                           start=self.NEARBY_TEST_START,
                                           end=self.NEARBY_TEST_END,
                                           resolution=self.MS_IN_DAY)
        self.assertEqual(ret0['data'][0]['value'], 3)
        self.assertEqual(ret0['data'][1]['value'], None)   
            
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

    # 2. step count
    def test_step_count_no_data(self):
        # Test if the participant has no data
        ret0 = secondary.step_count.step_count(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_END_TIME - 3 * self.MS_IN_DAY,
                                           end=self.TEST_END_TIME,
                                           resolution=self.MS_IN_DAY)
        for x in ret0['data']:
            self.assertEqual(x['value'], None)

    def test_step_count(self):
        # Test that step count works
        ret0 = secondary.step_count.step_count(id=self.TEST_PARTICIPANT_STEPS,
                                           start=self.TEST_START_TIME_STEPS,
                                           end=self.TEST_START_TIME_STEPS + 6 * self.MS_IN_DAY + 1,
                                           resolution=self.MS_IN_DAY)["data"]
        self.assertEqual(ret0[0]['value'], None)
        self.assertEqual(ret0[1]['value'], None)
        self.assertEqual(ret0[2]['value'], None)
        self.assertEqual(ret0[3]['value'], 131120)
        self.assertEqual(ret0[4]['value'], 179956)
        self.assertEqual(ret0[5]['value'], 282319)

    def test_call_duration(self):
        # Test that call duration works
        # Argument 'x' tests whether erroneous argument returns None.
        options = ["incoming", "outgoing", "all", "x"]
        rets=[]
        for option in options:
            local_ret = cortex.secondary.call_duration.call_duration(
                                           call_direction = option,
                                           id=self.TEST_PARTICIPANT_CALLS,
                                           start=self.CALLS_TEST_START,
                                           end=self.CALLS_TEST_END,
                                           resolution=self.MS_IN_DAY,
                                           feature="telephony")['data'][0]['value']
            rets.append(local_ret)

        # Test that None returned when there's no call data.

        ret_none = cortex.secondary.call_duration.call_duration(
                                        call_direction = "all",
                                        id=self.TEST_PARTICIPANT_CALLS,
                                        start=self.CALLS_TEST_START - self.MS_IN_DAY,
                                        end=self.CALLS_TEST_END - self.MS_IN_DAY,
                                        resolution=self.MS_IN_DAY,
                                        feature="telephony")['data'][0]['value']

        # Test that deprecated 'incoming' still functions.

        options_incoming = [True, False]
        rets_incoming=[]
        for option in options_incoming:
            local_ret = cortex.secondary.call_duration.call_duration(
                                        incoming=option,
                                        id=self.TEST_PARTICIPANT_CALLS,
                                        start=self.CALLS_TEST_START,
                                        end=self.CALLS_TEST_END,
                                        resolution=self.MS_IN_DAY,
                                        feature="telephony")['data'][0]['value']
            rets_incoming.append(local_ret)

        self.assertEqual(rets[0], 34)
        self.assertEqual(rets[1], 24)
        self.assertEqual(rets[2], 58)
        self.assertEqual(rets[3], None)
        self.assertEqual(ret_none, None)
        self.assertEqual(rets_incoming[0], 34)
        self.assertEqual(rets_incoming[1], 24)

    def test_call_number(self):
        # Test that call number works
        # Argument 'x' tests whether erroneous argument returns None.
        options = ["incoming", "outgoing", "all", "x"]
        rets=[]
        for option in options:
            local_ret = cortex.secondary.call_number.call_number(
                                           call_direction = option,
                                           id=self.TEST_PARTICIPANT_CALLS,
                                           start=self.CALLS_TEST_START,
                                           end=self.CALLS_TEST_END,
                                           resolution=self.MS_IN_DAY,
                                           feature="telephony")['data'][0]['value']
            rets.append(local_ret)

        # Test that None returned when there's no call data.

        ret_none = cortex.secondary.call_number.call_number(
                                        call_direction = "all",
                                        id=self.TEST_PARTICIPANT_CALLS,
                                        start=self.CALLS_TEST_START - self.MS_IN_DAY,
                                        end=self.CALLS_TEST_END - self.MS_IN_DAY,
                                        resolution=self.MS_IN_DAY,
                                        feature="telephony")['data'][0]['value']

        # Test that deprecated 'incoming' still functions.

        options_incoming = [True, False]
        rets_incoming=[]
        for option in options_incoming:
            local_ret = cortex.secondary.call_number.call_number(
                                        incoming=option,
                                        id=self.TEST_PARTICIPANT_CALLS,
                                        start=self.CALLS_TEST_START,
                                        end=self.CALLS_TEST_END,
                                        resolution=self.MS_IN_DAY,
                                        feature="telephony")['data'][0]['value']
            rets_incoming.append(local_ret)

        self.assertEqual(rets[0], 1)
        self.assertEqual(rets[1], 1)
        self.assertEqual(rets[2], 2)
        self.assertEqual(rets[3], None)
        self.assertEqual(ret_none, None)
        self.assertEqual(rets_incoming[0], 1)
        self.assertEqual(rets_incoming[1], 1)
        
if __name__ == '__main__':
    unittest.main()
