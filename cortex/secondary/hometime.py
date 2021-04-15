from ..feature_types import secondary_feature
from ..primary.significant_locations import significant_locations

import math
import datetime
import pandas as pd

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.entropy',
    dependencies=[significant_locations]
)
def entropy(resolution=MS_IN_A_DAY, **kwargs):
    """
    Calculate entropy 
    """
    _significant_locations = significant_locations(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    if len(_significant_locations['data']) == 0:
        _entropy = None
    _entropy = sum([loc['proportion'] * math.log(loc['proportion']) for loc in _significant_locations['data']])
    if _entropy == 0: #no sig locs
        _entropy = None
    return {'timetamp':kwargs['start'], 'entropy': _entropy}


@secondary_feature(
    name='cortex.feature.hometime',
    dependencies[significant_locations]
)
def hometime():
    _significant_locations = significant_locations(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    if len(_significant_locations['data']) == 0:
        _hometime = None
    _hometime = sum([loc['proportion'] * math.log(loc['proportion']) for loc in _significant_locations['data']])
    if _entropy == 0: #no sig locs
        _entropy = None
    return {'timetamp':kwargs['start'], 'entropy': _entropy}

def hometime(df, dates, resolution, k_max=10):
    _, df_sig_locs  = significant_locs(df, k_max=k_max)
    
    #Map each gps read with corresponding time window
    timesSeries = pd.Series(dates)
    time_sel_gps = df_sig_locs.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)
    
    df_sig_locs.loc[:, 'matched_time'] = time_sel_gps

    hometime_df_data = []
    #For each window, calculate entropy
    for t in dates:
        gps_readings = df_sig_locs.loc[(df_sig_locs['matched_time'] == t) & (df_sig_locs['cluster_label']), :].reset_index()
        hometime_total = datetime.timedelta()
        for idx, row in gps_readings.iterrows():            
            if idx == len(gps_readings) - 1: #If on last readings
                elapsed_time = (t + resolution) - gps_readings.loc[gps_readings.index[idx], 'local_datetime']
                if elapsed_time > datetime.timedelta(hours=1):
                    elapsed_time = datetime.timedelta(hours=1)
                
            else:
                elapsed_time = gps_readings.loc[gps_readings.index[idx + 1], 'local_datetime'] - gps_readings.loc[gps_readings.index[idx], 'local_datetime']
                if elapsed_time > datetime.timedelta(hours=1):
                    elapsed_time = datetime.timedelta(hours=1)

            hometime_total += elapsed_time

        if hometime_total == datetime.timedelta():
            hometime_total = np.nan

        hometime_df_data.append([t, hometime_total])

    hometimeDf = pd.DataFrame(hometime_df_data, columns=['Date', 'Hometime'])
    return hometimeDf