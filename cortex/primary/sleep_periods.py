from ..feature_types import primary_feature
from ..raw.accelerometer import accelerometer

import numpy as np
import pandas as pd 
import math 
import datetime
from geopy import distance
from functools import reduce

@primary_feature(
    name="cortex.feature.sleep_periods",
    dependencies=[accelerometer]
)
def sleep_periods(**kwargs):
    """
    Generate sleep periods with given data
    """
    def expected_sleep_period(accelerometer_data):
        """
        Return the expected sleep period for a set of accelerometer data

        :param accelerometer_data (list)

        :return _sleep_period_expted (dict): list bed/wake timestamps and mean accel. magnitude for expected bedtime
        """
        #Find maximum bout of inactivity; that's mean sleep period 
        df = pd.DataFrame.from_dict(accelerometer_data)
        df.loc[:, 'Time'] = pd.to_datetime(df['timestamp'], unit='ms')
        times = [(datetime.time(hour=h, minute=m), (datetime.datetime.combine(datetime.date.today(), datetime.time(hour=h, minute=m)) + datetime.timedelta(hours=8, minutes=0)).time()) for h in range(18, 24)  for m in [0, 30] ] + [(datetime.time(hour=h, minute=m), (datetime.datetime.combine(datetime.date.today(), datetime.time(hour=h, minute=m)) + datetime.timedelta(hours=8, minutes=0)).time()) for h in range(0, 4) for m in [0, 30] ]
        mean_activity = float('inf')
        for t0, t1 in times:
            if datetime.time(hour=18, minute=0) <= t0 <= datetime.time(hour=23, minute=30):
                selection = pd.concat([df.loc[t0 <= df['Time'].dt.time, :], df.loc[df['Time'].dt.time <= t1, :]])
                
            else:
                selection = df.loc[(t0 <= df['Time'].dt.time) & (df['Time'].dt.time <= t1), :]

            sel_act = selection.apply(lambda row: np.linalg.norm([row['x'], row['y'], row['z']]), axis=1).abs().mean()
            if sel_act < mean_activity:
                mean_activity = sel_act
                _sleep_period_expected = {'bed':t0 ,'wake':t1, 'accelerometer_magnitude':sel_act} 
            
        if mean_activity == float('inf'):
            _sleep_period_expected = {'bed':None, 'wake':None, 'accelerometer_magnitude':None}
            
        return _sleep_period_expected


    ### ###
    accelerometer_data = accelerometer(**kwargs)
    _sleep_period_expected = expected_sleep_period(accelerometer_data)
    if _sleep_period_expected['bed'] == None:
        return []

    accelDf = pd.DataFrame.from_dict(accelerometer_data)
    accelDf.loc[:, 'Time'] = pd.to_datetime(accelDf['timestamp'], unit='ms')
    accelDf.loc[:, 'magnitude'] = accelDf.apply(lambda row: np.linalg.norm([row['x'], row['y'], row['z']]), axis=1)
    #Get mean accel readings of 10min bins for participant
    data_10min = []
    for s, t in accelDf.groupby(pd.Grouper(key='Time', freq='10min')):
        res_10min = {'time': s.time(), 'magnitude': t['magnitude'].abs().mean()}
        data_10min.append(res_10min)

    df10min = pd.DataFrame.from_dict(data_10min).sort_values(by='time')
    
    bed_time, wake_time = _sleep_period_expected['bed'], _sleep_period_expected['wake']
    
    #Calculate sleep
    sleepStart, sleepStartFlex = bed_time, (datetime.datetime.combine(datetime.date.today(), bed_time) - datetime.timedelta(hours=2)).time()
    sleepEnd, sleepEndFlex = wake_time, (datetime.datetime.combine(datetime.date.today(), wake_time) + datetime.timedelta(hours=2)).time() 

    #We need to shift times so that the day begins a midnight (and thus is on the same day) sleep start flex begins on 
    accelDf.loc[:, "Shifted Time"] = pd.to_datetime(accelDf['Time']) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)
    accelDf.loc[:, "Shifted Day"] = pd.to_datetime(accelDf['Shifted Time']).dt.date 
    #Also adjust bed/wake/flex times to account for shift
    
    sleepStartShifted = (datetime.datetime.combine(datetime.date.today(), sleepStart) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)).time()
    sleepStartFlexShifted = (datetime.datetime.combine(datetime.date.today(), sleepStartFlex) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)).time()
    sleepEndShifted = (datetime.datetime.combine(datetime.date.today(), sleepEnd) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)).time()
    sleepEndFlexShifted = (datetime.datetime.combine(datetime.date.today(), sleepEndFlex) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)).time()
    
    
    _sleep_periods = []
    for day, df in accelDf.groupby('Shifted Day'):
        
        #Keep track of how many 10min blocks are 1. inactive during "active" periods; or 2. active during "inactive periods"
        night_activity_count, night_inactivity_count, day_inactivity_count = 0, 0, 0
        for t, tDf in df.groupby(pd.Grouper(key='Shifted Time', freq='10min')):
            #Have normal time for querying the 10 min for that block (df10min)
            normal_time = t + (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)

            #Ignore block if can't map to mean value
            if len(df10min.loc[df10min['time'] == normal_time.time(), 'magnitude'].values) == 0:
                continue 
            
            day_sleep_period_start = None
            if (sleepStartFlexShifted <= t.time() < sleepStartShifted) or (sleepEndShifted <= t.time()):
                if tDf['magnitude'].abs().mean() < df10min.loc[df10min['time'] == normal_time.time(), 'magnitude'].values[0]: 
                    night_inactivity_count += 1
                    if day_sleep_period_start is None:
                        day_sleep_period_start = normal_time
                
            elif sleepStartShifted <= t.time() < sleepEndShifted:
                if tDf['magnitude'].abs().mean() > df10min.loc[df10min['time'] == normal_time.time(), 'magnitude'].values[0]: 
                    night_activity_count += 1

        #Calculate day's sleep duration using these activity account
        daily_sleep = (datetime.datetime.combine(datetime.date.today(), datetime.time(hour=8)) - datetime.timedelta(minutes = night_activity_count * 10) + datetime.timedelta(minutes = night_inactivity_count * 10)).time()
      
        #Set sleep start time 
        if day_sleep_period_start is None: continue
        if day_sleep_period_start.time() < datetime.time(hour=8): sleep_period_timestamp = datetime.datetime.combine(day + datetime.timedelta(days=1), day_sleep_period_start).timestamp() * 1000
        else: sleep_period_timestamp = datetime.datetime.combine(day, day_sleep_period_start.time()).timestamp() * 1000
        _sleep_period = {'start': sleep_period_timestamp, 'duration': daily_sleep}
        _sleep_periods.append(_sleep_period)

    return _sleep_periods
