from ..feature_types import secondary_feature, log
from ..raw.accelerometer import accelerometer
import pandas as pd
import numpy as np

MS_IN_A_DAY = 86400000


@secondary_feature(
    name='cortex.feature.stationary_proportion',
    dependencies=[accelerometer]
)
def stationary_proportion(g=9.57, eps=.1, col='z', **kwargs):
    """
    Compute the proportion of "stationary" accelerometer readings.
    An accelerometer reading is "stationary" if the z component is close to gravitational acceleration (9.81 m/s^2)
    """
    log.info(f'Loading Accelerometer data for 1st trajectory...')
    acc = accelerometer(**kwargs)['data']
    if acc:
        acc = pd.DataFrame(acc)[['x', 'y', 'z']]
        n = len(acc)
        ct = len(acc[(acc[col] >= g - eps) & (acc[col] <= g + eps)])
        stationary_proportion = round(ct/n, 5)    
    else:
        stationary_proportion = []
    
    
    return {'timestamp':kwargs['start'], 'stationary_proportion': stationary_proportion}
    
    

