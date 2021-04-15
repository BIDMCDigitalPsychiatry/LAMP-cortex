import unittest
import LAMP
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import cortex


class TestPrimary(unittest.TestCase):

    # ID #
    def test_primary_id_none(self):
        TEST_PARTICIPANT = "U26468383"
        cortex.trips(id=None,  start=0, end=1617818393000)
        self.assertRaises(Exception)
            

    def test_primary_id_not_exist(self):
        TEST_PARTICIPANT = "U26468383"
        with self.assertRaise(LAMP.exceptions.ApiException):
            cortex.trips(id='BADID', start=0, end=1617818393000)

    def test_primary_id_no_data(self):
        EMPTY_PARTICIPANT = "U5704591513"
        trips = cortex.trips(id=EMPTY_PARTICIPANT, start=0, end=1617818393000)
        self.assertEquals(trips, {})

    #def test_primary_id_1(self):

    # Start #
    def test_primary_start_none(self):
        TEST_PARTICIPANT = "U26468383"
        with self.assertRaises(Exception):
            cortex.trips(id=TEST_PARTICIPANT, start=None, end=1617818393000)

    # End #
    def test_primary_end_none(self):
        TEST_PARTICIPANT = "U26468383"
        with self.assertRaises(Exception):
             cortex.trips(id=TEST_PARTICIPANT, start=0, end=None)

    # #
    def test_primary_start_end_same(self):
        TEST_PARTICIPANT = "U26468383"
        same_start, same_end = 1585363137479, 1585363137479
        tes = cortex.trips(id=TEST_PARTICIPANT, start=same_start, end=same_end)
        self.assertEquals(res, [])
        
    def test_primary_start_end_inverted(self):
        ## if start > end #
        TEST_PARTICIPANT = "U26468383"
        inverted_start, inverted_end = 1585363137479, 1583532324130
        with self.assertRaises(Exception("'start' argument must occur before 'end'.")):
            res = cortex.trips(id=TEST_PARTICIPANT, start=inverted_start, end=inverted_end)

    

if __name__ == '__main__':
    unittest.main()