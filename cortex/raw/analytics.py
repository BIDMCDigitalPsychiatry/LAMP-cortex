""" Module for raw feature analytics """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.analytics",
    dependencies=["lamp.analytics"]
)
def analytics(_limit=10000,
              cache=False,
              recursive=True,
              **kwargs):
    """Get all analytics data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the accelerometer event.
        user_agent (string): the user agent string.
        device_type (string): The OS of the device.
        device_token (string): The unique hashed device identifier.

    Example:
        [{'timestamp': 1618016071621,
         'device_token': 'dI_LZLy_Tjq7ppO2O4Pt:APA91bGfUdnsXa-oGW4SOnlqp85U5OjO2sa',
         # Noe: ^device token has been edited
         'device_type': 'Android',
         'user_agent': '1.1,6869500,Google,Pixel 3a'}}]
    """
    return
