""" Module for raw feature funny_memory """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.funny_memory",
    dependencies=["lamp.funny_memory"]
)
def funny_memory(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    """ Get funny_memory data bounded by time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the event.
        duration (int): the duration in ms
        activity (str): the activity id
        static_data (dict): a dict which includes 'start_time', 'today_date', 'month',
                'year', 'day', 'season', 'image_exposure_time', 'learning_trials', 'delay_time',
                'number_of_correct_pairs_recalled', 'number_of_correct_items_recalled',
                'number_of_correct_recognized', 'number_of_correct_force_choice',
                'number_of_total_pairs'
        temporal_slices (list): list of dicts which include the 'duration',
                'item', 'level', 'type', and 'value' for each attempt

    Example:
        [{'timestamp': 1741289577501,
          'duration': 174549,
          'activity': '3g3d5feth4frgf61adkh',
          'static_data': {'start_time': '14:30',
                          'today_date': '6',
                          'month': 'March',
                          'year': '2025',
                          'day': 'Thursday',
                          'season': 'Winter',
                          'image_exposure_time': 2000,
                          'learning_trials': 1,
                          'delay_time': 60,
                          'number_of_correct_pairs_recalled': 0,
                          'number_of_correct_items_recalled': 0,
                          'number_of_correct_recognized': 0,
                          'number_of_correct_force_choice': 5,
                          'number_of_total_pairs': 6},
          'temporal_slices': [
              {'duration': 23569, 'item': 3, 'level': 'Trial', 'type': False, 'value': None},
              {'duration': 5765, 'item': 5, 'level': 'Trial', 'type': False, 'value': None},
              {'duration': 5605, 'item': 4, 'level': 'Trial', 'type': False, 'value': None},
              {'duration': 6630, 'item': 1, 'level': 'Trial', 'type': False, 'value': None},
              {'duration': 5250, 'item': 0, 'level': 'Trial', 'type': False, 'value': None},
              {'duration': 69853, 'item': None, 'level': 'recall', 'type': False, 'value': None},
              {'duration': 75856, 'item': 3, 'level': 'recognition1', 'type': False, 'value': None},
              {'duration': 6035, 'item': 3, 'level': 'recognition2', 'type': True, 'value': None},]
        }],
    """
    return