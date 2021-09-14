""" Module for raw feature calls """
import LAMP
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.calls",
    dependencies=["lamp.calls"]
)
def calls(resolution=None, 
          _limit=2147483647, 
          cache=False, 
          **kwargs):
    """
    Get all call data bounded by time interval and optionally subsample the data.

    :param resolution (int): The subsampling resolution (TODO).
    :param limit (int): The maximum number of GPS events to query for (defaults to INT_MAX).
    :return timestamp (int): The UTC timestamp for the GPS event.
    :return TODO
    """

    data = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                               origin="lamp.calls",
                                               _from=kwargs['start'],
                                               to=kwargs['end'],
                                               _limit=_limit)['data']

    return [{'timestamp': x['timestamp'], **x['data']} for x in data]
