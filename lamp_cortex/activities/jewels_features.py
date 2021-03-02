import datetime
import pandas as pd
import numpy as np
from functools import reduce
import LAMP
    

def jewels_featurize(results, times, resolution, key):
    assert key in ['lamp.jewels_a', 'lamp.jewels_b']

    if key not in results:
        return pd.DataFrame({'Date':times})

    JEWELS_FEATURES = ['duration', 'point', 'score', 'total_attempts', 'total_bonus_collected', 'total_jewels_collected']
    traildat = results[key]
    stat = pd.DataFrame(traildat.static_data.tolist())
    sel_jewels_data = traildat.join(stat)

    column_labels = traildat.static_data.tolist()

    timesSeries = pd.Series(times)
    time_sel_jewels = sel_jewels_data.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)
    
    sel_jewels_data.loc[:, 'matched_time'] = time_sel_jewels 

    #For each window, calculate entropy
    jewels_data = []
    for t in times:
        t_jewels = sel_jewels_data.loc[sel_jewels_data['matched_time'] == t, :].reset_index().sort_values(by='local_datetime')
        t_data = [t] + t_jewels[JEWELS_FEATURES].mean().tolist() + [t_jewels.static_data.values]
        jewels_data.append(t_data)

    jewelsDf = pd.DataFrame(jewels_data, columns=['Date'] + ['.'.join([key, f]) for f in JEWELS_FEATURES + ['static_data']])
    return jewelsDf


def tempfunc(results, date_list, resolution):
    jewels_a, jewels_b = jewels_featurize(results, date_list, resolution=resolution, key='lamp.jewels_a'), jewels_featurize(results, date_list, resolution=resolution, key='lamp.jewels_b')
    df_list = [jewels_a, jewels_b]
    allDfs = reduce(lambda left, right: pd.merge(left, right, on=["Date"], how='left'), df_list)
    
    return allDfs


    
    
