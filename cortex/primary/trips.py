from ..feature_types import primary_feature, log
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
    # vectorized haversine function
    def haversine_np(lon1, lat1, lon2, lat2):
        """
        Source: https://stackoverflow.com/questions/42877802/pandas-dataframe-join-items-in-range-based-on-their-geo-coordinates-longitude 

        """
        lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2

        c = 2 * np.arcsin(np.sqrt(a))
        km = 6367 * c
        return km

    def euclid_distance1(lat, lng, lat0, lng0): # degrees -> km
        '''
        Using this for convenience over GeoPy because it doesn't support our vectorized operations w/ Pandas
        '''
        return 110.25 * ((((lat - lat0) ** 2) + (((lng - lng0) * np.cos(lat0)) ** 2)) ** 0.5)
    def distance(df,col, idx1, idx2):
        return df[col][idx1:idx2].sum()
    def end_timestamp(df, idx2, col='timestamp'):
        idx  = idx2 - 1
        return df['timestamp'][idx]
    ### Helper functions ###
    def label_gps_points(gps_data):
        """
        Label gps readings as being either "stationary" (0) or "transitionary" (1)

        :param sensor_data (dict): maps LAMP sensor to sensor events
        
        :return (pd.DataFrame): columns ['timestamp', 'latitude', 'longitude', 'stationary'], where 'stationary' is bool indicating whether GPS point is stationary/nonstationary
        """
        log.info(f'Inside label_gps_points')
        #SPEED_THRESHOLD = 1.0
        #stationary = True #initial state is not moving (in case gps points are very close together)
        log.info(f'create copy of gps_data')
        #labeled_data = gps_data.copy()
        print(gps_data)
        '''
        gps_data['timestamp_1'] = gps_data['timestamp'].shift(-1)
        gps_data['latitude_1'] = gps_data['latitude'].shift(-1)
        gps_data['longitude_1'] = gps_data['longitude'].shift(-1)
        gps_data['stationary'] = 0
        
        gps_data['dt'] = (gps_data['timestamp'] - gps_data['timestamp_1']) / 1000
        gps_data['dx'] = euclid_distance1(
            gps_data['latitude'], gps_data['longitude'],
            gps_data['latitude_1'], gps_data['longitude_1']
        )
        '''
        
    
        gps_data['dt'] = (gps_data['timestamp'] - gps_data['timestamp'].shift()) / (1000*3600)
        gps_data['dx'] = haversine_np(
            gps_data.latitude.shift(fill_value=0), gps_data.longitude.shift(fill_value=0),
            gps_data.loc[1:, 'latitude'], gps_data.loc[1:, 'longitude']
        )
        gps_data['speed'] = gps_data['dx'] / gps_data['dt']
        gps_data['stationary'] = ((gps_data['speed'] < 10) | (gps_data['dt'] > 600))
        gps_data['stationary_1'] = gps_data['stationary'].shift()
        gps_data['idx'] = gps_data.index
        new = gps_data[gps_data['stationary'] != gps_data['stationary_1']]
        new['idx_shift'] = new['idx'].shift(-1, fill_value=0)
        new[new['stationary'] == False]
        new = new[new['idx_shift'] != 0]
        new['distance'] = new.apply(lambda row: distance(gps_data, 'dx', row['idx'], row['idx_shift']), axis=1)
        new['end'] = new.apply(lambda row: end_timestamp(gps_data, row['idx_shift']), axis=1)
        new = new[['timestamp', 'end', 'latitude', 'longitude', 'distance']]

        return list(new.T.to_dict().values())
        
        #return gps_data
        '''
        xyz = zip(gps_data.iterrows(), gps_data.shift(-1).iterrows())
        for (_, point1), (_, point2) in xyz:
            print((point1['timestamp'], point2['timestamp']))
            start = time.time()
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
            print(ctr, time.time() - start)
            ctr += 1
        return labeled_data
        '''
        
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
    '''
    log.info(f'Modifying DataFrame')
    df = pd.DataFrame.from_dict(list(reversed(gps(**kwargs)['data'])))
    log.info(f'Labeling GPS')
    labeled_gps = label_gps_points(df)
    log.info(f'Running get_trips')
    trip_list = get_trips(labeled_gps)
    '''
    
    '''
    start = time.time()
    log.info(f'Modifying DataFrame')
    df = pd.DataFrame.from_dict(list(reversed(gps(**kwargs)['data'])))
    log.info(f'Labeling GPS')
    labeled_gps = label_gps_points(df)
    log.info(f'Running get_trips')
    trip_list = get_trips(labeled_gps)
    print(time.time() - start)
    return trip_list
    '''
    
    log.info(f'Modifying DataFrame')
    start = time.time()
    df = pd.DataFrame.from_dict(list(reversed(gps(**kwargs)['data'])))
    log.info(f'Labeling GPS')
    labeled_gps = label_gps_points(df)
    print(time.time() - start, labeled_gps[:2])
    print(labeled_gps)
    return labeled_gps