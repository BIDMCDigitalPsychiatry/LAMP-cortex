""" Module for screen duration from primary feature screen active """
import numpy as np
from ..feature_types import secondary_feature
from ..primary.screen_active import screen_active

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.screen_duration',
    dependencies=[screen_active]
)
def screen_duration(**kwargs):
    """Computes screen_duration (in ms) by summing the screen_active periods over a
        given time.


    The (kwargs['start'], kwargs['end']) timestamps used within the function are
    different than the ones that should be passed in as parameters --
    'cortex.feature_types.secondary_features' is being called first. Please
    see documentation there for more detail.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.

    Returns:
        A dict consisting of:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The time (in ms) spent with the device screen on.

    """
    _screen_active = screen_active(**kwargs)
    _screen_duration = np.sum([active_bout['duration'] for active_bout in _screen_active['data']])
    # screen duration should be None if there is no data
    if _screen_active['has_raw_data'] == 0:
        _screen_duration = None
    return {'timestamp':kwargs['start'], 'value': _screen_duration}
