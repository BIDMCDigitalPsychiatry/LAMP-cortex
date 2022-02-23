""" Module for raw feature jewels_a """
import LAMP
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
        activity_name (str): 'lamp.jewels_a'
        static_data (dict): a dict which includes 'point', 'score', 'total_attempts',
                'total_bonus_collected', 'total_jewels_collected'
        temporal_slices (list): list of dicts which include the 'duration',
                'item', 'level', 'status', and 'value' for each attempt

    Example:
        [{'timestamp': 1621490047833,
          'duration': 90184,
          'activity': 'p05jxcyxhb3wtcw4aazx',
          'activity_name': 'lamp.jewels_a',
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
    jewels_a_ids = [activity['id'] for activity in
                    LAMP.Activity.all_by_participant(kwargs['id'])['data']
                    if activity['spec'] == 'lamp.jewels_a']

    _jewels_a = [{'timestamp': res['timestamp'],
                  'duration': res['duration'],
                  'activity': res['activity'],
                  'activity_name': 'lamp.jewels_a',
                  'static_data': res['static_data'],
                  'temporal_slices': res['temporal_slices']}
                 for res in LAMP.ActivityEvent.all_by_participant(kwargs['id'],
                                                                  _from=kwargs['start'],
                                                                  to=kwargs['end'],
                                                                  _limit=_limit)['data']
                 if res['activity'] in jewels_a_ids]

    while _jewels_a and recursive:
        _to = _jewels_a[-1]['timestamp']
        _jewels_a_next = [{'timestamp': res['timestamp'],
                           'duration': res['duration'],
                           'activity':res['activity'],
                           'activity_name':'lamp.jewels_a',
                           'static_data':res['static_data'],
                           'temporal_slices':res['temporal_slices']}
                          for res in LAMP.ActivityEvent.all_by_participant(kwargs['id'],
                                                                           _from=kwargs['start'],
                                                                           to=_to,
                                                                           _limit=_limit)['data']
                          if res['activity'] in jewels_a_ids]

        if not _jewels_a_next: break
        if _jewels_a_next[-1]['timestamp'] == _to: break
        _jewels_a += _jewels_a_next

    return _jewels_a
