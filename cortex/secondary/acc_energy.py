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
    df = accelerometer(**kwargs)['data']
    if df:
        df = pd.DataFrame(df)[['x', 'y', 'z']]
        n = len(df)
        a = np.square(df).sum(axis=1).sum()
        acc_energy = math.sqrt(a/n)
        return {'timestamp':kwargs['start'], 'acc_energy': acc_energy}
    else:
        return None