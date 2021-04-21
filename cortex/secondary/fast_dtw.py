from ..feature_types import secondary_feature, log
from ..raw.gps import gps
import pandas as pd
import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

MS_IN_A_DAY = 86400000


@secondary_feature(
    name='cortex.feature.fast_dtw',
    dependencies=[gps]
)
def fast_dtw(LOOKBACK=MS_IN_A_DAY, **kwargs):
    """
    Calculate FastDTW score between two trajectories
    """
    log.info(f'Loading GPS data for 1st trajectory...')
    gps1 = gps(**kwargs)
    if gps1:
        arr1 = pd.DataFrame(gps1)[['latitude', 'longitude']].to_numpy()
    else:
        return None
    log.info(f'Loading GPS data for 2nd trajectory...')
    start2 = kwargs['start'] - LOOKBACK
    end2 = kwargs['end'] - LOOKBACK
    gps2 = gps(id = kwargs['id'], start = start2, end = end2)
    log.info(f'Calculating fastDTW Distance...')
    if gps2:
        arr2 = pd.DataFrame(gps2)[['latitude', 'longitude']].to_numpy()
        fastDTW_score, _ = fastdtw(arr1, arr2, dist=euclidean)
    else:
        arr2 = None #testing
    
    return {'timestamp':kwargs['start'], 'fastDTW_score': fastDTW_score}
    