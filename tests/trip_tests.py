import unittest
import cortex
import LAMP

class TestTrips(unittest.TestCase):
    TEST_PARTICIPANT = "U26468383"


    # ID #
    def test_trips_id_none(self):
        cortex.trips(None,  0, 1617818393000)
        self.assertRaises(Exception)
            

    def test_trips_id_not_exist(self):
        cortex.trips('BADID', 0, 1617818393000)
        self.assertRaise(LAMP.exceptions.ApiException)

    def test_trips_id_no_data(self):
        EMPTY_PARTICIPANT = "U5704591513"
        trips = cortex.trips(EMPTY_PARTICIPANT, 0, 1617818393000)
        self.assertEquals(trips, {})

    def test_trips_id_1(self):

    # Start #
    def test_trips_start_none(self):
        cortex.trips(TEST_PARTICIPANT, None, 1617818393000)
        self.assertRaises(Exception)

    # End #
    def test_trips_end_none(self):
        cortex.trips(TEST_PARTICIPANT, 0, None)
        self.assertRaises(Exception)

    # #
    def test_trips_start_end_same(self):
        same_start, same_end = 1585363137479, 1585363137479
        cortex.trips(TEST_PARTICIPANT, start=same_start, end=same_end)
        
    def test_trips_start_end_inverted(self):
        ## if start > end #
        inverted_start, inverted_end = 1585363137479, 1583532324130
        cortex.trips(TEST_PARTICIPANT, start=inverted_start, end=same_end)
        if 

    

if __name__ == '__main__':
    unittest.main()