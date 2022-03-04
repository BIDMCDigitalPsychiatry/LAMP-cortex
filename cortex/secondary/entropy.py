""" Module to compute entropy from primary feature significant_locations """
import math
from ..feature_types import secondary_feature
from ..primary.significant_locations import significant_locations

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.entropy',
    dependencies=[significant_locations]
)
def entropy(**kwargs):
    """Calculate entropy sum (p log p) where p is the proportion of time spent at each signficant location


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
            value (float): The entropy of significant locations visited.

    """
    _significant_locations = significant_locations(**kwargs)

    if len(_significant_locations['data']) == 0:
        _entropy = None
    else:
        _entropy = -sum([loc['proportion'] * math.log(loc['proportion'])
                     for loc in _significant_locations['data'] if 0 < loc['proportion'] <= 1])
    return {'timestamp': kwargs['start'], 'value': _entropy}
