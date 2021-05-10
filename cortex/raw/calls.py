from ..feature_types import raw_feature
import LAMP


@raw_feature(
    name="lamp.calls",
    dependencies=["lamp.calls"]
)
def calls(resolution=None, limit=2147483647, cache=True, **kwargs):
    """
    Get all cal data bounded by time interval and optionally subsample the data.

    :param resolution (int): The subsampling resolution (TODO).
    :param limit (int): The maximum number of GPS events to query for (defaults to INT_MAX).
    :return timestamp (int): The UTC timestamp for the GPS event.
    :return TODO 
    """

    data = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                               origin="lamp.calls",
                                               _from=kwargs['start'],
                                               to=kwargs['end'],
                                               _limit=limit)['data']

    return [{'timestamp': x['timestamp'], **x['data']} for x in data]
