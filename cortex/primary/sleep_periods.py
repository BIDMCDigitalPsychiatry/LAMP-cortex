from ..feature_types import primary_feature, log
from ..raw.accelerometer import accelerometer

import numpy as np
import pandas as pd 
import datetime
import LAMP


@primary_feature(
    name="cortex.feature.sleep_periods",
    dependencies=[accelerometer],
    attach=True
)
def sleep_periods(**kwargs):
    """
    Generate sleep periods with given data
    """
    def _expected_sleep_period(accelerometer_data_reduced):
        """
        Return the expected sleep period for a set of accelerometer data

        :param accelerometer_data (list)

        :return _sleep_period_expted (dict): list bed/wake timestamps and mean accel. magnitude for expected bedtime
        """
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
        return []
    
    # Calculate sleep periods 
    _sleep_period_expected = _expected_sleep_period(reduced_data['data'])
    
    if _sleep_period_expected['bed'] is None:
        return []

    accelDf = pd.DataFrame.from_dict(accelerometer_data)
    accelDf.loc[:, 'Time'] = pd.to_datetime(accelDf['timestamp'], unit='ms')
    accelDf.loc[:, 'magnitude'] = accelDf.apply(lambda row: np.linalg.norm([row['x'],
                                                                            row['y'],
                                                                            row['z']]), axis=1)

    # Get mean accel readings of 10min bins for participant
    df10min = pd.DataFrame.from_dict(reduced_data['data']).sort_values(by='time')

    bed_time, wake_time = _sleep_period_expected['bed'], _sleep_period_expected['wake']

    # Calculate sleep
    sleepStart, sleepStartFlex = bed_time, (datetime.datetime.combine(datetime.date.today(), bed_time) -
                                            datetime.timedelta(hours=2)).time()
    sleepEnd, sleepEndFlex = wake_time, (datetime.datetime.combine(datetime.date.today(), wake_time) +
                                         datetime.timedelta(hours=2)).time() 

    # We need to shift times so that the day begins a midnight (and thus is on the same day) sleep start flex begins on 
    accelDf.loc[:, "Shifted Time"] = pd.to_datetime(accelDf['Time']) - \
        (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)

    accelDf.loc[:, "Shifted Day"] = pd.to_datetime(accelDf['Shifted Time']).dt.date

    sleepStartShifted = (datetime.datetime.combine(datetime.date.today(), sleepStart) -
                         (datetime.datetime.combine(datetime.date.min, sleepEndFlex) -
                          datetime.datetime.min)).time()

    sleepStartFlexShifted = (datetime.datetime.combine(datetime.date.today(), sleepStartFlex) -
                             (datetime.datetime.combine(datetime.date.min, sleepEndFlex) -
                              datetime.datetime.min)).time()

    sleepEndShifted = (datetime.datetime.combine(datetime.date.today(), sleepEnd) -
                       (datetime.datetime.combine(datetime.date.min, sleepEndFlex) -
                        datetime.datetime.min)).time()

    _sleep_periods = []
    for day, df in accelDf.groupby('Shifted Day'):
        # Keep track of how many 10min blocks are 1. inactive during "active" periods; or 2. active during "inactive periods"
        night_activity_count, night_inactivity_count = 0, 0
        day_sleep_period_start = None
        for t, tDf in df.groupby(pd.Grouper(key='Shifted Time', freq='10min')):
            # Have normal time for querying the 10 min for that block (df10min)
            normal_time = t + (datetime.datetime.combine(datetime.date.min, sleepEndFlex) - datetime.datetime.min)
            # Ignore block if can't map to mean value
            if len(df10min.loc[df10min['time'] == normal_time.time(), 'magnitude'].values) == 0:
                continue 
                
            if (sleepStartFlexShifted <= t.time() < sleepStartShifted) or (sleepEndShifted <= t.time()):
                if tDf['magnitude'].abs().mean() < df10min.loc[df10min['time'] == normal_time.time(), 'magnitude'].values[0]: 
                    night_inactivity_count += 1
                    if day_sleep_period_start is None:
                        day_sleep_period_start = normal_time.time()

            elif sleepStartShifted <= t.time() < sleepEndShifted:
                if tDf['magnitude'].abs().mean() > df10min.loc[df10min['time'] == normal_time.time(), 'magnitude'].values[0]: 
                    night_activity_count += 1

        # Calculate day's sleep duration using these activity account
        daily_sleep = (datetime.datetime.combine(datetime.date.today(), datetime.time(hour=8)) - 
                       datetime.timedelta(minutes=night_activity_count * 10) + 
                       datetime.timedelta(minutes=night_inactivity_count * 10)).time()

        daily_sleep = daily_sleep.hour + daily_sleep.minute/60

        # Set sleep start time 
        if day_sleep_period_start is None: #if None, default to expected
            day_sleep_period_start = _sleep_period_expected['bed']
        if day_sleep_period_start < datetime.time(hour=8):
            sleep_period_timestamp = datetime.datetime.combine(day + datetime.timedelta(days=1),
                                                               day_sleep_period_start).timestamp() * 1000
        else:
            sleep_period_timestamp = datetime.datetime.combine(day, day_sleep_period_start).timestamp() * 1000

        _sleep_period = {'start': int(sleep_period_timestamp),
                         'end': int(sleep_period_timestamp + (daily_sleep * 3600000))} #MS_IN_AN_HOUR
        _sleep_periods.append(_sleep_period)

    return _sleep_periods
