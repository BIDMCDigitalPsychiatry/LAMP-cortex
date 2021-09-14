""" Module for raw feature screen state """
from ..feature_types import raw_feature
import LAMP


@raw_feature(
    name="lamp.screen_state",
    dependencies=["lamp.screen_state"]
)
def screen_state(resolution=None, 
                 _limit=2147483647, 
                 cache=False, 
                 **kwargs):
    """
    Get all screen state data bounded by time interval and optionally subsample the data.

    :param resolution (int): The subsampling resolution (TODO).
    :param limit (int): The maximum number of events to query for (defaults to INT_MAX).
    :return timestamp (int): The UTC timestamp for the screen_state event.
    :return TODO
    """
    data = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                               origin="lamp.screen_state",
                                               _from=kwargs['start'],
                                               to=kwargs['end'],
                                               _limit=limit)['data']
    return [{'timestamp': x['timestamp'], **x['data']} for x in data]
