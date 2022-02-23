""" Module to compute the longest inactive bout from accelerometer and screen state """
import numpy as np
import pandas as pd

from ..feature_types import secondary_feature
from ..raw.accelerometer import accelerometer
from ..raw.screen_state import screen_state


@secondary_feature(
    name="cortex.feature.new_inactive",
    dependencies=[accelerometer, screen_state]
)
def inactive_duration(jerk_threshold=500, **kwargs):
    """ Returns the duration in ms of the longest bout of inactive
        accelerometer and screen state.

        Jerk is recomputed here for speed purposes.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for
                which the feature is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for
                which the feature is being generated. Required.
        jerk_threshold (int): The max difference between points to be computed
                in the sum, in ms.(i.e. if there is too large of a gap in time
                between accelerometer points, jerk has little meaning)

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The inactive bout length in ms.
    """
    _ss = screen_state(**kwargs)['data']
    if _ss:
        _ss = pd.DataFrame(_ss)[['timestamp', 'value']]
        _ss = _ss[['timestamp', 'value']]
        _ss['start'] = _ss.timestamp.shift()
        _ss['prev_state'] = _ss.value.shift()
        _ss['dt'] = _ss.timestamp - _ss.start
        ss_start, ss_end = get_screen_bouts(_ss)
    else:
        print("no ss")
        return {'timestamp': kwargs['start'], 'value': None}

    _acc = accelerometer(**kwargs)['data']
    if _acc:
        acc_df = pd.DataFrame(_acc)[['x', 'y', 'z', 'timestamp']]
        acc_df = acc_jerk(acc_df, jerk_threshold)
        acc_start, acc_end = get_nonzero_jerk(acc_df)
    else:
        print("no acc")
        return {'timestamp': kwargs['start'], 'value': None}

    print(acc_start)
    print(acc_end)
    print(ss_start)
    print(ss_end)
    intersection = max_intersection(acc_start, acc_end, ss_start, ss_end)
    return {'timestamp': kwargs['start'], 'value': intersection}

def acc_jerk(acc_df, threshold):
    """ Function to compute jerk.

        Args:
            acc_df: the dataframe with raw accelerometer
            threshold (int): The max difference between points to be computed
                in the sum, in ms.(i.e. if there is too large of a gap in time
                between accelerometer points, jerk has little meaning)
        Returns:
            the computed jerk
    """
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
        return acc_df
    print("no acc above thresh")
    return []

def get_nonzero_jerk(df, threshold=3.0, inclusive=True):
    """ Get the intervals of non-zero jerk.

        Args:
            df: the df holding the jerk
            threshold: the threshold below which jerk is considered "inactive"
            inclusive: whether to include the end points
        Returns:
            list of intervals of non-zero jerk
    """
    state = False
    df['above_threshold'] = df['acc_jerk'] > threshold
    arr = np.array(df['above_threshold'])
    arr_ext = np.r_[False, arr==state, False]
    idx = np.flatnonzero(arr_ext[:-1] != arr_ext[1:])
    idx_list = list(zip(idx[:-1:2], idx[1::2] - int(inclusive)))
    max_length = 1
    acc_start = 0
    acc_end = 0
    if idx_list:
        print("no acc points")
        for tup in idx_list:
            tmp_start = df['start'].iloc[tup[0]]
            tmp_end = df['start'].iloc[tup[1]]
            interval = (tmp_start, tmp_end)
            length = tmp_end - tmp_start
            if length > max_length:
                max_length = length
                acc_start = df['start'][tup[0]]
                acc_end = df['start'][tup[1]]
    return (acc_start, acc_end)

def get_screen_bouts(df):
    """ Get the bouts of screen activity.

        Args:
            df: the dataframe holding screen state data
        Returns:
            The screen state start / end
    """
    if not df.empty:
        tmp = df[df['value'] == 0].sort_values(by='dt').dropna()
        ss_start = tmp.iloc[-1]['start']
        ss_end = tmp.iloc[-1]['timestamp']
        return (ss_start, ss_end)
    return (0, 0)

def max_intersection(acc_start, acc_end, ss_start, ss_end):
    """ Helper function to get the maximum overlap of the accelerometer
        and screen state inactive periods.
    """
    intersection = min(acc_end, ss_end) - max(acc_start, ss_start)
    if intersection >= 0:
        return intersection
    return None
