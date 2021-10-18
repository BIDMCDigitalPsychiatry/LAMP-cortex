""" Module for raw feature screen state """
from ..feature_types import raw_feature


@raw_feature(
    name="lamp.screen_state",
    dependencies=["lamp.screen_state"]
)
def screen_state(_limit=10000,
                 cache=False,
                 recursive=False,
                 **kwargs):
    """ Get all screen state data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the screen_state event.
        value OR state (int): 0, 1, 2, 3 to denote screen on, off, locked, charging**
        valueString (str): "Screen On", "Screen Off", "Screen Locked"
    Note that based on phone type, value may be returned as "value" or as
            "state". Additionally, not all devices will return a "valueString".
    ** value / state are also phone dependent, so state = 0 on one phone could be the
        same as state = 1 on a different phone.

    Example:
    [{'timestamp': 1618014245255, 'value': 1, 'valueString': 'Screen Off'},
     {'timestamp': 1618014216292, 'value': 0, 'valueString': 'Screen On'},
     {'timestamp': 1618013053261, 'value': 2, 'valueString': 'Screen Locked'},
     {'timestamp': 1618013043261, 'value': 1, 'valueString': 'Screen Off'},
     {'timestamp': 1618012058266, 'value': 0, 'valueString': 'Screen On'},]
    """
    return
