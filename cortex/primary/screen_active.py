""" Module for computing screen active bouts from screen state """
import datetime
import LAMP

from ..feature_types import primary_feature
from ..raw.screen_state import screen_state
from ..raw.analytics import analytics

@primary_feature(
    name="cortex.screen_active",
    dependencies=[screen_state, analytics]
)
def screen_active(attach=True,
                  duration_threshold=1000 * 60 * 60 * 2, #2 hours
                  **kwargs):
    """Builds bout of screen activity.

    Relies on the 'screen_state' raw sensor. On events/off events are encoded differently for iOS and Android devices.
    Accordingly, device type is found first using lamp.analytics.

    Args:
        attach (boolean): Indicates whether to use LAMP.Type.attachments in calculating the feature.
        duration_threshold (int): The maximum allowable duration of a screen active bout, in ms.
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.

    Returns:
        A dict with fields:
            data (list): The screen-on bouts, each one with a (start, end) timestamp.
            has_raw_data (int): Indicates whether there is raw data.
    """
    # if attach then run it for the entrire thing and return the entire thing
    # otherwise run it for the entire thing but keep the original timestamps
    # get new timestamps
    start_time = 0
    end_time = int(datetime.datetime.now().timestamp()) * 1000

    # get device type 
    _analytics = analytics(**kwargs)
    _device_types = [_event['device_type'] for _event in _analytics['data'] if 'device_type' in _event]
    _device_type = 'iOS' #default to ios

    for d in _device_types:
        if d not in ['iOS', 'Android']: #ignore non-smartphone reads
            continue
        _device_type = d
        break

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
    _screen_active = _get_screen_state_data(_screen_state, device_type=_device_type, duration_threshold=duration_threshold, flipped=0)
    _screen_active_flipped = _get_screen_state_data(_screen_state, device_type=_device_type, duration_threshold=duration_threshold, flipped=1)

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

def _get_screen_state_data(_screen_state,
                           device_type,
                           duration_threshold=1000 * 60 * 60 * 2,
                           flipped=0):

    if device_type == 'iOS':
        on_events = [0] #[1, 3]
        off_events = [1, 2] #[0, 2]
    elif device_type == 'Android':
        # ANDROID STUFF
        on_events = [0, 3] #[1, 3]
        off_events = [1, 2] #[0, 2]
    else:
        raise Exception('Unknown device type')

    if flipped:
        on_copy, off_copy = [n for n in on_events], [n for n in off_events]
        on_events = off_copy
        off_events = on_copy

    _screen_active = []
    start = True # if looking for start
    bout = {}

    for i in range(len(_screen_state) - 1):
        elapsed = _screen_state[i+1]['timestamp'] - _screen_state[i]['timestamp']
        if (elapsed < 1000 and _screen_state[i+1]['state'] in on_events
            and _screen_state[i]['state'] in on_events):
            continue
        if start and _screen_state[i]['state'] in on_events:
            bout['start'] = _screen_state[i]['timestamp']
            start = False
        elif not start and _screen_state[i]['state'] in off_events:
            bout['end'] = _screen_state[i]['timestamp']
            bout['duration'] = bout['end'] - bout['start']

            #If bout duration too long, ignore it
            if bout['duration'] <= duration_threshold:
                _screen_active.append(bout)

            bout = {}
            start = True

    if not start and _screen_state[-1]['state'] in off_events:
        bout['end'] = _screen_state[-1]['timestamp']
        bout['duration'] = bout['end'] - bout['start']
        _screen_active.append(bout)

    return _screen_active
