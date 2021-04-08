
from ..feature_types import secondary_feature
from ..raw.gps import gps
import pandas as pd
import numpy as np
import similaritymeasures

MS_IN_A_DAY = 86400000

'''
@secondary_feature(
    name='cortex.feature.frechet',
    dependencies=[gps]
'''
def frechet(LOOKBACK=MS_IN_A_DAY, **kwargs):
    """
    Calculate Frechet Distance between two trajectories
    """
    arr1 = pd.DataFrame(gps(**kwargs))[['latitude', 'longitude']].to_numpy()
    start2 = kwargs['start'] - LOOKBACK
    end2 = kwargs['end'] - LOOKBACK
    #arr2 = pd.DataFrame(gps(id = kwargs['id'], start = start2, end = end2))[['latitude', 'longitude']].to_numpy()
    return arr1
    


