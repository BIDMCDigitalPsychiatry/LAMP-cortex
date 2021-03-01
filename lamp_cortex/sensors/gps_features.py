import math 
import pandas as pd
import numpy as np
import datetime
from geopy import distance
from sklearn.cluster import KMeans
from functools import reduce

def label_gps_points(sensor_data, gps_sensor):
    """
    Label gps readings as being either "stationary" (0) or "transitionary" (1)

    :param sensor_data (dict): maps LAMP sensor to sensor events
    
    :return (pd.DataFrame): columns ['local_timestamp', 'latitude', 'longitude', 'stationary'], where 'stationary' is bool indicating whether GPS point is stationary/nonstationary
    """
    assert gps_sensor in sensor_data

    SPEED_THRESHOLD = 1.0
    stationary = True #initial state is not moving (in case gps points are very close together)

    labeled_data = sensor_data[gps_sensor].copy()
    for (_, point1), (_, point2) in zip(sensor_data[gps_sensor].iterrows(), sensor_data[gps_sensor].shift(-1).iterrows()):
        #If last timestamp in df, carry over label from previous point
        if point1['local_timestamp'] == labeled_data.loc[labeled_data.index[-1], 'local_timestamp']:
            labeled_data.loc[labeled_data.index[-1], 'stationary'] = labeled_data.loc[labeled_data.index[-2], 'stationary']
            
        else:

            #if nan coordinates, keep stationary status and move on
            if None in [point1['latitude'], point1['longitude'], 
                          point2['latitude'], point2['longitude']]:
                pass
            elif np.isnan(point1['latitude']) or np.isnan(point1['longitude']) or np.isnan(point2['latitude']) or np.isnan(point2['longitude']):
                pass
            else:
                dist = distance.distance((point1['latitude'], point1['longitude']), (point2['latitude'], point2['longitude'])).km 
                elapsed_time = ((datetime.datetime.utcfromtimestamp(point2['local_timestamp'] / 1000) - datetime.datetime.utcfromtimestamp(point1['local_timestamp'] / 1000)).seconds / 3600)            
                #update stationary if points are separated temporally (elaped time non-zero)
                if elapsed_time > 0.0:
                    speed =  dist / ((datetime.datetime.utcfromtimestamp(point2['local_timestamp'] / 1000) - datetime.datetime.utcfromtimestamp(point1['local_timestamp'] / 1000)).seconds / 3600)
                    if speed >= SPEED_THRESHOLD: stationary = False
                    else: stationary = True

            labeled_data.loc[labeled_data['local_timestamp'] == point1['local_timestamp'], 'stationary'] = stationary

    return labeled_data

def get_total_distance(df, idx1, idx2):
    dist = 0
    for i in range(idx1 + 1, idx2 + 1):        
        c2 = (float(df.loc[df.index == i, 'latitude'].values[0]), float(df.loc[df.index == i, 'longitude'].values[0]))
        c1 = (float(df.loc[df.index == i - 1, 'latitude'].values[0]), float(df.loc[df.index == i - 1, 'longitude'].values[0]))
    
        if np.isnan(c1[0]) or np.isnan(c1[1]) or np.isnan(c2[0]) or np.isnan(c2[1]):
            continue
        dist += distance.distance(c1, c2).km
    return dist

def get_trips(df, state=False, inclusive=True):
    '''
    Input:
    df (Pandas Dataframe)
    state (bool)
    inclusive (bool)

    Returns: list of trips (tuples of start and end timestamps)
    '''
    
    df['local_timestamp'] = pd.to_datetime(df['local_timestamp'], unit='ms')
    arr = np.array(df['stationary'])
    arr_ext = np.r_[False, arr == state, False]
    idx = np.flatnonzero(arr_ext[:-1] != arr_ext[1:])
    idx_list = list(zip(idx[:-1:2], idx[1::2] - int(inclusive)))

    trip_list = []
    for tup in idx_list:
        dist = get_total_distance(df, tup[0], tup[1])
        trip = (df['local_timestamp'][tup[0]], df['local_timestamp'][tup[1]],dist)
        trip_list.append(trip)

    tripDf = pd.DataFrame(trip_list, columns=["Trip Start", "Trip End", "Distance"])
    return tripDf

