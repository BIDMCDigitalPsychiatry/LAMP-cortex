""" Module for raw feature bluetooth """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.bluetooth",
    dependencies=["lamp.bluetooth"]
)
def bluetooth(_limit=10000,
              cache=False,
              recursive=True,
              **kwargs):
    """ Get all bluetooth data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the Bluetooth event.
        bt_rssi (int): The rssi for the Bluetooth event.
        bt_name (str): The name of the Bluetooth device.
        bt_address (str): Address of Bluetooth event.

    Example:
        [{'timestamp': 1617990580971,
          'bt_rssi': -97,
          'bt_name': '[TV] Samsung 7 Series (65)',
          'bt_address': '873C0B2B-6B43-6DBE-8ECC-369D59767ADF'},
         {'timestamp': 1617990285117,
          'bt_rssi': -100,
          'bt_name': '[TV] Samsung Q900 Series (65)',
          'bt_address': '049AD0D2-9CB1-E132-6347-0BDFCED3E8B8'},]
    """
    return
