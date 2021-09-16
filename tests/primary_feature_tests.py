""" Module for unittesting primary features """
import unittest
import sys
import os
import math
import logging
import pandas as pd
import cortex
import cortex.primary as primary
import cortex.raw as raw
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class TestPrimary(unittest.TestCase):
    # pylint: disable=invalid-sequence-index
    """ Class for testing primary features """
    MS_IN_DAY = 60 * 60 * 24 * 1000
    TEST_PARTICIPANT = "U26468383"
    EMPTY_PARTICIPANT = "U5704591513"
    TEST_END_TIME = 1585363115912
    TEST_SCREEN_ACTIVE_START_0 = 1585355933805
    TEST_SCREEN_ACTIVE_END_0 = 1585356533814
    TEST_SCREEN_ACTIVE_START_1 = 1585346933781
    TEST_SCREEN_ACTIVE_END_1 = 1585358335411
    TEST_SCREEN_ACTIVE_START_2 = 1585346933781
    TEST_SCREEN_ACTIVE_END_2 = TEST_SCREEN_ACTIVE_START_2 + 3 * MS_IN_DAY
    TEST_START_TIME_JERK = 1584137124130

    def setUp(self):
        """ Setup the tests """
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)

    # 0. Trips
    def test_primary_id_none(self):
        # Test id is none
        param = "id"
        with self.assertRaisesRegex(Exception, f"parameter `{param}` is required but missing"):
            primary.trips.trips(id=None,  start=0, end=1617818393000)

    def test_primary_id_not_exist(self):
        # Test invalid id
        trips = primary.trips.trips(id='BADID', start=0, end=1617818393000)
        self.assertEqual(trips['data'], [])

    def test_primary_id_no_data(self):
        # Test if there is no data
        trips = primary.trips.trips(id=self.EMPTY_PARTICIPANT, start=0, end=1617818393000)
        self.assertEqual(trips['data'], [])

    def test_primary_start_none(self):
        # Test if start is none
        with self.assertRaises(Exception):
            primary.trips.trips(id=self.TEST_PARTICIPANT, start=None, end=1617818393000)

    def test_primary_end_none(self):
        # Test if end is none
        with self.assertRaises(Exception):
            primary.trips.trips(id=self.TEST_PARTICIPANT, start=0, end=None)

    def test_primary_start_end_same(self):
        # Test if the start and end are the same
        same_start, same_end = 1585363137479, 1585363137479
        res = primary.trips.trips(id=self.TEST_PARTICIPANT, start=same_start, end=same_end)
        self.assertEqual(res['data'], [])

    def test_primary_start_end_inverted(self):
        # Test if start > end
        inverted_start, inverted_end = 1585363137479, 1583532324130
        with self.assertRaisesRegex(Exception, "'start' argument must occur before 'end'."):
            primary.trips.trips(id=self.TEST_PARTICIPANT,
                                       start=inverted_start,
                                       end=inverted_end)

    # 1. Significant locations
    def test_siglocs_no_data(self):
        # Test if the participant has no data
        ret0 = primary.significant_locations.significant_locations(id=self.EMPTY_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode')
        self.assertEqual(ret0['data'], [])
        self.assertEqual(ret0['has_raw_data'], 0)
        ret1 = primary.significant_locations.significant_locations(id=self.EMPTY_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='k_means')
        self.assertEqual(ret1['data'], [])
        self.assertEqual(ret1['has_raw_data'], 0)

    def test_siglocs_max_clusters(self):
        # Test if max_clusters is set
        # try for 1 cluster
        ret1 = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  max_clusters=1,
                                                                  max_dist=0)
        num_clusters1 = len(ret1['data'])
        self.assertEqual(num_clusters1, 1)
        # try for 5 clusters
        ret5 = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  max_clusters=5,
                                                                  max_dist=0)
        num_clusters5 = len(ret5['data'])
        self.assertEqual(num_clusters5, 5)
        # try for more clusters than possible
        gps_data = pd.DataFrame.from_dict(raw.gps.gps(id=self.TEST_PARTICIPANT,
                                                      start=0,
                                                      end=self.TEST_END_TIME)['data'])
        gps_data = gps_data[gps_data['timestamp'] != gps_data['timestamp'].shift()]
        gps_data['latitude'] = gps_data['latitude'].apply(lambda x: round(x, 3))
        gps_data['longitude'] = gps_data['longitude'].apply(lambda x: round(x, 3))
        top_counts = gps_data[['latitude', 'longitude']].value_counts()
        # Test for some number of clusters larger than the max possible number
        ret100 = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                     start=0,
                                                                     end=self.TEST_END_TIME,
                                                                     method='mode',
                                                                     max_clusters=100000,
                                                                     max_dist=0)
        num_clusters100 = len(ret100['data'])
        self.assertEqual(num_clusters100, len(top_counts))

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

    def test_siglocs_min_cluster_and_max_clusters(self):
        # Test when both min cluster size and max clusters is set
        #    Max clusters should override min cluster size
        ret = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  max_clusters=1,
                                                                  min_cluster_size=0.001,
                                                                  max_dist=0)
        num_clusters = len(ret['data'])
        self.assertEqual(num_clusters, 1)

    def test_siglocs_top_clusters(self):
        # Make sure the top clusters are the expected ones
        ret = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  min_cluster_size=0.01,
                                                                  max_dist=0)
        ret = ret['data']
        self.assertEqual(ret[0]['latitude'], 42.320)
        self.assertEqual(ret[0]['longitude'], -71.051)
        self.assertEqual(ret[1]['latitude'], 42.340)
        self.assertEqual(ret[1]['longitude'], -71.105)
        self.assertEqual(ret[2]['latitude'], 42.340)
        self.assertEqual(ret[2]['longitude'], -71.104)
        self.assertEqual(ret[3]['latitude'], 42.319)
        self.assertEqual(ret[3]['longitude'], -71.051)

    def test_siglocs_kmeans(self):
        # Test that siglocs is calling the correct method
        ret = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='k_means',
                                                                  min_cluster_size=0.01)
        ret = ret['data']
        num_clusters = len(ret)
        self.assertEqual(num_clusters, 6)

    def test_siglocs_top_clusters_remove_clusters(self):
        # Make sure the top clusters are the expected ones
        #    if max dist is set
        ret = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  min_cluster_size=0.01,
                                                                  max_dist=200)
        ret = ret['data']
        self.assertEqual(ret[0]['latitude'], 42.320)
        self.assertEqual(ret[0]['longitude'], -71.051)
        self.assertEqual(ret[1]['latitude'], 42.340)
        self.assertEqual(ret[1]['longitude'], -71.105)
        self.assertEqual(len(ret), 2)

    # 2. Screen active
    def test_screenactive_no_data(self):
        # Test if the participant has no data
        ret0 = primary.screen_active.screen_active(id=self.EMPTY_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME)
        self.assertEqual(ret0['data'], [])
        self.assertEqual(ret0['has_raw_data'], 0)
        ret1 = primary.screen_active.screen_active(id=self.EMPTY_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME)
        self.assertEqual(ret1['data'], [])
        self.assertEqual(ret1['has_raw_data'], 0)

    def test_screenactive_correct_duration(self):
        # Test if the correct active duration is returned
        cortex.feature_types.delete_attach(self.TEST_PARTICIPANT, features=["cortex.screen_active"])
        ret0 = primary.screen_active.screen_active(id=self.TEST_PARTICIPANT,
                                                   start=self.TEST_SCREEN_ACTIVE_START_0,
                                                   end=self.TEST_SCREEN_ACTIVE_END_0)
        correct_dur = 600000
        self.assertEqual(ret0['data'][0]['duration'], correct_dur)

    def test_screenactive_correct_number(self):
        # Test if the number of bouts is correct
        ret0 = primary.screen_active.screen_active(id=self.TEST_PARTICIPANT,
                                                   start=self.TEST_SCREEN_ACTIVE_START_1,
                                                   end=self.TEST_SCREEN_ACTIVE_END_1)
        num_bouts = len(ret0['data'])
        self.assertEqual(num_bouts, 2)

    # 3. Acc_jerk
    def test_acc_jerk_no_data(self):
        # Test if the participant has no data
        ret0 = primary.acc_jerk.acc_jerk(id=self.EMPTY_PARTICIPANT,
                                           start=self.TEST_END_TIME - 3 * self.MS_IN_DAY,
                                           end=self.TEST_END_TIME,
                                           resolution=self.MS_IN_DAY)

        self.assertEqual(ret0['data'], [])
        self.assertEqual(ret0['has_raw_data'], 0)

    def test_acc_jerk_default_threshold(self):
        # Test to make sure jerk is correct
        ret1 = primary.acc_jerk.acc_jerk(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_START_TIME_JERK,
                                           end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1)
        ACC_DEFAULT = 4.132388383691913e-05
        self.assertEqual(ret1['data'][0]["acc_jerk"], ACC_DEFAULT)
        self.assertEqual(len(ret1['data']), 1)


    def test_mean_acc_jerk_differnt_thresholds(self):
        # Test to make sure the threshold parameter works for jerk
        #
        # Note that threshold should not be set this high, this
        # is done for testing purposes only
        ret1 = primary.acc_jerk.acc_jerk(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_START_TIME_JERK,
                                           end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1,
                                           threshold=5000)
        ACC_JERK1_0 = 3.4714133045562506e-08
        ACC_JERK1_1 = 1.4439344535270027e-07
        self.assertEqual(ret1["data"][0]['acc_jerk'], ACC_JERK1_0)
        self.assertEqual(ret1["data"][1]['acc_jerk'], ACC_JERK1_1)
        self.assertEqual(len(ret1["data"]), 4)

        ret2 = primary.acc_jerk.acc_jerk(id=self.TEST_PARTICIPANT,
                                           start=self.TEST_START_TIME_JERK,
                                           end=self.TEST_START_TIME_JERK + self.MS_IN_DAY + 1,
                                           threshold=550000)
        ACC_JERK2_0 = 3.4714133045562506e-08
        ACC_JERK2_1 = 1.4439344535270027e-07
        ACC_JERK2_2 = 2.673282483361155e-08
        ACC_JERK2_3 = 2.8462423632716186e-10
        self.assertEqual(ret2["data"][0]['acc_jerk'], ACC_JERK2_0)
        self.assertEqual(ret2["data"][1]['acc_jerk'], ACC_JERK2_1)
        self.assertEqual(ret2["data"][2]['acc_jerk'], ACC_JERK2_2)
        self.assertEqual(ret2["data"][3]['acc_jerk'], ACC_JERK2_3)
        self.assertEqual(len(ret2["data"]), 14)

if __name__ == '__main__':
    unittest.main()
