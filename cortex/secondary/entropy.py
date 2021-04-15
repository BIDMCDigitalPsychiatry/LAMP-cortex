from ..feature_types import secondary_feature
from ..primary.significant_locations import significant_locations

import math
import datetime
import pandas as pd

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.entropy',
    dependencies=[significant_locations]
)
def entropy(resolution=MS_IN_A_DAY, **kwargs):
    """
    Calculate entropy 
    """
    _significant_locations = significant_locations(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    if len(_significant_locations['data']) == 0:
        _entropy = None
    _entropy = sum([loc['proportion'] * math.log(loc['proportion']) for loc in _significant_locations['data']])
    if _entropy == 0: #no sig locs
        _entropy = None
    return {'timetamp':kwargs['start'], 'entropy': _entropy}
