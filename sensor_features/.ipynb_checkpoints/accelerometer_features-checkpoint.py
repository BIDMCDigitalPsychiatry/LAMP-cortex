import math 
import pandas as pd
import numpy as np
import datetime
from geopy import distance
from functools import reduce

def sleep_time_mean(sensor_data, dates):
    """
    Return mean expected bed and wake time
    """
    accelDf = convert_to_df(sensor_data)
    bed_raw, wake_raw, _ = get_optimal_inactivity(accelDf)
    bed, wake = pd.to_datetime(bed_raw, format= '%H:%M' ).time(), pd.to_datetime(wake_raw, format= '%H:%M' ).time()
    return bed, wake

def activities(sensor_data, dates):
    """
    Get percentage of sleep, active, and sedentary for the patient
    """
    TIME = dates[0].time()
    accelDf = convert_to_df(sensor_data)
    bed_time, wake_time = sleep_time_mean(sensor_data, dates)
    #Get mean accel readings of 10min bins for participant
    times, magnitudes = [], []
    accelDf.loc[:, 'Time'] = pd.to_datetime(accelDf["Time"].astype(str))
    for s, t in accelDf.groupby(pd.Grouper(key='Time', freq='10min')):
        times.append(s.time())
        magnitudes.append(t['magnitude'].abs().mean())

    df10min = pd.DataFrame({'Time':times, 'Magnitude':magnitudes}).sort_values(by='Time')
    
    #Calculate sleep
    sleepStart, sleepStartFlex = bed_time, (datetime.datetime.combine(datetime.date.today(), bed_time) - datetime.timedelta(hours=2)).time()
    sleepEnd, sleepEndFlex = wake_time, (datetime.datetime.combine(datetime.date.today(), wake_time) + datetime.timedelta(hours=2)).time() 

    #We need to shift times so that the day begins a midnight (and thus is on the same day) sleep start flex begins on 
    accelDf.loc[:, "Shifted Time"] = pd.to_datetime(accelDf['UTC time']) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)
    accelDf.loc[:, "Shifted Day"] = pd.to_datetime(accelDf['Shifted Time']).dt.date 
    #Also adjust bed/wake/flex times to account for shift
    
    sleepStartShifted = (datetime.datetime.combine(datetime.date.today(), sleepStart) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)).time()
    sleepStartFlexShifted = (datetime.datetime.combine(datetime.date.today(), sleepStartFlex) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)).time()
    sleepEndShifted = (datetime.datetime.combine(datetime.date.today(), sleepEnd) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)).time()
    sleepEndFlexShifted = (datetime.datetime.combine(datetime.date.today(), sleepEndFlex) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)).time()
    
    
    daily_activity_data = []
    for day, df in accelDf.groupby('Shifted Day'):
        
        #Keep track of how many 10min blocks are 1. inactive during "active" periods; or 2. active during "inactive periods"
        night_activity_count, night_inactivity_count, day_inactivity_count = 0, 0, 0
        #for t, tDf in df.groupby(pd.Grouper(key='UTC time', freq='10min')):
        for t, tDf in df.groupby(pd.Grouper(key='Shifted Time', freq='10min')):
            if (sleepStartFlexShifted <= t.time() < sleepStartShifted) or (sleepEndShifted <= t.time()):
            #if t - sleepStart
                if tDf['magnitude'].abs().mean() < df10min.loc[df10min['Time'] == t.time(), 'Magnitude'].values[0]: 
                    night_inactivity_count += 1
                    
            elif sleepStartShifted <= t.time() < sleepEndShifted:
                if tDf['magnitude'].abs().mean() > df10min.loc[df10min['Time'] == t.time(), 'Magnitude'].values[0]: 
                    night_activity_count += 1

            else: #if sleepEndFlex <= t.time() < sleepStartFlex:
                if tDf['magnitude'].abs().mean() < df10min.loc[df10min['Time'] == t.time(), 'Magnitude'].values[0]:
                    day_inactivity_count += 1

        #Calculate day's sleep using these activity account
        
        daily_sleep = (datetime.datetime.combine(datetime.date.today(), datetime.time(hour=8)) - datetime.timedelta(minutes = night_activity_count * 10) + datetime.timedelta(minutes = night_inactivity_count * 10)).time()
        daily_sedentary = datetime.time(hour = int(day_inactivity_count * 10 / 60), 
                                        minute = (day_inactivity_count * 10) % 60)
        
        #Label rest of the day as being active
        h1, m1, s1 = daily_sleep.hour, daily_sleep.minute, daily_sleep.second
        h2, m2, s2 = daily_sedentary.hour, daily_sedentary.minute, daily_sedentary.second
        t1_secs, t2_secs = s1 + 60 * (m1 + 60 * h1), s2 + 60 * (m2 + 60 * h2) 

        SECS_IN_A_DAY = 86400
        t3_secs = SECS_IN_A_DAY - (t1_secs + t2_secs)
        #print(t3_secs)
        daily_active = datetime.time(hour = int(t3_secs / 3600),
                                     minute = int((t3_secs % 3600) / 60),
                                     second = (t3_secs % 3600) % 60)
        
        daily_activity_data.append([datetime.datetime.combine(day, TIME), daily_sleep, daily_sedentary, daily_active])

    return pd.DataFrame(daily_activity_data, columns = ["Date", "Sleep Duration", "Sedentary Duration", "Active Duration"])

