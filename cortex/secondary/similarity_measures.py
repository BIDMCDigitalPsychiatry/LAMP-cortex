from ..feature_types import secondary_feature, log
from ..raw.gps import gps
import pandas as pd
import numpy as np
import similaritymeasures
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

MS_IN_A_DAY = 86400000


@secondary_feature(
    name='cortex.feature.similarity_measures',
    dependencies=[gps]
)
def similarity_measures(LOOKBACK=MS_IN_A_DAY, **kwargs):
    """
    Calculate all similarity measures between two trajectories
    """
    log.info(f'Loading GPS data for 1st trajectory...')
    gps1 = gps(**kwargs)
    if gps1:
        arr1 = pd.DataFrame(gps1)[['latitude', 'longitude']].to_numpy()
    else:
        return {'timestamp':kwargs['start'], 
                'frechet_distance': None, 
                'area_between': None, 
                'partial_curve_mapping': None, 
                'curve_length_similarity': None, 
                'fastDTW_score': None}   
    log.info(f'Loading GPS data for 2nd trajectory...')
    start2 = kwargs['start'] - LOOKBACK
    end2 = kwargs['end'] - LOOKBACK
    gps2 = gps(id = kwargs['id'], start = start2, end = end2)
    
    log.info(f'Calculating all similarity measures...')
    if gps2:
        arr2 = pd.DataFrame(gps2)[['latitude', 'longitude']].to_numpy()
        log.info(f'Calculating Frechet...')
        discrete_frechet = similaritymeasures.frechet_dist(arr1, arr2)
        log.info(f'Calculating Area between...')
        area_between = similaritymeasures.area_between_two_curves(arr1, arr2)
        log.info(f'Calculating PCM...')
        pcm = similaritymeasures.pcm(arr1, arr2)
        log.info(f'Calculating curve length...')
        curve_length = similaritymeasures.curve_length_measure(arr1, arr2)
        log.info(f'Calculating FastDTW...')
        fastDTW_score, _ = fastdtw(arr1, arr2, dist=euclidean)
        
    else:
        return {'timestamp':kwargs['start'], 
                'frechet_distance': None, 
                'area_between': None, 
                'partial_curve_mapping': None, 
                'curve_length_similarity': None, 
                'fastDTW_score': None}
    
    return {'timestamp':kwargs['start'], 
            'frechet_distance': discrete_frechet, 
            'area_between': area_between, 
            'partial_curve_mapping': pcm, 
            'curve_length_similarity': curve_length, 
            'fastDTW_score': fastDTW_score}


