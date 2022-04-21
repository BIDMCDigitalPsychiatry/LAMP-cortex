""" Module for raw feature jewels_a """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.jewels_a",
    dependencies=["lamp.jewels_a"]
)
def jewels_a(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    """ Get jewels_a data bounded by time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the jewels_a event.
        duration (int): the duration in ms
        activity (str): the activity id
        static_data (dict): a dict which includes 'point', 'score', 'total_attempts',
                'total_bonus_collected', 'total_jewels_collected'
        temporal_slices (list): list of dicts which include the 'duration',
                'item', 'level', 'status', and 'value' for each attempt

    Example:
        [{'timestamp': 1621490047833,
          'duration': 90184,
          'activity': 'p05jxcyxhb3wtcw4zx',
          'static_data': {'point': 1,
                          'score': 100,
                          'total_attempts': 4,
                          'total_bonus_collected': 0,
                          'total_jewels_collected': 4},
          'temporal_slices': [
              {'duration': 0,'item': 1, 'level': 1, 'status': True, 'value': None},
              {'duration': 1561, 'item': 2, 'level': 1, 'status': True, 'value': None},
              {'duration': 372, 'item': 3, 'level': 1, 'status': True, 'value': None},
              {'duration': 613, 'item': 4, 'level': 1, 'status': True, 'value': None}]
        }],
    """
    return
