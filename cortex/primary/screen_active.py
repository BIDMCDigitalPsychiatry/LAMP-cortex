""" Module for computing screen active bouts from screen state """
import datetime
import LAMP

from ..feature_types import primary_feature
from ..raw.screen_state import screen_state

@primary_feature(
    name="cortex.screen_active",
    dependencies=[screen_state]
)
def screen_active(attach=False,
                  **kwargs):
    """ Builds bout of screen activity.

        Checks for both state = 0 --> ON
                    and state = 0 --> OFF
        and compares to activity data to determine which is correct.
    """
    # if attach then run it for the entrire thing and return the entire thing
    # otherwise run it for the entire thing but keep the original timestamps
    # get new timestamps
    start_time = 0
    end_time = int(datetime.datetime.now().timestamp()) * 1000

    # get all of the data for the bouts
    _screen_state = list(reversed(screen_state(id=kwargs['id'],
                                               start=start_time,
                                               end=end_time)['data']))
    has_raw_data = 1
    if len(_screen_state) == 0:
        has_raw_data = 0

    # Ensure state is present; convert value if not
    for _event in _screen_state:
        if 'state' not in _event:
            if 'data' not in _event:
                _event['state'] = _event['value']
            else:
                _event['state'] = _event['data']['value']

    # Initialize
    _screen_active = _get_screen_state_data(_screen_state, flipped=0)
    _screen_active_flipped = _get_screen_state_data(_screen_state, flipped=1)

    # figure out which one is correct
    # find activity, determine whether screen = 0 or 1 at this time
    activities = LAMP.ActivityEvent.all_by_participant(kwargs['id'])['data']
    _ret_screen_active = []
    if len(activities) > 0:
        screen_on_time = activities[0]['timestamp']
        val = [loc for loc in _screen_active if loc['start'] <= screen_on_time <= loc['end']]
        if len(val) == 1:
            _ret_screen_active = _screen_active
        else:
            _ret_screen_active = _screen_active_flipped
    else:
        # assume normal is correct
        _ret_screen_active = _screen_active
        
    # filter out events that 
    return {'data': _ret_screen_active, 'has_raw_data': has_raw_data}

def _get_screen_state_data(_screen_state, flipped=0):
    on_events = [1, 3]
    off_events = [0, 2]
    if flipped:
        on_events = [0, 2]
        off_events = [1, 3]

    _screen_active = []
    start = True # if looking for start
    bout = {}
    for i in range(len(_screen_state) - 1):
        elapsed = _screen_state[i+1]['timestamp'] - _screen_state[i]['timestamp']
        # For normal
        if (elapsed < 1000 and _screen_state[i+1]['state'] in on_events
            and _screen_state[i]['state'] in on_events):
            continue
        if start and _screen_state[i]['state'] in on_events:
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
