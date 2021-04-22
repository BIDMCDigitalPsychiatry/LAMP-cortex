from ..feature_types import secondary_feature, log
from ..primary.significant_locations import significant_locations

import math
import datetime
import pandas as pd

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.hometime',
    dependencies=[significant_locations]
)
def hometime(resolution=MS_IN_A_DAY, **kwargs):
    _significant_locations = significant_locations(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    if len(_significant_locations['data']) == 0:
        _hometime = None
    else:
        _hometime = [loc['duration'] for loc in _significant_locations['data'] if loc['rank'] == 0][0]
    return {'timestamp':kwargs['start'], 'hometime': _hometime}
