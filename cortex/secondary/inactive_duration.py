""" Module to compute the longest inactive bout from accelerometer and screen state """
import numpy as np
import pandas as pd

from ..feature_types import secondary_feature
from ..raw.accelerometer import accelerometer
from ..raw.screen_state import screen_state


@secondary_feature(
    name="cortex.feature.inactive_duration",
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
        _ss = pd.DataFrame(_ss)
        if 'state' in _ss and 'value' not in _ss:
            _ss = _ss.rename(columns={"state": "value"})
        _ss = _ss[['timestamp', 'value']]
        _ss = _ss.iloc[::-1].reset_index(drop=True)
        _ss['start'] = _ss.timestamp.shift()
        _ss['prev_state'] = _ss.value.shift()
        _ss['dt'] = _ss.timestamp - _ss.start
        ss_tups = get_screen_bouts(_ss)

    else:
        return {'timestamp': kwargs['start'], 'value': None}

    _acc = accelerometer(**kwargs)['data']
    if _acc:
        acc_df = pd.DataFrame(_acc)[['x', 'y', 'z', 'timestamp']]
        acc_df = acc_df.iloc[::-1]
        acc_df = acc_jerk(acc_df, jerk_threshold)
        acc_tups = get_acc_bouts(acc_df)
    else:
        return {'timestamp': kwargs['start'], 'value': None}

    if ss_tups is None or acc_tups is None or len(ss_tups) == 0 or len(acc_tups) == 0:
        return {'timestamp': kwargs['start'], 'value': None}
    ss_max_index = get_max_index(ss_tups)
    ss_start, ss_end = get_max_bout(ss_tups, ss_max_index)
    acc_max_index = get_max_index(acc_tups)
    acc_start, acc_end = acc_tups[acc_max_index]
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
    return []

def max_intersection(acc_start, acc_end, ss_start, ss_end):
    """ Helper function to get the maximum overlap of the accelerometer
        and screen state inactive periods.
    """
    intersection = min(acc_end, ss_end) - max(acc_start, ss_start)
    if intersection >= 0:
        return intersection
    return None

def get_max_bout(tup_list, start_idx, gap_threshold=10*1000):
    """ Helper function to get the maximum bout.

        Args:
            tup_list: the list of tuples
            start_idx: the starting index
            gap_threshold (int, ms, default: 10s): the time threshold to merge bouts
        Returns:
            the start of the bout
    """
    bout_start = get_bout_start(tup_list, start_idx, gap_threshold)
    bout_end = get_bout_end(tup_list, start_idx, gap_threshold)
    return (bout_start, bout_end)

def get_bout_start(tup_list, start_idx, gap_threshold):
    """ Helper function to find the start of the bout.

        Args:
            tup_list: the list of tuples
            start_idx: the starting index
            gap_threshold: the time threshold to merge bouts
        Returns:
            the start of the bout
    """
    n = len(tup_list)
    bout_start = tup_list[start_idx][0]
    while start_idx != 0:
        curr_start = tup_list[start_idx][0]
        left_end = tup_list[start_idx - 1][1]
        if curr_start - left_end <= gap_threshold:
            bout_start = tup_list[start_idx - 1][0]
            start_idx -= 1
        else:
            break
    return bout_start

def get_bout_end(tup_list, start_idx, gap_threshold):
    """ Helper function to find the end of the bout.

        Args:
            tup_list: the list of tuples
            start_idx: the starting index
            gap_threshold: the time threshold to merge bouts
        Returns:
            the end of the bout
    """
    n = len(tup_list)
    bout_end = tup_list[start_idx][1]
    while start_idx != n - 1:
        curr_end = tup_list[start_idx][1]
        right_start = tup_list[start_idx + 1][0]
        if right_start - curr_end <= gap_threshold:
            bout_end = tup_list[start_idx + 1][1]
            start_idx += 1
        else:
            break
    return bout_end


def get_screen_bouts(df):
    """ Get the bouts of screen inactivity.

        Args:
            df: the dataframe holding screen state data
        Returns:
            List of tuples (start, end) of inactive periods based on Screen State
    """
    if not df.empty:
        tmp = df[df['value'] == 0].dropna()
        if not tmp.empty:
            ss_tups = [tuple(x) for x in tmp[['start', 'timestamp']].values]
            return ss_tups
    return None

def get_acc_bouts(df, jerk_threshold=0.5):
    """ Get the bouts of non-zero jerk.

        Args:
            df: the dataframe holding accelerometer jerk data
        Returns:
            List of tuples (start, end) of inactive periods based on acc_jerk
    """
    df['above_threshold'] = df['acc_jerk'] > jerk_threshold
    df['prev_above'] = df['above_threshold'].shift()
    df = df[df['above_threshold'] == False]
    df = df[df['prev_above'] == True]
    if not df.empty:
        df['end'] = df['start'].shift()
        df = df.dropna()
        tuples = [tuple(x) for x in df[['end', 'start']].values]
        return tuples
    return None 

def get_max_index(tup_list):
    """ Helper function to get the max index of the tuple list.
    """
    return tup_list.index(max(tup_list, key=lambda x: x[1] - x[0]))
