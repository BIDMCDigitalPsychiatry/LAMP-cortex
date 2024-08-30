""" Module for screen_unlock_duration from raw device_usage """
import numpy as np
from ..feature_types import secondary_feature, log
from ..raw.device_usage import device_usage

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.screen_unlock_duration',
    dependencies=[device_usage]
)
def screen_unlock_duration(**kwargs):
    """Returns the amount of time the screen was unlocked.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window
                for which the feature is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window
                for which the feature is being generated. Required.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window
            (same as kwargs['start']).
            value (float): The amount of time the screen was unlocked.
    """
    _screen_states = device_usage(**kwargs)['data']

    screen_unlock_duration = np.sum(state['totalUnlockDuration'] for state in _screen_states)
    
    if len(_screen_states) == 0:
        number = None

    else:
        number = screen_unlock_duration

    return {'timestamp': kwargs['start'], 'value': number}
