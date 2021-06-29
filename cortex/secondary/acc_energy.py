from ..feature_types import secondary_feature, log
from ..raw.accelerometer import accelerometer
import math
import pandas as pd
import numpy as np

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.acc_energy',
    dependencies=[accelerometer]
)
def acc_energy(**kwargs):
    log.info(f'Loading Accelerometer data...')
    _acc = accelerometer(**kwargs)['data']
    if _acc:
        df = pd.DataFrame(_acc)[['x', 'y', 'z']]
        df = df[df['timestamp'] != df['timestamp'].shift()]
        n = len(df)
        a = np.square(df).sum(axis=1).sum()
        acc_energy = math.sqrt(a/n)
        
    else:
        acc_energy = None
    
    return {'timestamp':kwargs['start'], 'acc_energy': acc_energy}