from ..feature_types import secondary_feature
from ..raw.gps import gps
import pandas as pd
import numpy as np
import similaritymeasures
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

MS_IN_A_DAY = 86400000

'''
@secondary_feature(
    name='cortex.feature.frechet',
    dependencies=[gps]
'''
def similarity_measures(LOOKBACK=MS_IN_A_DAY, **kwargs):
    """
    Calculate Frechet Distance between two trajectories
    """
    gps1 = gps(**kwargs)
    if gps1:
        arr1 = pd.DataFrame(gps1)[['latitude', 'longitude']].to_numpy()
    else:
        return None    
    start2 = kwargs['start'] - LOOKBACK
    end2 = kwargs['end'] - LOOKBACK
    gps2 = gps(id = kwargs['id'], start = start2, end = end2)
    if gps2:
        arr2 = pd.DataFrame(gps2)[['latitude', 'longitude']].to_numpy()
        discrete_frechet = similaritymeasures.frechet_dist(arr1, arr2)
        area_between = similaritymeasures.area_between_two_curves(arr1, arr2)
        pcm = similaritymeasures.pcm(arr1, arr2)
        curve_length = similaritymeasures.curve_length_measure(arr1, arr2)
        fastDTW_score, _ = fastdtw(arr1, arr2, dist=euclidean)
        
    else:
        arr2 = None #testing 
    
    return {'timestamp':kwargs['start'], 
            'frechet_distance': discrete_frechet, 
            'area_between': area_between, 
            'partial_curve_mapping': pcm, 
            'curve_length_similarity': curve_length, 
            'fastDTW_score': fastDTW_score}