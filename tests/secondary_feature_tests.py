""" Module for unittesting primary features """
import unittest
import sys
import os
import math
import pandas as pd
import logging
sys.path.insert(1, 'home/andrew/LAMP-cortex')
import cortex
import cortex.secondary as secondary

import LAMP
import pdb
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
            os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))


class TestSecondary(unittest.TestCase):
    # pylint: disable=invalid-sequence-index
    """ Class for testing secondary features """
    MS_IN_DAY = 60 * 60 * 24 * 1000
    TEST_DAN = "U1753020007"
    TEST_PARTICIPANT = "U26468383"
    TEST_PARTICIPANT_ANDROID = "U1771421483"
    TEST_PARTICIPANT_IOS = "U3826134542"
    EMPTY_PARTICIPANT = "U5704591513"
    TEST_PARTICIPANT_STEPS = "U5946075691"
    TEST_END_TIME = 1583532324130 + 30 * MS_IN_DAY
    TEST_START_TIME_JERK = 1584137124130
    TEST_START_TIME_STEPS = 1651161331270 - 5 * MS_IN_DAY

    def setUp(self):
        """ Setup the tests """
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)

#     # 0. bluetooth_device_count
#     def test_device_count_no_data(self):
#         # Test if the participant has no data
#         ret0 = secondary.bluetooth_device_count.bluetooth_device_count(id=self.EMPTY_PARTICIPANT,
#                                            start=self.TEST_END_TIME - 3 * self.MS_IN_DAY,
#                                            end=self.TEST_END_TIME,
#                                            resolution=self.MS_IN_DAY)
#         for x in ret0['data']:
#             self.assertEqual(x['value'], None)

#     # 1. data_quality
#     def test_data_quality_no_data(self):
#         # Test if the participant has no data
#         ret0 = secondary.data_quality.data_quality(id=self.EMPTY_PARTICIPANT,
#                                            start=self.TEST_END_TIME - 3 * self.MS_IN_DAY,
#                                            end=self.TEST_END_TIME,
#                                            resolution=self.MS_IN_DAY,
#                                            feature="gps")
#         for x in ret0['data']:
#             self.assertEqual(x['value'], 0)

#     def test_data_quality_undefined_feature(self):
#         # Test that None is returned for a feature that does not exist
#         ret0 = secondary.data_quality.data_quality(id=self.EMPTY_PARTICIPANT,
#                                            start=self.TEST_END_TIME - 3 * self.MS_IN_DAY,
#                                            end=self.TEST_END_TIME,
#                                            resolution=self.MS_IN_DAY,
#                                            feature="abcdef")
#         for x in ret0['data']:
#             self.assertEqual(x['value'], None)

#     def test_data_quality_gps(self):
#         # Test that gps data quality works
#         ret0 = secondary.data_quality.data_quality(id=self.TEST_PARTICIPANT,
#                                            start=self.TEST_START_TIME_JERK,
#                                            end=self.TEST_START_TIME_JERK + 2 * self.MS_IN_DAY + 1,
#                                            resolution=self.MS_IN_DAY,
#                                            feature="gps")
#         self.assertEqual(ret0['data'][0]['value'], 0.9166666666666666)
#         self.assertEqual(ret0['data'][1]['value'], 0.7222222222222222)

#     def test_data_quality_bin_size(self):
#         # Test that bin size works
#         ret0 = secondary.data_quality.data_quality(id=self.TEST_PARTICIPANT,
#                                            start=self.TEST_START_TIME_JERK,
#                                            end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1,
#                                            resolution=self.MS_IN_DAY,
#                                            feature="gps",
#                                            bin_size=10000)
#         self.assertEqual(ret0['data'][0]['value'], 0.05775462962962963)

#     def test_data_quality_acc(self):
#         # test that acc works
#         ret0 = secondary.data_quality.data_quality(id=self.TEST_PARTICIPANT,
#                                            start=self.TEST_START_TIME_JERK,
#                                            end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1,
#                                            resolution=self.MS_IN_DAY,
#                                            feature="accelerometer")
#         self.assertEqual(ret0['data'][0]['value'], 0.001412037037037037)

#     # 2. step count
#     def test_step_count_no_data(self):
#         # Test if the participant has no data
#         ret0 = secondary.step_count.step_count(id=self.TEST_PARTICIPANT,
#                                            start=self.TEST_END_TIME - 3 * self.MS_IN_DAY,
#                                            end=self.TEST_END_TIME,
#                                            resolution=self.MS_IN_DAY)
#         for x in ret0['data']:
#             self.assertEqual(x['value'], None)

#     def test_step_count(self):
#         # Test that step count works
#         ret0 = secondary.step_count.step_count(id=self.TEST_PARTICIPANT_STEPS,
#                                            start=self.TEST_START_TIME_STEPS,
#                                            end=self.TEST_START_TIME_STEPS + 6 * self.MS_IN_DAY + 1,
#                                            resolution=self.MS_IN_DAY)["data"]
#         self.assertEqual(ret0[0]['value'], None)
#         self.assertEqual(ret0[1]['value'], None)
#         self.assertEqual(ret0[2]['value'], None)
#         self.assertEqual(ret0[3]['value'], 131120)
#         self.assertEqual(ret0[4]['value'], 179017)
#         self.assertEqual(ret0[5]['value'], 3598)
        
    def test_final_andrew(self):
        # Test that call degree works
        ret0 = secondary.call_degree.call_degree(call_type = 'incoming',id=self.TEST_DAN,
                                           start=self.TEST_START_TIME_STEPS,
                                           end=self.TEST_START_TIME_STEPS + 6 * self.MS_IN_DAY + 1,
                                           resolution=self.MS_IN_DAY)["data"]
#         breakpoint()
        self.assertEqual(ret0[0]['value'],0)
#         self.assertEqual(ret0[5]['value'], 3598)

if __name__ == '__main__':
    unittest.main()