def gen_trip_dict(interval_range):
    trip_dict = {}
    for i in range(len(interval_range)):
        trip_dict[interval_range[i]] = {'Trip Count': 0, 'Duration': 0, 'Distance Traveled': 0}
    return trip_dict

def get_trip_count(trip_dict, interval_range, l):
    for i in range(len(interval_range)):
        for j in range(len(l)):
            if l[j][0] >= interval_range[i].left and l[j][1] <= interval_range[i].right:
                trip_dict[interval_range[i]]['Trip Count'] += 1
    return trip_dict

def get_trip_features(trips, dates, freq=datetime.timedelta(days=1)):#interval_range, l):
    '''
    trip_dict values' units:
    Duration - Minutes
    Distance Traveled - Meters
    '''
    l = trips
    interval_range = dates

    trip_dict = gen_trip_dict(interval_range)

    #for i in range(len(interval_range)):
    for i in range(len(dates)):
        if i == len(dates) - 1:
            date, next_date = dates[i], dates[i] + freq
        else:
            date, next_date = dates[i], dates[i+1]
        for idx, trip in trips.iterrows():
            if date <= trip['Trip Start'] and next_date >= trip['Trip End']:
                trip_dict[date]['Trip Count'] += 1
                trip_duration = trip['Trip End'] - trip['Trip Start']
                trip_dict[date]['Duration'] = (trip_duration.days * 24) + (trip_duration.seconds / 60)
                trip_dict[date]['Distance Traveled'] = trip['Distance']

    tripDf = pd.DataFrame([[t, trip_dict[t]['Trip Count'], trip_dict[t]['Duration'], trip_dict[t]['Distance Traveled']] for t in trip_dict],
                          columns=['Date', 'Trip Count', 'Duration', 'Distance Traveled'])

    return tripDf

def significant_locs(df, k_max=10):
    """
    Get the coordinates of the significant locations

    :return centers ()
    :return df (pd.DataFrame): gps data with each readings labeled with a sig loc
    """
    K_clusters = range(1, min(k_max, len(df)))
    kmeans = [KMeans(n_clusters=i) for i in K_clusters]
    df_arr = df[['latitude', 'longitude']].values
    score = [kmeans[i].fit(df_arr).score(df_arr) for i in range(len(kmeans))]
    for i in range(len(score)):
        if i == len(score) - 1:
            k = i +1
            break
        
        elif abs(score[i + 1] - score[i] < .01):
            k = i + 1
            break

    kmeans = KMeans(n_clusters=k, init='k-means++')
    kmeans.fit(df_arr)  # Compute k-means clustering.
    df.loc[:, 'cluster_label'] = kmeans.fit_predict(df[['latitude', 'longitude']])
    centers = kmeans.cluster_centers_  # Coordinates of cluster centers.

    return centers, df

def significant_locations_visited(df, dates, resolution, k_max=10):
    centers, df_sig_locs  = significant_locs(df, k_max=k_max)
    
    #Map each gps read with corresponding time window
    timesSeries = pd.Series(dates)
    time_sel_gps = df_sig_locs.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)
    
    df_sig_locs.loc[:, 'matched_time'] = time_sel_gps

    sig_locs_visited_df_data = []
    #For each window, calculate entropy
    for t in dates:
        gps_readings = df_sig_locs.loc[df_sig_locs['matched_time'] == t, :].reset_index()
        
        if len(gps_readings) == 0:
            time_locs = []

        else:
            for idx, row in gps_readings.iterrows():            
                time_locs_labels = gps_readings['cluster_label'].unique()
                time_locs = [centers[l] for l in time_locs_labels]

        sig_locs_visited_df_data.append([t, time_locs])

    sigLocsDf = pd.DataFrame(sig_locs_visited_df_data, columns=['Date', 'Significant Locations'])
    return sigLocsDf


