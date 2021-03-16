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
    _entropy = sum([loc['proportion'] * math.log(loc['proportion']) for loc in _significant_locations])
    return {'entropy': _entropy}