def convert_to_df(sensor_data):
    """
    Turn sensor data dict into df
    """
    sensorDf = sensor_data['lamp.accelerometer'].copy()
    
    # pd.DataFrame(data=[[r[0], r[1]['x'], r[1]['y'], r[1]['z']] for r in sensor_data["lamp.accelerometer"]], 
    #                         columns = ['timestamp', 'x', 'y', 'z']).drop_duplicates()
    
        
    sensorDf['UTC time'] = [str(d.date()) + "T" + str(d.time()) for d in sensorDf['local_datetime']]
    
    sensorDf['Day'] = sensorDf.apply(lambda row: row['UTC time'].split('T')[0], axis=1)
    sensorDf['Time'] = sensorDf.apply(lambda row: row['UTC time'].split('T')[1], axis=1)
    sensorDf['Time'] = pd.to_datetime(sensorDf['Time']).dt.time
    sensorDf['magnitude'] = sensorDf.apply(lambda row: np.linalg.norm([row['x'], row['y'], row['z']]), axis=1)
    sensorDf.loc[:, 'magnitude'] = sensorDf.loc[:, 'magnitude'] - 1 
    
    return sensorDf

def get_optimal_inactivity(df, length=8):
    #Find maximum bout of inactivity
    times = [(datetime.time(hour=h, minute=m).strftime("%H:%M"), (datetime.datetime.combine(datetime.date.today(), datetime.time(hour=h, minute=m)) + datetime.timedelta(hours=8, minutes=0)).strftime("%H:%M")) for h in range(18, 24)  for m in [0, 30] ] + [(datetime.time(hour=h, minute=m).strftime("%H:%M"), (datetime.datetime.combine(datetime.date.today(), datetime.time(hour=h, minute=m)) + datetime.timedelta(hours=8, minutes=0)).strftime("%H:%M")) for h in range(0, 4) for m in [0, 30] ]
    mean_activity = float('inf')
    for t0, t1 in times:
        if "18:00" <= t0 <= "23:00":
            selection = pd.concat([df.loc[datetime.datetime.strptime(t0, "%H:%M").time() <= df['Time'], :], df.loc[df['Time'] <= datetime.datetime.strptime(t1, "%H:%M").time(), :]])
        else:
            selection = df.loc[(datetime.datetime.strptime(t0, "%H:%M").time() <= df['Time']) & (df['Time'] <= datetime.datetime.strptime(t1, "%H:%M").time()), :]

        sel_act = selection['magnitude'].abs().mean()

        if sel_act < mean_activity:
            mean_activity = sel_act
            period = (t0, t1, sel_act)
         
    if mean_activity == float('inf'):
        return None
    return period
    
def all(sensor_data, dates, resolution):
    if 'lamp.accelerometer' not in sensor_data:
        return pd.DataFrame({'Date': dates})

    df_list = []
    if resolution == datetime.timedelta(days=1):
        activeDf = activities(sensor_data, dates)
        df_list.append(activeDf)

    allDfs = reduce(lambda left, right: pd.merge(left, right, on=["Date"], how='left'), df_list)
    return allDfs

if __name__ == "__main__":
    pass