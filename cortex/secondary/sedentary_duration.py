from ..feature_types import secondary_feature, log
from ..raw.accelerometer import accelerometer

import numpy as np
import pandas as pd
import datetime 

import LAMP 

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.sedentary_duration',
    dependencies=[accelerometer]
)
def sedentary_duration(resolution=MS_IN_A_DAY, **kwargs):
    """
    Generate sleep periods with given data
    """
    def _expected_sleep_period(accelerometer_data_reduced):

        df = pd.DataFrame.from_dict(accelerometer_data_reduced)

        # Creating possible times for expected sleep period, which will be checkede
        times = [(datetime.time(hour=h, minute=m), (datetime.datetime.combine(datetime.date.today(), datetime.time(hour=h, minute=m)) + datetime.timedelta(hours=8, minutes=0)).time()) for h in range(18, 24)  for m in [0, 30] ] + [(datetime.time(hour=h, minute=m), (datetime.datetime.combine(datetime.date.today(), datetime.time(hour=h, minute=m)) + datetime.timedelta(hours=8, minutes=0)).time()) for h in range(0, 4) for m in [0, 30]]

        mean_activity = float('inf')
        for t0, t1 in times:
            if datetime.time(hour=18, minute=0) <= t0 <= datetime.time(hour=23, minute=30):
                selection = pd.concat([df.loc[t0 <= df.time, :], df.loc[df.time <= t1, :]])

            else:
                selection = df.loc[(t0 <= df.time) & (df.time <= t1), :]

            if len(selection) == 0 or selection['count'].sum() == 0: 
                continue
                
            nonnan_ind = np.where(np.logical_not(np.isnan(selection['magnitude'])))[0]
            nonnan_sel = selection.iloc[nonnan_ind]
            #sel_act = np.average(selection['magnitude'][nonnan_ind], weights=selection['count'][nonnan_ind])
            sel_act = np.average(nonnan_sel['magnitude'], weights=nonnan_sel['count'])
            if sel_act < mean_activity:
                mean_activity = sel_act
                _sleep_period_expected = {'bed': t0, 'wake': t1, 'accelerometer_magnitude': sel_act} 

        if mean_activity == float('inf'):
            _sleep_period_expected = {'bed': None, 'wake': None, 'accelerometer_magnitude': None}

        return _sleep_period_expected

    # Data reduction
    try:
        reduced_data = LAMP.Type.get_attachment(kwargs['id'], 'cortex.sleep_periods.reduced')['data']
        for i, x in enumerate(reduced_data['data']):
            reduced_data['data'][i]['time'] = datetime.time(x['time']['hour'],
                                                            x['time']['minute'])
        log.info("Using saved reduced data...")
    except Exception:
        reduced_data = {'end':0, 'data':[]}
        log.info("No saved reduced data found, starting new...")


    reduced_data_end = reduced_data['end']
    
    if reduced_data_end < kwargs['end']:  # update reduced data

        # Accel binning
        _accelerometer = accelerometer(**{**kwargs, 'start': reduced_data_end})['data']
        if len(_accelerometer) > 0:
            reduceDf = pd.DataFrame.from_dict(_accelerometer)
            reduceDf.loc[:, 'Time'] = pd.to_datetime(reduceDf['timestamp'], unit='ms')
            reduceDf.loc[:, 'magnitude'] = reduceDf.apply(lambda row: np.linalg.norm([row['x'],
                                                                                      row['y'],
                                                                                      row['z']]), axis=1)

            # Get mean accel readings of 10min bins for participant
            new_reduced_data = []
            for s, t in reduceDf.groupby(pd.Grouper(key='Time', freq='10min')):
                res_10min = {'time': s.time(), 'magnitude': t['magnitude'].abs().mean(), 'count': len(t)}
                # Update new reduced data
                found = False
                for accel_bin in reduced_data['data']:
                    if accel_bin['time'] == res_10min['time']:
                        accel_bin['magnitude'] = np.mean([accel_bin['magnitude']] * accel_bin['count'] +
                                                         [res_10min['magnitude']] * res_10min['count'])
                        accel_bin['count'] = accel_bin['count'] + res_10min['count']
                        new_reduced_data.append(accel_bin)
                        found = True
                        break

                if not found:  # if time not found, initialize it
                    new_reduced_data.append(res_10min)

            # convert to time dicts for saving
            save_reduced_data = []
            for x in new_reduced_data:
                if x['magnitude'] and x['count']:
                    save_reduced_data.append({'time': {'hour': x['time'].hour,
                                                       'minute': x['time'].minute},
                                               'magnitude': x['magnitude'],
                                               'count': x['count']})
                    
            reduced_data = {'end': kwargs['end'], 'data': new_reduced_data}

            # set attachment
            LAMP.Type.set_attachment(kwargs['id'], 'me',
                                     attachment_key='cortex.sleep_periods.reduced',
                                     body={'end': kwargs['end'],
                                           'data': save_reduced_data})
            log.info("Saving reduced data...")


    accelerometer_data = accelerometer(**kwargs)['data']
    if len(accelerometer_data) == 0: 
        return {'timestamp':kwargs['start'], 'sedentary_duration':None}
    
    # Calculate sleep periods 
    _sleep_period_expected = _expected_sleep_period(reduced_data['data'])
    
    if _sleep_period_expected['bed'] is None:
        {'timestamp':kwargs['start'], 'sedentary_duration':None}

    accelDf = pd.DataFrame.from_dict(accelerometer_data)
    accelDf.loc[:, 'Time'] = pd.to_datetime(accelDf['timestamp'], unit='ms')
    accelDf.loc[:, 'magnitude'] = accelDf.apply(lambda row: np.linalg.norm([row['x'],
                                                                            row['y'],
                                                                            row['z']]), axis=1)

    # Get mean accel readings of 10min bins for participant
    df10min = pd.DataFrame.from_dict(reduced_data['data']).sort_values(by='time')

    bed_time, wake_time = _sleep_period_expected['bed'], _sleep_period_expected['wake']
    inactivity_count = 0
    for t, df in accelDf.groupby(pd.Grouper(key='Time', freq='10min')):
        # Ignore block if can't map to mean value
        if len(df10min.loc[df10min['time'] == t, 'magnitude'].values) == 0:
            continue 
        
        if datetime.time(0, 0) <= bed_time <= datetime.time(4, 0):
            if t < bed_time or t > wake_time:
                if df['magnitude'].abs().mean() < df10min.loc[df10min['time'] == normal_time.time(), 'magnitude'].values[0]:
                    inactivity_count += 1
        elif datetime.time(18, 0) <= bed_time <= datetime.time(23, 30):
            if wake_time < t < bed_time:
                if df['magnitude'].abs().mean() < df10min.loc[df10min['time'] == normal_time.time(), 'magnitude'].values[0]:
                    inactivity_count += 1
        
    #Calculate activity duration
    _sedentary_duration = (1000*60*10) * inactivity_count # MS_IN_10_MIN * number_of_10min

    return {'timestamp':kwargs['start'], 'sedentary_duration':_sedentary_duration}
