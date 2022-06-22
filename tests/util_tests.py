""" Module for unittesting primary features """
import unittest
import sys
import os
import logging
import cortex.utils as utils
import LAMP
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
            os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))


class TestUtils(unittest.TestCase):
    # pylint: disable=invalid-sequence-index
    """ Class for testing util functions """
    MS_IN_DAY = 60 * 60 * 24 * 1000
    TEST_PARTICIPANT_OLD = "U26468383"
    TEST_PARTICIPANT_IOS = "U1753020007"
    TEST_PARTICIPANT_ANDROID = "U2898028549"

    def setUp(self):
        """ Setup the tests """
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)

    # 0. useful functions misc - os version
    def test_get_device_info_old_data(self):
        # Should return None for all fields for older users
        # as the user_agent string has changed lately
        ret0 = utils.misc_functions.get_os_version(self.TEST_PARTICIPANT_OLD)
        for x in ret0:
            self.assertEqual(ret0[x], None)

    def test_get_device_info_old_ios_android(self):
        # Test if the participant has no data
        ret0 = utils.misc_functions.get_os_version(self.TEST_PARTICIPANT_IOS)
        self.assertEqual(ret0['device_type'], 'iOS')
        self.assertEqual(ret0['os_version'], 'iOS 15.3.1')
        self.assertEqual(ret0['phone_type'], 'iPhone iPhone10,4')

        ret1 = utils.misc_functions.get_os_version(self.TEST_PARTICIPANT_ANDROID)
        self.assertEqual(ret1['device_type'], 'Android')
        self.assertEqual(ret1['os_version'], 'Android 10')
        self.assertEqual(ret1['phone_type'], 'OnePlus')

if __name__ == '__main__':
    unittest.main()
