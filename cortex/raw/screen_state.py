""" Module for raw feature screen state """
from ..feature_types import raw_feature
import LAMP


@raw_feature(
    name="lamp.screen_state",
    dependencies=["lamp.screen_state"]
)
def screen_state(_limit=10000, 
                 cache=False,
                 recursive=False,
                 **kwargs):
    """
    Get all screen state data bounded by time interval and optionally subsample the data.

    :param _limit (int): The maximum number of sensor events to query for in a single request
    :param cache (bool): Indicates whether to save raw data locally in cache dir
    :param recursive (bool): if True, continue requesting data until all data is returned; else just one request
    
    :return timestamp (int): The UTC timestamp for the screen_state event.
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
