""" Module for raw feature wifi """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.wifi",
    dependencies=["lamp.wifi"]
)
def wifi(_limit=10000,
         cache=False,
         recursive=False,
         **kwargs):
    """ Get all wifi data bounded by time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the wifi event.
        bssid: MAC address of wireless access point.
        ssid: Network name.

    Example:
        [{'timestamp': 1618015753796, 'bssid': 'a6:68:7e:82:48:72', 'ssid': 'ATTHFtEYgs'},
         {'timestamp': 1618015452266, 'bssid': 'a6:68:7e:82:48:72', 'ssid': 'ATTHFtEYgs'},]
    """
    return
