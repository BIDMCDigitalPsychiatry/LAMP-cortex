""" Module for raw feature steps """
from ..feature_types import raw_feature


@raw_feature(
    name="lamp.steps",
    dependencies=["lamp.steps"]
)
def steps(_limit=10000,
          cache=False,
          recursive=False,
          **kwargs):
    """ Get all step count bounded by time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the steps event.
        value (int): The step count.

    Example:
        [{'timestamp': 1618007651905, 'value': 2406},
         {'timestamp': 1618007649334, 'value': 2402},
         {'timestamp': 1618007646762, 'value': 2395},
         {'timestamp': 1618007644190, 'value': 2390},
         {'timestamp': 1618007641618, 'value': 2384},]
    """
    return
