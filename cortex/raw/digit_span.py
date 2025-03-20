""" Module for raw feature digit_span """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.digit_span",
    dependencies=["lamp.digit_span"]
)
def digit_span(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    """ Get digit_span data bounded by time interval.

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
        [{'timestamp': 1742234809723,
          'duration': 90184,
          'activity': 'p05jxcyxhb3wtcw4zx',
          'duration': 55626,
          'static_data': {'correct_answers': 10,
                          'point': 1,
                          'score': 59,
                          'total_questions': 17,
                          'wrong_answers': 7},
          'temporal_slices': [
                {'duration': 583, 'item': 3, 'level': 1, 'type': True, 'value': None},
                {'duration': 1500, 'item': 6, 'level': 1, 'type': True, 'value': None},
                {'duration': 6519, 'item': 7, 'level': 2, 'type': True, 'value': None},
                {'duration': 647, 'item': 1, 'level': 2, 'type': True, 'value': None},
                {'duration': 601, 'item': 4, 'level': 2, 'type': True, 'value': None},
                {'duration': 699, 'item': 9, 'level': 2, 'type': True, 'value': None},
                {'duration': 11555, 'item': 9, 'level': 3, 'type': False, 'value': None},
                {'duration': 446, 'item': 6, 'level': 3, 'type': False, 'value': None},
                {'type': 'manual_exit', 'value': False}],
        }],
    """
    return