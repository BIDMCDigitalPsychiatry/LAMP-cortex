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
        Jerk is the rate at which acceleration changes with respect to time.

        Args:
            threshold (int): The max difference between points to be computed in the sum, in ms.
                (I.e. if there is too large of a gap in time between accelerometer
                points, jerk has little meaning)
            attach (boolean): Indicates whether to use LAMP.Type.attachments in calculating the feature.
            **kwargs:
                id (string): The participant's LAMP id. Required.
                start (int): The initial UNIX timestamp (in ms) of the window for which the feature 
                    is being generated. Required.
                end (int): The last UNIX timestamp (in ms) of the window for which the feature 
                    is being generated. Required.
        Returns:
            A dict with fields:
                data (list): A list of dicts, with each dict having 3 keys: 'start', 'end', and 'acc_jerk'.
                    'acc_jerk' is the accelerometer jerk in m / s^3
                has_raw_data (int): Indicates whether raw data is present. 

        Example:
            [{'start': 1625171685730.0,
              'end': 1625171685929.0,
              'acc_jerk': 1.7460826170665855},
             {'start': 1625171685532.0,
              'end': 1625171685730.0,
              'acc_jerk': 1.00943647205571},
             {'start': 1625171685334.0,
              'end': 1625171685532.0,
              'acc_jerk': 0.051706493081616275}]
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
