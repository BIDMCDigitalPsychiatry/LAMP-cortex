""" Module for computing screen active bouts from device state """
import datetime
import LAMP

from ..feature_types import primary_feature
from ..raw.device_state import device_state

@primary_feature(
    name="cortex.screen_active",
    dependencies=[device_state]
)
def screen_active(attach=True,
                  duration_threshold=1000 * 60 * 60 * 2, #2 hours
                  **kwargs):
    """Builds bout of screen activity.

    Relies on the 'device_state' raw sensor. In the past, on events/off events
    were encoded differently for iOS and Android devices. For this functionality,
    please use an older version of cortex (03.11.2022 or earlier). These events
    should now be consistent across iOS and Android.

    The mapping is:
        0 --> "screen_on"
        1 --> "screen_off"
        2 --> "locked"
        3 --> "unlocked"

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

    # get all of the data for the bouts
    _device_state = list(reversed(device_state(id=kwargs['id'],
                                               start=start_time,
                                               end=end_time)['data']))
    has_raw_data = 1
    if len(_device_state) == 0:
        has_raw_data = 0

    # Ensure value is present; convert state if not
    for _event in _device_state:
        if 'value' not in _event:
            if 'data' not in _event:
                _event['value'] = _event['state']
            else:
                _event['value'] = _event['data']['state']

    # Initialize
    _screen_active = _get_device_state_data(_device_state,
                                            duration_threshold=duration_threshold,
                                            flipped=0)
    _screen_active_flipped = _get_device_state_data(_device_state,
                                                    duration_threshold=duration_threshold,
                                                    flipped=1)

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

    return {'data': _ret_screen_active, 'has_raw_data': has_raw_data}

def _get_device_state_data(_device_state,
                           duration_threshold=1000 * 60 * 60 * 2,
                           flipped=0):
    """ Get device_state data bouts.

        Arg:
            _device_state (list): the raw device state data
            duration_threshold (int, unit: ms, default: 2 hours): exclude bouts
                longer than this threshold
            flipped (boolean, default: 0): whether to use the screen on bouts
                or screen off bouts
    """

    on_events = [0, 3]
    off_events = [1, 2]

    if flipped:
        on_events = [1, 2]
        off_events = [0, 3]

    _screen_active = []
    start = True # if looking for start
    bout = {}

    for i in range(len(_device_state) - 1):
        elapsed = _device_state[i+1]['timestamp'] - _device_state[i]['timestamp']
        if (elapsed < 1000 and _device_state[i+1]['value'] in on_events
            and _device_state[i]['value'] in on_events):
            continue
        if start and _device_state[i]['value'] in on_events:
            bout['start'] = _device_state[i]['timestamp']
            start = False
        elif not start and _device_state[i]['value'] in off_events:
            bout['end'] = _device_state[i]['timestamp']
            bout['duration'] = bout['end'] - bout['start']

            #If bout duration too long, ignore it
            if bout['duration'] <= duration_threshold:
                _screen_active.append(bout)

            bout = {}
            start = True

    if not start and _device_state[-1]['value'] in off_events:
        bout['end'] = _device_state[-1]['timestamp']
        bout['duration'] = bout['end'] - bout['start']
        _screen_active.append(bout)

    return _screen_active
