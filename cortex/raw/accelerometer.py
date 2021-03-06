from ..feature_types import raw_feature, log
import LAMP


@raw_feature(
    name="lamp.accelerometer",
    dependencies=["lamp.accelerometer"]
)
def accelerometer(resolution=None, limit=20000, **kwargs):
    """
    Get all GPS data bounded by time interval and optionally subsample the data.

    :param resolution (int): The subsampling resolution (TODO).
    :param limit (int): The maximum number of sensor events to query for (defaults to INT_MAX).
    :return timestamp (int): The UTC timestamp for the GPS event.
    :return latitude (float): The latitude for the GPS event.
    :return longitude (float): The longitude for the GPS event.
    :return altitude (float): The altitude for the GPS event.
    :return accuracy (float): The accuracy (in meters) for the GPS event.
    """

    data = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                               origin="lamp.accelerometer",
                                               _from=kwargs['start'],
                                               to=kwargs['end'],
                                               _limit=limit)['data']
    while data:
        to = data[-1]['timestamp']
        data_next = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                                        origin="lamp.accelerometer",
                                                        _from=kwargs['start'],
                                                        to=to,
                                                        _limit=limit)['data']
        if not data_next: break
        if data_next[-1]['timestamp'] == to: break
        data += data_next
    return [{'timestamp': x['timestamp'], **x['data']} for x in data]

# def sleep_time_mean(sensor_data, dates):
#     """
#     Return mean expected bed and wake time
#     """
#     accelDf = convert_to_df(sensor_data)
#     bed_raw, wake_raw, _ = get_optimal_inactivity(accelDf)
#     if (bed_raw, wake_raw) == (None, None):
#         return (None, None)
#     bed, wake = pd.to_datetime(bed_raw, format= '%H:%M' ).time(), pd.to_datetime(wake_raw, format= '%H:%M' ).time()
#     return bed, wake

# def activities(sensor_data, dates):
#     """
#     Get percentage of sleep, active, and sedentary for the patient
#     """
#     TIME = dates[0].time()
#     accelDf = convert_to_df(sensor_data)
#     bed_time, wake_time = sleep_time_mean(sensor_data, dates)
#     if (bed_time, wake_time) == (None, None):
#         return pd.DataFrame({"Date": dates,
#                              "Sleep Duration": [None] * len(dates),
#                              "Sedentary Duration": [None] * len(dates), 
#                              "Activity Duration": [None] * len(dates)})

#     #Get mean accel readings of 10min bins for participant
#     times, magnitudes = [], []
#     accelDf.loc[:, 'Time'] = pd.to_datetime(accelDf["Time"].astype(str))
#     for s, t in accelDf.groupby(pd.Grouper(key='Time', freq='10min')):
#         times.append(s.time())
#         magnitudes.append(t['magnitude'].abs().mean())

#     df10min = pd.DataFrame({'Time':times, 'Magnitude':magnitudes}).sort_values(by='Time')
    
#     #Calculate sleep
#     sleepStart, sleepStartFlex = bed_time, (datetime.datetime.combine(datetime.date.today(), bed_time) - datetime.timedelta(hours=2)).time()
#     sleepEnd, sleepEndFlex = wake_time, (datetime.datetime.combine(datetime.date.today(), wake_time) + datetime.timedelta(hours=2)).time() 

#     #We need to shift times so that the day begins a midnight (and thus is on the same day) sleep start flex begins on 
#     accelDf.loc[:, "Shifted Time"] = pd.to_datetime(accelDf['UTC time']) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)
#     accelDf.loc[:, "Shifted Day"] = pd.to_datetime(accelDf['Shifted Time']).dt.date 
#     #Also adjust bed/wake/flex times to account for shift
    
#     sleepStartShifted = (datetime.datetime.combine(datetime.date.today(), sleepStart) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)).time()
#     sleepStartFlexShifted = (datetime.datetime.combine(datetime.date.today(), sleepStartFlex) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)).time()
#     sleepEndShifted = (datetime.datetime.combine(datetime.date.today(), sleepEnd) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)).time()
#     sleepEndFlexShifted = (datetime.datetime.combine(datetime.date.today(), sleepEndFlex) - (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)).time()
    
    
#     daily_activity_data = []
#     for day, df in accelDf.groupby('Shifted Day'):
        
#         #Keep track of how many 10min blocks are 1. inactive during "active" periods; or 2. active during "inactive periods"
#         night_activity_count, night_inactivity_count, day_inactivity_count = 0, 0, 0
#         for t, tDf in df.groupby(pd.Grouper(key='Shifted Time', freq='10min')):
#             #Have normal time for querying the 10 min for that block (df10min)
#             normal_time = t + (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)

#             #Ignore block if can't map to mean value
#             if len(df10min.loc[df10min['Time'] == normal_time.time(), 'Magnitude'].values) == 0:
#                 continue 
             
#             if (sleepStartFlexShifted <= t.time() < sleepStartShifted) or (sleepEndShifted <= t.time()):
#                 if tDf['magnitude'].abs().mean() < df10min.loc[df10min['Time'] == normal_time.time(), 'Magnitude'].values[0]: 
#                     night_inactivity_count += 1
                    
