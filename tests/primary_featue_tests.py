import unittest
import LAMP
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import cortex


class TestPrimary(unittest.TestCase):
    TEST_PARTICIPANT = "U26468383"
    
    # ID #
    def test_primary_id_none(self):        
        with self.assertRaisesRegex(Exception, f"Processing secondary feature \"{name}\"..."):
            cortex.trips(id=None,  start=0, end=1617818393000)

    def test_primary_id_not_exist(self):
        with self.assertRaise(LAMP.exceptions.ApiException):
            cortex.trips(id='BADID', start=0, end=1617818393000)

    def test_primary_id_no_data(self):
        EMPTY_PARTICIPANT = "U5704591513"
        trips = cortex.trips(id=EMPTY_PARTICIPANT, start=0, end=1617818393000)
        self.assertEquals(trips, {})

    #def test_primary_id_1(self):

    # Start #
    def test_primary_start_none(self):
        with self.assertRaises(Exception):
            cortex.trips(id=self.TEST_PARTICIPANT, start=None, end=1617818393000)

    # End #
    def test_primary_end_none(self):
        with self.assertRaises(Exception):
             cortex.trips(id=self.TEST_PARTICIPANT, start=0, end=None)

    # #
    def test_primary_start_end_same(self):
        same_start, same_end = 1585363137479, 1585363137479
        tes = cortex.trips(id=self.TEST_PARTICIPANT, start=same_start, end=same_end)
        self.assertEquals(res, [])
        
    def test_primary_start_end_inverted(self):
        ## if start > end #
        inverted_start, inverted_end = 1585363137479, 1583532324130
        with self.assertRaisesRegex(Exception, "'start' argument must occur before 'end'."):
            res = cortex.trips(id=self.TEST_PARTICIPANT, start=inverted_start, end=inverted_end)

    

if __name__ == '__main__':
    unittest.main()