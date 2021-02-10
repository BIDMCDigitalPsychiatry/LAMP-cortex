import math 
import pandas as pd
import numpy as np
import datetime
from geopy import distance
from sklearn.cluster import KMeans

#import geopy

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
                #print(dist, elapsed_time)
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
        #print(df.loc[df.index == i, :])
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

    #callDf = pd.DataFrame([[min([t for t in times if t <= call[0]], key=lambda x: abs(x - call[0])), dict(call[1])['call_trace']] for call in call_data if dict(call[1])['call_type'] == label and call[0] >= sorted(times)[0] and call[0] <= sorted(times)[-1] + resolution], columns=['Date', 'Call Trace'])
    #for date in dates:
    #    print(date)

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
    """
    K_clusters = range(1, k_max)
    kmeans = [KMeans(n_clusters=i) for i in K_clusters]
    #score = [kmeans[i].fit(Y_axis).score(Y_axis) for i in range(len(kmeans))]
    score = [kmeans[i].fit(df[['latitude', 'longitude']]).score(df[['latitude', 'longitude']]) for i in range(len(kmeans))]
    for i in range(len(score)):
        if i == len(score) - 1:
            k = i +1
            break
        
        elif abs(score[i + 1] - score[i] < .01):
            k = i + 1
            break
    # k = 3
    kmeans = KMeans(n_clusters=k, init='k-means++')
    kmeans.fit(df[['latitude', 'longitude']])  # Compute k-means clustering.
    df.loc[:, 'cluster_label'] = kmeans.fit_predict(df[['latitude', 'longitude']])
    centers = kmeans.cluster_centers_  # Coordinates of cluster centers.
    labels = kmeans.predict(df[['latitude', 'longitude']])  # Labels of each point
    cluster_count = df['cluster_label'].value_counts()
    cluster_dict = cluster_count.to_dict()
    return centers

def entropy(df, dates, k_max=10):

    K_clusters = range(1, k_max)
    kmeans = [KMeans(n_clusters=i) for i in K_clusters]
    #score = [kmeans[i].fit(Y_axis).score(Y_axis) for i in range(len(kmeans))]
    print(kmeans, range(len(kmeans)))
    score = [kmeans[i].fit(df[['latitude', 'longitude']]).score(df[['latitude', 'longitude']]) for i in range(len(kmeans))]
    for i in range(len(score)):
        if i == len(score) - 1:
            k = i +1
            break
        
        elif abs(score[i + 1] - score[i] < .01):
            k = i + 1
            break
    # k = 3
    kmeans = KMeans(n_clusters=k, init='k-means++')
    kmeans.fit(df[['latitude', 'longitude']])  # Compute k-means clustering.

    df.loc[:, 'cluster_label'] = kmeans.fit_predict(df[['latitude', 'longitude']])
    centers = kmeans.cluster_centers_  # Coordinates of cluster centers.

    #Find entropy for each time period
    
    print(dates)
    labels = kmeans.predict(df[['latitude', 'longitude']])  # Labels of each point
    cluster_count = df['cluster_label'].value_counts()
    cluster_dict = cluster_count.to_dict()

    entropy = 0.0
    size = len(df)
    for n in cluster_dict:
        pctg = cluster_dict[n] / size
        prod = pctg * math.log(pctg)
        entropy -= prod

    return entropy



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

    tripDf = get_trip_features(trip_data, 
                               dates, 
                               freq=resolution)

    #entropy(gps_sensor, dates)
    
    return tripDf
    
