""" Module for computing screen active bouts from screen state """
import numpy as np
import pandas as pd

from ..feature_types import primary_feature
from ..raw.accelerometer import accelerometer

@primary_feature(
    name="cortex.acc_jerk",
    dependencies=[accelerometer]
)
def acc_jerk(threshold=500,
             attach=False,
             **kwargs):
    """ Computes the jerk of the accelerometer data.
        Rate at which the participant's accelerometer data changes with respect to time.

        params:
            threshold - the max difference between points to be computed in the sum in ms
                (ie if there is too large of a gap in time between accelerometer
                points, jerk has little meaning)
            attach - indicates whether to use LAMP.Type.attachments in calculating the feature
        returns:
            the jerk in m / s^3
    """
    _acc = accelerometer(**kwargs)['data']
    if _acc:
        has_raw_data = 1
        acc_df = pd.DataFrame(_acc)[['x', 'y', 'z', 'timestamp']]
        acc_df['timestamp_shift'] = acc_df['timestamp'].shift()
        acc_df = acc_df[acc_df['timestamp'] != acc_df['timestamp_shift']]
        acc_df['dt'] = (acc_df['timestamp'].shift() - acc_df['timestamp']) / 1000
        acc_df['x_shift'] = acc_df['x'].shift()
        acc_df['y_shift'] = acc_df['y'].shift()
        acc_df['z_shift'] = acc_df['z'].shift()
        acc_df = acc_df[acc_df['dt'] < (threshold / 1000)]
        # if there are no datapoints with small enough dts then skip this computation
        if len(acc_df) > 0:
            x_sum = (acc_df['x_shift'] - acc_df['x']) / acc_df['dt']
            y_sum = (acc_df['y_shift'] - acc_df['y']) / acc_df['dt']
            z_sum = (acc_df['z_shift'] - acc_df['z']) / acc_df['dt']
            acc_df['acc_jerk'] = np.sqrt((x_sum.pow(2) + y_sum.pow(2) + z_sum.pow(2)))
            acc_df = acc_df.dropna()
            acc_df = acc_df[['timestamp', 'timestamp_shift', 'acc_jerk']]
            acc_df.columns = ['start', 'end', 'acc_jerk']
            _ret = list(acc_df[['start', 'end', 'acc_jerk']].T.to_dict().values())
        else:
            _ret = []
    else:
        has_raw_data = 0
        _ret = []

    return {'data': _ret, 'has_raw_data': has_raw_data}