#             elif sleepStartShifted <= t.time() < sleepEndShifted:
#                 if tDf['magnitude'].abs().mean() > df10min.loc[df10min['Time'] == normal_time.time(), 'Magnitude'].values[0]: 
#                     night_activity_count += 1

#             else: 
#                 if tDf['magnitude'].abs().mean() < df10min.loc[df10min['Time'] == normal_time.time(), 'Magnitude'].values[0]:
#                     day_inactivity_count += 1

#         #Calculate day's sleep using these activity account
        
#         daily_sleep = (datetime.datetime.combine(datetime.date.today(), datetime.time(hour=8)) - datetime.timedelta(minutes = night_activity_count * 10) + datetime.timedelta(minutes = night_inactivity_count * 10)).time()
#         daily_sedentary = datetime.time(hour = int(day_inactivity_count * 10 / 60), 
#                                         minute = (day_inactivity_count * 10) % 60)
        
#         #Label rest of the day as being active
#         h1, m1, s1 = daily_sleep.hour, daily_sleep.minute, daily_sleep.second
#         h2, m2, s2 = daily_sedentary.hour, daily_sedentary.minute, daily_sedentary.second
#         t1_secs, t2_secs = s1 + 60 * (m1 + 60 * h1), s2 + 60 * (m2 + 60 * h2) 

#         SECS_IN_A_DAY = 86400
#         t3_secs = SECS_IN_A_DAY - (t1_secs + t2_secs)
#         #print(t3_secs)
#         daily_active = datetime.time(hour = int(t3_secs / 3600),
#                                      minute = int((t3_secs % 3600) / 60),
#                                      second = (t3_secs % 3600) % 60)
        
#         daily_activity_data.append([datetime.datetime.combine(day, TIME), daily_sleep, daily_sedentary, daily_active])

#     return pd.DataFrame(daily_activity_data, columns = ["Date", "Sleep Duration", "Sedentary Duration", "Active Duration"])

# def convert_to_df(sensor_data):
#     """
#     Turn sensor data dict into df
#     """
#     sensorDf = sensor_data['lamp.accelerometer'].copy()
        
#     sensorDf['UTC time'] = [str(d.date()) + "T" + str(d.time()) for d in sensorDf['local_datetime']]
#     sensorDf['Day'] = sensorDf.apply(lambda row: row['UTC time'].split('T')[0], axis=1)
#     sensorDf['Time'] = sensorDf.apply(lambda row: row['UTC time'].split('T')[1], axis=1)
#     sensorDf['Time'] = pd.to_datetime(sensorDf['Time']).dt.time
#     sensorDf['magnitude'] = sensorDf.apply(lambda row: np.linalg.norm([row['x'], row['y'], row['z']]), axis=1)
#     sensorDf.loc[:, 'magnitude'] = sensorDf.loc[:, 'magnitude'] - 1 
    
#     return sensorDf

# def get_optimal_inactivity(df, length=8):
#     #Find maximum bout of inactivity
#     times = [(datetime.time(hour=h, minute=m).strftime("%H:%M"), (datetime.datetime.combine(datetime.date.today(), datetime.time(hour=h, minute=m)) + datetime.timedelta(hours=8, minutes=0)).strftime("%H:%M")) for h in range(18, 24)  for m in [0, 30] ] + [(datetime.time(hour=h, minute=m).strftime("%H:%M"), (datetime.datetime.combine(datetime.date.today(), datetime.time(hour=h, minute=m)) + datetime.timedelta(hours=8, minutes=0)).strftime("%H:%M")) for h in range(0, 4) for m in [0, 30] ]
#     mean_activity = float('inf')
#     for t0, t1 in times:
#         if "18:00" <= t0 <= "23:00":
#             selection = pd.concat([df.loc[datetime.datetime.strptime(t0, "%H:%M").time() <= df['Time'], :], df.loc[df['Time'] <= datetime.datetime.strptime(t1, "%H:%M").time(), :]])
#         else:
#             selection = df.loc[(datetime.datetime.strptime(t0, "%H:%M").time() <= df['Time']) & (df['Time'] <= datetime.datetime.strptime(t1, "%H:%M").time()), :]

#         sel_act = selection['magnitude'].abs().mean()

#         if sel_act < mean_activity:
#             mean_activity = sel_act
#             period = (t0, t1, sel_act)
         
#     if mean_activity == float('inf'):
#         return None, None, None
#         #Default to midnight to 7am return ("00:00", "07:00", df['magnitude'].abs().mean())
        
#     return period
    
# def all(sensor_data, dates, resolution):
#     if 'lamp.accelerometer' not in sensor_data:
#         return pd.DataFrame({'Date': dates})

#     df_list = []
#     if resolution == datetime.timedelta(days=1):
#         activeDf = activities(sensor_data, dates)
#         df_list.append(activeDf)

#     allDfs = reduce(lambda left, right: pd.merge(left, right, on=["Date"], how='left'), df_list)
#     return allDfs
