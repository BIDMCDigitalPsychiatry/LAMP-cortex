""" Module for unittesting primary features """
import unittest
import sys
import os
import logging
import pandas as pd
import cortex.primary as primary
import cortex.raw as raw
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class TestPrimary(unittest.TestCase):
    # pylint: disable=invalid-sequence-index
    """ Class for testing primary features """
    TEST_PARTICIPANT = "U26468383"
    EMPTY_PARTICIPANT = "U5704591513"
    TEST_END_TIME = 1585363115912

    def setUp(self):
        """ Setup the tests """
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)


    # 0. Trips
    def test_primary_id_none(self):
        """ Test id is none """
        param = "id"
        with self.assertRaisesRegex(Exception, f"parameter `{param}` is required but missing"):
            primary.trips.trips(id=None,  start=0, end=1617818393000)

    def test_primary_id_not_exist(self):
        """ Test invalid id """
        trips = primary.trips.trips(id='BADID', start=0, end=1617818393000)
        self.assertEqual(trips['data'], [])

    def test_primary_id_no_data(self):
        """ Test if there is no data """
        trips = primary.trips.trips(id=self.EMPTY_PARTICIPANT, start=0, end=1617818393000)
        self.assertEqual(trips['data'], [])

    def test_primary_start_none(self):
        """ Test if start is none """
        with self.assertRaises(Exception):
            primary.trips.trips(id=self.TEST_PARTICIPANT, start=None, end=1617818393000)

    def test_primary_end_none(self):
        """ Test if end is none """
        with self.assertRaises(Exception):
            primary.trips.trips(id=self.TEST_PARTICIPANT, start=0, end=None)

    def test_primary_start_end_same(self):
        """ Test if the start and end are the same """
        same_start, same_end = 1585363137479, 1585363137479
        res = primary.trips.trips(id=self.TEST_PARTICIPANT, start=same_start, end=same_end)
        self.assertEqual(res['data'], [])

    def test_primary_start_end_inverted(self):
        """ Test if start > end """
        inverted_start, inverted_end = 1585363137479, 1583532324130
        with self.assertRaisesRegex(Exception, "'start' argument must occur before 'end'."):
            primary.trips.trips(id=self.TEST_PARTICIPANT,
                                       start=inverted_start,
                                       end=inverted_end)

    # 1. Significant locations
    def test_siglocs_no_data(self):
        """ Test if the participant has no data """
        ret0 = primary.significant_locations.significant_locations(id=self.EMPTY_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode')
        self.assertEqual(ret0['data'], [])
        ret1 = primary.significant_locations.significant_locations(id=self.EMPTY_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='k_means')
        self.assertEqual(ret1['data'], [])

    def test_siglocs_max_clusters(self):
        """ Test if max_clusters is set """
        # try for 1 cluster
        ret1 = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  max_clusters=1)
        num_clusters1 = len(ret1['data'])
        self.assertEqual(num_clusters1, 1)
        # try for 5 clusters
        ret5 = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  max_clusters=5)
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
                                                                  max_clusters=100000)
        num_clusters100 = len(ret100['data'])
        self.assertEqual(num_clusters100, len(top_counts))

    def test_siglocs_min_cluster_size(self):
        """ Test min cluster size """
        ret0 = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  min_cluster_size=0.5)
        num_clusters0 = len(ret0['data'])
        self.assertEqual(num_clusters0, 1)

        ret1 = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  min_cluster_size=0.1)
        num_clusters1 = len(ret1['data'])
        self.assertEqual(num_clusters1, 2)

        ret2 = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  min_cluster_size=0.01)
        num_clusters2 = len(ret2['data'])
        self.assertEqual(num_clusters2, 4)

    def test_siglocs_min_cluster_and_max_clusters(self):
        """ Test when both min cluster size and max clusters is set
            Max clusters should override min cluster size
        """
        ret = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  max_clusters=1,
                                                                  min_cluster_size=0.001)
        num_clusters = len(ret['data'])
        self.assertEqual(num_clusters, 1)

    def test_siglocs_top_clusters(self):
        """ Make sure the top clusters are the expected ones """
        ret = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='mode',
                                                                  min_cluster_size=0.01)
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
        """ Test that siglocs is calling the correct method """
        ret = primary.significant_locations.significant_locations(id=self.TEST_PARTICIPANT,
                                                                  start=0,
                                                                  end=self.TEST_END_TIME,
                                                                  method='k_means',
                                                                  min_cluster_size=0.01)
        ret = ret['data']
        num_clusters = len(ret)
        self.assertEqual(num_clusters, 6)


if __name__ == '__main__':
    unittest.main()
