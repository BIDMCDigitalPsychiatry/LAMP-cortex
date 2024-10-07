""" Module for computing battery level from device state """
import datetime
import statistics

from ..feature_types import secondary_feature
from ..raw.device_state import device_state

@secondary_feature(
    name="cortex.battery_level",
    dependencies=[device_state]
)
def battery_level(**kwargs):
    """Returns the mean battery level in a time window.

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
            value (float): The mean battery level in that time window.
    """
    _device_states = device_state(**kwargs)['data']
    
    if len(_device_states) == 0:
        battery_level = None
    else:
        battery_levels = [state['battery_level'] for state in _device_states]
        battery_level = statistics.mean(battery_levels)
    return {'timestamp': kwargs['start'], 'value': battery_level}
