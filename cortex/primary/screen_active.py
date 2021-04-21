from ..feature_types import primary_feature
from ..raw.screen_state import screen_state

import pandas as pd

@primary_feature(
    name="cortex.screen_active",
    dependencies=[screen_state],
    attach=True
)
def screen_active(**kwargs):
    """
    Builds bout of screen activitty
    """
    _screen_state = list(reversed(screen_state(**kwargs)['data']))

    on_events = [1, 3]
    off_events = [0, 2]
    #Ensure state is present; convert value if not
    for _event in _screen_state:
        if 'state' not in _event:
            if 'data' not in _event:
                _event['state'] = _event['value']
            else:
                _event['state'] = _event['data']['value']

    #Initialize
    _screen_active = []
    start = True #if looking for start 
    bout = {}
    for i in range(len(_screen_state) - 1):
        elapsed = _screen_state[i+1]['timestamp'] - _screen_state[i]['timestamp']
        if elapsed < 1000 and _screen_state[i+1]['state'] in on_events and _screen_state[i]['state'] in on_events:
            continue
        elif start and _screen_state[i]['state'] in on_events:
            bout['start'] = _screen_state[i]['timestamp']
            start = False 
        elif not start and _screen_state[i]['state'] in off_events:
            bout['end'] = _screen_state[i]['timestamp']
            bout['duration'] = bout['end'] - bout['start']
            _screen_active.append(bout)

            bout = {}
            start = True
    
    if not start and _screen_state[-1]['state'] in off_events:
            bout['end'] = _screen_state[-1]['timestamp']
            bout['duration'] = bout['end'] - bout['start']
            _screen_active.append(bout)
            
    return _screen_active
