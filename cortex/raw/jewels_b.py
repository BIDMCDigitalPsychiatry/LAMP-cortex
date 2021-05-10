from ..feature_types import raw_feature
import LAMP


@raw_feature(
    name="lamp.jewels_b",
    dependencies=["lamp.jewels_b"]
)
def jewels_b(resolution=None, limit=20000, cache=True, **kwargs):

    jewels_b_ids = [activity['id'] for activity in
                    LAMP.Activity.all_by_participant(kwargs['id'])['data']
                    if activity['spec'] == 'lamp.jewels_b']

    _jewels_b = [{'timestamp': res['timestamp'],
                  'duration': res['duration'],
                  'activity': res['activity'],
                  'activity_name': 'lamp.jewels_b',
                  'static_data': res['static_data'],
                  'temporal_slices': res['temporal_slices']}
                 for res in LAMP.ActivityEvent.all_by_participant(kwargs['id'],
                                                                  _from=kwargs['start'],
                                                                  to=kwargs['end'],
                                                                  _limit=limit)['data']
                 if res['activity'] in jewels_b_ids]

    while _jewels_b:
        kwargs['end'] = _jewels_b[-1]['timestamp']
        _jewels_b_next = [{'timestamp': res['timestamp'],
                           'duration': res['duration'],
                           'activity':res['activity'],
                           'activity_name':'lamp.jewels_b',
                           'static_data':res['static_data'],
                           'temporal_slices':res['temporal_slices']}
                          for res in LAMP.ActivityEvent.all_by_participant(kwargs['id'],
                                                                           _from=kwargs['start'],
                                                                           to=kwargs['end'],
                                                                           _limit=limit)['data']
                          if res['activity'] in jewels_b_ids]

        if not _jewels_b_next: break
        if _jewels_b_next[-1]['timestamp'] == kwargs['end']: break
        print('append')
        _jewels_b += _jewels_b_next
    return _jewels_b
