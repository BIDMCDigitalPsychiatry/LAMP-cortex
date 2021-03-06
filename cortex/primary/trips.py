from ..feature_types import primary_feature
from ..raw.gps import gps
import numpy as np
import pandas as pd
import time
from geopy import distance
import datetime


@primary_feature(
    name="cortex.trips",
    dependencies=[gps],
    attach=True
)
def trips(**kwargs):
    """
    
    :param id (string):
    :param start (int):
    :param end (int):
    :return trip_list (list): all trips in the given timeframe; each one has (start, end)
    """
    ### Helper functions ###
    def label_gps_points(gps_data):
        """
        Label gps readings as being either "stationary" (0) or "transitionary" (1)

        :param sensor_data (dict): maps LAMP sensor to sensor events
        
        :return (pd.DataFrame): columns ['timestamp', 'latitude', 'longitude', 'stationary'], where 'stationary' is bool indicating whether GPS point is stationary/nonstationary
        """

        SPEED_THRESHOLD = 1.0
        stationary = True #initial state is not moving (in case gps points are very close together)

        labeled_data = gps_data.copy()
        for (_, point1), (_, point2) in zip(gps_data.iterrows(), gps_data.shift(-1).iterrows()):
            #If last timestamp in df, carry over label from previous point
            if point1['timestamp'] == labeled_data.loc[labeled_data.index[-1], 'timestamp']:
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
                    elapsed_time = ((datetime.datetime.utcfromtimestamp(point2['timestamp'] / 1000) - datetime.datetime.utcfromtimestamp(point1['timestamp'] / 1000)).seconds / 3600)            
                    #update stationary if points are separated temporally (elaped time non-zero)
                    if elapsed_time > 0.0:
                        speed =  dist / ((datetime.datetime.utcfromtimestamp(point2['timestamp'] / 1000) - datetime.datetime.utcfromtimestamp(point1['timestamp'] / 1000)).seconds / 3600)
                        if speed >= SPEED_THRESHOLD: stationary = False
                        else: stationary = True

                labeled_data.loc[labeled_data['timestamp'] == point1['timestamp'], 'stationary'] = stationary

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
        
        if len(df) == 0: return []
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        arr = np.array(df['stationary'])
        arr_ext = np.r_[False, arr == state, False]
        idx = np.flatnonzero(arr_ext[:-1] != arr_ext[1:])
        idx_list = list(zip(idx[:-1:2], idx[1::2] - int(inclusive)))

        trip_list = []
        for tup in idx_list:
            if tup[0] == tup[1]:
                continue
            dist = get_total_distance(df, tup[0], tup[1])
            trip = {'start': {'timestamp': time.mktime(df['timestamp'][tup[0]].timetuple()) * 1000,
                            'latitude': df['latitude'][tup[0]],
                            'longitude': df['longitude'][tup[0]]},
                    'end': {'timestamp': time.mktime(df['timestamp'][tup[1]].timetuple()) * 1000,
                            'latitude':df['latitude'][tup[1]],
                            'longitude':df['longitude'][tup[1]]},
                    'distance': dist}
            
            trip_list.append(trip)

        return trip_list

    ### ####

    df = pd.DataFrame.from_dict(list(reversed(gps(**kwargs)['data'])))
    labeled_gps = label_gps_points(df)
    trip_list = get_trips(labeled_gps)
    return trip_list
