""" Module for computing screen active bouts from screen state """
from ..feature_types import primary_feature, log
from ..raw.screen_state import screen_state

@primary_feature(
    name="cortex.screen_active",
    dependencies=[screen_state],
    attach=True
)
def screen_active(**kwargs):
    """
    Builds bout of screen activitty
    """
    log.info("IN SCREEN ACTIVE")
    log.info(kwargs['start'])
    log.info(kwargs['end'])
    _screen_state = list(reversed(screen_state(**kwargs)['data']))
    log.info(_screen_state)

    on_events = [0, 2]# [1, 3]
    off_events = [1, 3]# [0, 2]
    # Ensure state is present; convert value if not
    for _event in _screen_state:
        if 'state' not in _event:
            if 'data' not in _event:
                _event['state'] = _event['value']
            else:
                _event['state'] = _event['data']['value']

    # Initialize
    _screen_active = []
    start = True # if looking for start
    bout = {}
    for i in range(len(_screen_state) - 1):
        log.info(i)
        log.info(_screen_state[i])
        if i == len(_screen_state) - 1:
            log.ifo(_screen_state[i])
        elapsed = _screen_state[i+1]['timestamp'] - _screen_state[i]['timestamp']
        if (elapsed < 1000 and _screen_state[i+1]['state'] in on_events
            and _screen_state[i]['state'] in on_events):
            continue
        elif start and _screen_state[i]['state'] in on_events:
            bout['start'] = _screen_state[i]['timestamp']
            start = False
            log.info("setting start")
            log.info(_screen_state[i])
        elif not start and _screen_state[i]['state'] in off_events:
            bout['end'] = _screen_state[i]['timestamp']
            bout['duration'] = bout['end'] - bout['start']
            log.info("adding a bout...")
            log.info(bout)
            _screen_active.append(bout)

            bout = {}
            start = True

    if not start and _screen_state[-1]['state'] in off_events:
        bout['end'] = _screen_state[-1]['timestamp']
        bout['duration'] = bout['end'] - bout['start']
        log.info("adding a bout 2...")
        _screen_active.append(bout)

    return _screen_active
