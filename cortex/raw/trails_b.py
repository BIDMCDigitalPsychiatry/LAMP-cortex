""" Module for raw feature trails_b """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.trails_b",
    dependencies=["lamp.trails_b"]
)
def trails_b(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    """ Get trails_b data bounded by time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the event.
        duration (int): the duration in ms
        activity (str): the activity id
        static_data (dict): a dict which includes 'point', 'score', 'total_questions',
                'correct_answers', 'wrong_answers'
        temporal_slices (list): list of dicts which include the 'duration',
                'item', 'level', 'type', and 'value' for each attempt

    Example:
        [{'timestamp': 1739548751369,
          'duration': 10272,
          'activity': '79ct4dmby98xn9mcehsk',
          'static_data': {'correct_answers': 12,
                          'point': 1,
                          'total_questions': 12,
                          'wrong_answers': 0,
                          'score': 40},
          'temporal_slices': [
              {'duration': 1739548753201, 'item': '1', 'level': 1, 'type': True, 'value': None},
              {'duration': 507, 'item': 'A', 'level': 1, 'type': True, 'value': None},
              {'duration': 647, 'item': '2', 'level': 1, 'type': True, 'value': None},
              {'duration': 728, 'item': 'B', 'level': 1, 'type': True, 'value': None},
              {'duration': 406, 'item': '3', 'level': 1, 'type': True, 'value': None},
              {'duration': 451, 'item': 'C', 'level': 1, 'type': True, 'value': None},
              {'type': 'manual_exit', 'value': True}],
        }],
    """
    return