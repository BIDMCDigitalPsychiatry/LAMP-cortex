""" Module for raw feature screen state """
import LAMP
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
    """
    data = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                               origin="lamp.screen_state",
                                               _from=kwargs['start'],
                                               to=kwargs['end'],
                                               _limit=_limit)['data']
    while data and recursive:
        to = data[-1]['timestamp']
        data_next = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                                        origin="lamp.screen_state",
                                                        _from=kwargs['start'],
                                                        to=to,
                                                        _limit=_limit)['data']
        if not data_next or data_next[-1]['timestamp'] == to:
            break
        data += data_next

    return [{'timestamp': x['timestamp'], **x['data']} for x in data]
