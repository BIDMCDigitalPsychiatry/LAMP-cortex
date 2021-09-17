from ..feature_types import raw_feature
import LAMP


@raw_feature(
    name="lamp.jewels_a",
    dependencies=["lamp.jewels_a"]
)
def jewels_a(_limit=10000, 
             cache=False,
             recursive=True,
             **kwargs):
    """
    Get jewels_a data bounded by time interval
    
    :param _limit (int): The maximum number of sensor events to query for in a single request
    :param cache (bool): Indicates whether to save raw data locally in cache dir
    :param recursive (bool): if True, continue requesting data until all data is returned; else just one request
    
    :return timestamp (int): The UTC timestamp for the jewels_a event.
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
        to = _jewels_a[-1]['timestamp']
        _jewels_a_next = [{'timestamp': res['timestamp'],
                           'duration': res['duration'],
                           'activity':res['activity'],
                           'activity_name':'lamp.jewels_a',
                           'static_data':res['static_data'],
                           'temporal_slices':res['temporal_slices']}
                          for res in LAMP.ActivityEvent.all_by_participant(kwargs['id'],
                                                                           _from=kwargs['start'],
                                                                           to=to,
                                                                           _limit=_limit)['data']
                          if res['activity'] in jewels_a_ids]

        if not _jewels_a_next: break
        if _jewels_a_next[-1]['timestamp'] == to: break
        _jewels_a += _jewels_a_next

    return _jewels_a