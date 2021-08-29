""" Module for unittesting primary features """
import unittest
import sys
import os
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

    # 1. Acc_jerk
    def test_acc_jerk_no_data(self):
        # Test if the participant has no data
        ret0 = secondary.acc_jerk.acc_jerk(id=self.EMPTY_PARTICIPANT,
                                           start=self.TEST_END_TIME - 3 * self.MS_IN_DAY,
                                           end=self.TEST_END_TIME,
                                           resolution=self.MS_IN_DAY)
        for x in ret0['data']:
            self.assertEqual(x['acc_jerk'], None)

    def test_acc_jerk_default_threshold(self):
        # Test to make sure jerk is correct
        ret1 = secondary.acc_jerk.acc_jerk(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_START_TIME_JERK,
                                           end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1,
                                           resolution=self.MS_IN_DAY)
        ACC_JERK_DEFAULT = 0.04132388383691913
        self.assertEqual(ret1['data'][0]['acc_jerk'], ACC_JERK_DEFAULT)


    def test_acc_jerk_differnt_thresholds(self):
        # Test to make sure the threshold parameter works for jerk
        #
        # Note that threshold should not be set this high, this
        # is done for testing purposes only
        ACC_JERK_5S = 0.020665072792929968
        ACC_JERK_70S = 0.018483403010722384
        ret1 = secondary.acc_jerk.acc_jerk(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_START_TIME_JERK,
                                           end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1,
                                           resolution=self.MS_IN_DAY,
                                           threshold=5000)
        self.assertEqual(ret1['data'][0]['acc_jerk'], ACC_JERK_5S)

        ret2 = secondary.acc_jerk.acc_jerk(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_START_TIME_JERK,
                                           end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1,
                                           resolution=self.MS_IN_DAY,
                                           threshold=70000)
        self.assertEqual(ret2['data'][0]['acc_jerk'], ACC_JERK_70S)

if __name__ == '__main__':
    unittest.main()
