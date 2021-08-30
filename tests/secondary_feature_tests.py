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
LAMP.connect('admin', 'LAMPLAMP')
sys.path.insert(1,'/home/danielle/LAMP-cortex')


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

    # 1. mean_acc_jerk
    def test_acc_jerk_no_data(self):
        # Test if the participant has no data
        ret0 = secondary.mean_acc_jerk.mean_acc_jerk(id=self.EMPTY_PARTICIPANT,
                                           start=self.TEST_END_TIME - 3 * self.MS_IN_DAY,
                                           end=self.TEST_END_TIME,
                                           resolution=self.MS_IN_DAY)
        for x in ret0['data']:
            self.assertEqual(x['mean_acc_jerk'], None)

    def test_mean_acc_jerk_default_threshold(self):
        # Test to make sure jerk is correct
        ret1 = secondary.mean_acc_jerk.mean_acc_jerk(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_START_TIME_JERK,
                                           end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1,
                                           resolution=self.MS_IN_DAY)
        ACC_DEFAULT = 4.132388383691913e-05
        self.assertEqual(ret1['data'][0]['mean_acc_jerk'], ACC_DEFAULT)


    def test_mean_acc_jerk_differnt_thresholds(self):
        # Test to make sure the threshold parameter works for jerk
        #
        # Note that threshold should not be set this high, this
        # is done for testing purposes only
        ACC_JERK_5S = 1.05517280095106e-05
        ACC_JERK_70S = 8.441456035918827e-06
        ret1 = secondary.mean_acc_jerk.mean_acc_jerk(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_START_TIME_JERK,
                                           end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1,
                                           resolution=self.MS_IN_DAY,
                                           threshold=5000)
        self.assertEqual(ret1['data'][0]['mean_acc_jerk'], ACC_JERK_5S)

        ret2 = secondary.mean_acc_jerk.mean_acc_jerk(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_START_TIME_JERK,
                                           end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1,
                                           resolution=self.MS_IN_DAY,
                                           threshold=70000)
        self.assertEqual(ret2['data'][0]['mean_acc_jerk'], ACC_JERK_70S)

if __name__ == '__main__':
    unittest.main()
