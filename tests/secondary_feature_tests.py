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
    TEST_END_TIME = 1583532324130 + MS_IN_DAY + 1
    #1583532324130
    #1585358317568

    def setUp(self):
        """ Setup the tests """
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)

    # 1. Acc_jerk
    def test_acc_jerk_no_data(self):
        # Test if the participant has no data
        ret0 = secondary.acc_jerk.acc_jerk(id=self.EMPTY_PARTICIPANT, start=0, end=self.TEST_END_TIME,
                            resolution=self.MS_IN_DAY)
        print(ret0)
        for x in ret0['data']:
            self.assertEqual(x['acc_jerk'], None)

    def test_acc_jerk_default_threshold(self):
        # Test to make sure jerk is correct
        earliest_time = LAMP.SensorEvent.all_by_participant(participant_id=self.TEST_PARTICIPANT,
                                       origin="lamp.accelerometer",
                                       _from=0,
                                       to=self.TEST_END_TIME,
                                       _limit=-1)['data']
        latest_time = LAMP.SensorEvent.all_by_participant(participant_id=self.TEST_PARTICIPANT,
                                       origin="lamp.accelerometer",
                                       _from=0,
                                       to=self.TEST_END_TIME,
                                       _limit=1)['data']
        print(earliest_time)
        print(latest_time)
                                                
        ret1 = secondary.acc_jerk.acc_jerk(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  resolution=self.MS_IN_DAY)
        print(ret1['data'])
        
    """
    def test_siglocs_min_cluster_size(self):
        # Test min cluster size
        ret0 = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  min_cluster_size=0.5,
                                                                  max_dist=0)
        num_clusters0 = len(ret0['data'])
        self.assertEqual(num_clusters0, 1)

        ret1 = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  min_cluster_size=0.1,
                                                                  max_dist=0)
        num_clusters1 = len(ret1['data'])
        self.assertEqual(num_clusters1, 2)

        ret2 = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  min_cluster_size=0.01,
                                                                  max_dist=0)
        num_clusters2 = len(ret2['data'])
        self.assertEqual(num_clusters2, 4)
    """

if __name__ == '__main__':
    unittest.main()
