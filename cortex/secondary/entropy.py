from ..feature_types import secondary_feature
from ..primary.significant_locations import significant_locations
from ..raw import sensors_results, cognitive_games_results, surveys_results

import math
import datetime
import pandas as pd

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.entropy',
    dependencies=[significant_locations]
)
def entropy(id, start, end, resolution=MS_IN_A_DAY, **kwargs):
    """
    Calculate entropy 
    """
    timestamp_list = kwargs['timestamp_list']

    #Find significant locations for each window
    entropy_data = []
    for window in zip(timestamp_list[:-1], timestamp_list[1:]):
        window_start, window_end = window[0], window[1]
        sig_locs = significant_locations(id, start=window_start, end=window_end)
        ent = sum([loc['proportion'] * math.log(loc['proportion']) for loc in sig_locs])
        entropy_data.append({'timestamp':window_start, 'duration':resolution, 'entropy':ent})
    
    return entropy_data 