def entropy(df, dates, resolution, k_max=10):
    """
    """
    _, df_sig_locs  = significant_locs(df, k_max=k_max)
    
    #Map each gps read with corresponding time window
    timesSeries = pd.Series(dates)
    time_sel_gps = df_sig_locs.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)
    
    df_sig_locs.loc[:, 'matched_time'] = time_sel_gps

    ent_df_data = []
    #For each window, calculate entropy
    for t in dates: 
        cluster_dict = {cluster:[] for cluster in df_sig_locs['cluster_label'].unique()}
        gps_readings = df_sig_locs.loc[df_sig_locs['matched_time'] == t, :].reset_index().sort_values(by='local_datetime')
        for idx, row in gps_readings.iterrows():            
            if idx == len(gps_readings) - 1: #If on last readings
                elapsed_time = (t + resolution) - gps_readings.loc[gps_readings.index[idx], 'local_datetime']
                #print(elapsed_time)
                if elapsed_time > datetime.timedelta(hours=1):
                    elapsed_time = datetime.timedelta(hours=1)
        
            else:
                elapsed_time = gps_readings.loc[gps_readings.index[idx + 1], 'local_datetime'] - gps_readings.loc[gps_readings.index[idx], 'local_datetime']
        
                if elapsed_time > datetime.timedelta(hours=1):
                    elapsed_time = datetime.timedelta(hours=1)

            # BUG: producing some negative elapsed times
            if elapsed_time < datetime.timedelta():
                continue

            cluster = gps_readings.loc[gps_readings.index[idx], 'cluster_label']
            cluster_dict[cluster].append(elapsed_time)
        
        total_time_locations_all = pd.concat([pd.Series(cluster_dict[c]) for c in cluster_dict]).sum()
        if total_time_locations_all == 0.0:
            total_time_locations_all = datetime.timedelta()

        entropy = 0.0
        for c in cluster_dict:
            c_time = pd.Series(cluster_dict[c]).sum()
            if c_time == 0:
                continue

            pctg = c_time / total_time_locations_all
            if pctg == 0:
                continue 
            
            prod = pctg * math.log(pctg)
            entropy -= entropy 

        if entropy == 0.0: #then add nan
            entropy = np.nan 

        ent_df_data.append([t, entropy])

    entDf = pd.DataFrame(ent_df_data, columns=['Date', 'Entropy'])

    return entDf

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


def all(sensor_data, dates, resolution):
    #Check one of two gps sensors
    if "lamp.gps" in sensor_data and len(sensor_data['lamp.gps']) > 1:
        gps_sensor = "lamp.gps"

    else: #no gps sensor; return empty df
        return pd.DataFrame({'Date': dates})

    labeled_data = label_gps_points(sensor_data, gps_sensor=gps_sensor)
    trip_data = get_trips(labeled_data)
    interval_range = pd.interval_range(labeled_data.loc[labeled_data.index[0], 'local_timestamp'], 
                                       labeled_data.loc[labeled_data.index[-1], 'local_timestamp'], 
                                       freq=resolution)

    tripDf = get_trip_features(trip_data, dates, freq=resolution)
    entropyDf = entropy(sensor_data[gps_sensor], dates, resolution)
    hometimeDf = hometime(sensor_data[gps_sensor], dates, resolution)
    sigLocsDf = significant_locations_visited(sensor_data[gps_sensor], dates, resolution)

    df_list = [tripDf, entropyDf, hometimeDf, sigLocsDf]
    allDfs = reduce(lambda left, right: pd.merge(left, right, on=["Date"], how='left'), df_list)
    
    return allDfs
    
