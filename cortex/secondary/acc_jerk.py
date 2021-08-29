""" Module for computing jerk from raw accelerometer data """
import math
import pandas as pd
import numpy as np

from ..feature_types import secondary_feature
from ..raw.accelerometer import accelerometer

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.acc_energy',
    dependencies=[accelerometer]
)
def acc_jerk(threshold=500, **kwargs):
    """ Computes the jerk of the accelerometer data.
        Jerk is the squared differences in accelerometer.

        params:
            threshold - the max difference between points to be computed in the sum
                (ie if there is too large of a gap in time between accelerometer
                points, jerk has little meaning)
    """
    _acc = accelerometer(**kwargs)['data']
    jerk = None
    if _acc:
        acc_df = pd.DataFrame(_acc)[['x', 'y', 'z', 'timestamp']]
        acc_df = acc_df[acc_df['timestamp'] != acc_df['timestamp'].shift()]
        acc_df['dt'] =  acc_df['timestamp'].shift() - acc_df['timestamp']
        acc_df['x_shift'] = acc_df['x'].shift()
        acc_df['y_shift'] = acc_df['y'].shift()
        acc_df['z_shift'] = acc_df['z'].shift()
        acc_df = acc_df[acc_df['dt'] < threshold]
        # if there are no datapoints with small enough dts then skip this computation
        if len(acc_df) > 0:
            x_sum = np.square((acc_df['x_shift'] - acc_df['x']) / acc_df['dt']).sum()
            y_sum = np.square((acc_df['y_shift'] - acc_df['y']) / acc_df['dt']).sum()
            z_sum = np.square((acc_df['z_shift'] - acc_df['z']) / acc_df['dt']).sum()
            jerk = math.sqrt((x_sum + y_sum + z_sum) / len(acc_df))

    return {'timestamp': kwargs['start'], 'acc_jerk': jerk}
