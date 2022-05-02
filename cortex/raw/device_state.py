""" Module for raw feature device state """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.device_state",
    dependencies=["lamp.device_state"]
)
def device_state(_limit=10000,
                 cache=False,
                 recursive=True,
                 **kwargs):
    """ Get all screen state data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the screen_state event.
        value (int): 0, 1, 2, 3 to denote screen on, off, locked, charging**
        representation (str): "screen_off", "screen_on", "locked", "unlocked"
    Note that based on phone type, value may be returned as "value" or as
            "state". Additionally, not all devices will return a "valueString".
    ** value / state are also phone dependent, so state = 0 on one phone could be the
        same as state = 1 on a different phone.

    Example:
    [{'sensor': 'lamp.device_state',
      'data': {
          'value': 1,
          'representation': 'screen_off',
          'battery_level': 0.8999999761581421
      },
      'timestamp': 1650897192888},
    {'sensor': 'lamp.device_state',
     'data': {
         'value': 0,
         'representation': 'screen_on',
         'battery_level': 0.9100000262260437
      },
      'timestamp': 1650896876889},]
    """
    return
