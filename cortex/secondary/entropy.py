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
    """
    Calculate entropy
        sum (p log p)
        where p is the proportion of time spent at each signficant location
    """
    if kwargs.get('method') is not None:
        _significant_locations = significant_locations(id=kwargs['id'],
                                                       start=kwargs['start'],
                                                       end=kwargs['end'],
                                                       method=kwargs['method'])
    else:
        _significant_locations = significant_locations(id=kwargs['id'],
                                                       start=kwargs['start'],
                                                       end=kwargs['end'])

    if len(_significant_locations['data']) == 0:
        _entropy = None

    _entropy = -sum([loc['proportion'] * math.log(loc['proportion'])
                     for loc in _significant_locations['data'] if 0 < loc['proportion'] <= 1])
    return {'timestamp': kwargs['start'], 'value': _entropy}
