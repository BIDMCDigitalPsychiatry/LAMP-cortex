from ..feature_types import secondary_feature
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
    """
    Calculate hometime
    hometime is the proportion of time spent at home
    """
    _significant_locations = significant_locations(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    if len(_significant_locations['data']) == 0:
        hometime = None
    
    return {'timetamp':kwargs['start'], 'hometime': hometime}




