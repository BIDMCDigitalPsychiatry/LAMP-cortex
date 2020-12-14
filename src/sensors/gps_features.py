import math 
import pandas as pd
import numpy as np
from datetime import datetime
from geopy import distance

#import geopy

def label_gps_points(sensor_data):
    """
    Label gps readings as being either "stationary" (0) or "transitionary" (1)

    :param sensor_data (dict): maps LAMP sensor to sensor events
    
    :return (pd.DataFrame): columns ['local_timestamp', 'latitude', 'longitude', 'stationary'], where 'stationary' is bool indicating whether GPS point is stationary/nonstationary
    """
    SPEED_THRESHOLD = 1.0

    labeled_data = sensor_data['lamp.gps'].copy()
    for (_, point1), (_, point2) in zip(sensor_data['lamp.gps'].iterrows(), sensor_data['lamp.gps'].shift(-1).iterrows()):
        #If last timestamp in df, carry over label from previous point
        if point1['local_timestamp'] == labeled_data.loc[labeled_data.index[-1], 'local_timestamp']:
            labeled_data.loc[labeled_data.index[-1], 'stationary'] = labeled_data.loc[labeled_data.index[-2], 'stationary']
            
        else:
            dist = distance.distance((point1['latitude'], point1['longitude']), (point2['latitude'], point2['longitude'])).km 
            speed =  dist / ((datetime.utcfromtimestamp(point2['local_timestamp'] / 1000) - datetime.utcfromtimestamp(point1['local_timestamp'] / 1000)).seconds / 3600)
            
            if speed >= SPEED_THRESHOLD: stationary = False
            else: stationary = True
            labeled_data.loc[labeled_data['local_timestamp'] == point1['local_timestamp'], 'stationary'] = stationary

    return labeled_data

def get_total_distance(df, idx1, idx2):
    dist = 0
    for i in range(idx1 + 1, idx2 + 1):
        c2 = (df['latitude'][i], df['longitude'][i])
        c1 = (df['latitude'][i-1], df['longitude'][i-1])
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

def trip_count(dates):
    pass

def get_trip_features(trips, dates):#interval_range, l):
    '''
    trip_dict values' units:
    Duration - Minutes
    Distance Traveled - Meters
    '''

    #callDf = pd.DataFrame([[min([t for t in times if t <= call[0]], key=lambda x: abs(x - call[0])), dict(call[1])['call_trace']] for call in call_data if dict(call[1])['call_type'] == label and call[0] >= sorted(times)[0] and call[0] <= sorted(times)[-1] + resolution], columns=['Date', 'Call Trace'])
    for date in dates:
        print(date)

    
    # trip_dict = gen_trip_dict(interval_range)
    # for i in range(len(interval_range)):
    #     for j in range(len(l)):
    #         if l[j][0] >= interval_range[i].left and l[j][1] <= interval_range[i].right:
                
    #             trip_dict[interval_range[i]]['Trip Count'] += 1
                
    #             trip_len = l[j][1] - l[j][0]
    #             days, seconds = trip_len.days, trip_len.seconds
    #             hours = days * 1440 + seconds / 60
    #             trip_dict[interval_range[i]]['Duration'] += hours

    #             trip_dict[interval_range[i]]['Distance Traveled'] += l[j][2]

    # return trip_dict



def all(sensor_data, dates, resolution):
    labeled_data = label_gps_points(sensor_data)
    trip_data = get_trips(labeled_data)
    interval_range = pd.interval_range(labeled_data.loc[labeled_data.index[0], 'local_timestamp'], 
                                       labeled_data.loc[labeled_data.index[-1], 'local_timestamp'], 
                                       freq=resolution)

    get_trip_features(trip_data, dates)


if __name__ == "__main__":
    pass