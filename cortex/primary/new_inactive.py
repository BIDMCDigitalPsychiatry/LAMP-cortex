import numpy as np
import pandas as pd

from ..feature_types import primary_feature
from ..raw.accelerometer import accelerometer
from ..raw.screen_state import screen_state


@primary_feature(
    name="cortex.new_inactive",
    dependencies=[accelerometer, screen_state]
)
def new_inactive(jerk_threshold=500,**kwargs):
    _acc = accelerometer(**kwargs)['data']
    _ss = screen_state(**kwargs)['data']
    if _acc:
        acc_df = pd.DataFrame(_acc)[['x', 'y', 'z', 'timestamp']]
        acc_df = acc_jerk(acc_df)
        acc_start, acc_end = get_nonzero(acc_df)
    else:
        _ret = []
    
    if ss:
        ss = pd.DataFrame(ss)[['timestamp', 'value']]
        ss = ss.ss['dt'] = ss['timestamp'] - ss['timestamp'].shift()
        ss['prev_state'] = ss['value'].shift()
    else:
        _ret = []
        
    return _ret

def acc_jerk(acc_df, threshold=500):
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
        #_ret = list(acc_df[['start', 'end', 'acc_jerk']].T.to_dict().values())
        return acc_df
    
    else:
        return []

def get_nonzero(df, THRESHOLD=3.0, state=False, inclusive=True):
    '''    
    Returns: list of intervals of non-zero jerk
    '''
    df['above_threshold'] = df['acc_jerk'] > THRESHOLD
    arr = np.array(df['above_threshold'])
    arr_ext = np.r_[False, arr==state, False]
    idx = np.flatnonzero(arr_ext[:-1] != arr_ext[1:])
    
    idx_list = list(zip(idx[:-1:2], idx[1::2] - int(inclusive)))
    max_length = 1
    acc_start = 0 
    acc_end = 0 
    for tup in idx_list:
        interval = (df['start'][tup[0]], df['start'][tup[1]])
        length = df['start'][tup[1]] - df['start'][tup[0]]
        if length > max_length:
            max_length = length
            acc_start = df['start'][tup[0]]
            acc_end = df['start'][tup[1]]
    return (acc_start, acc_end)

