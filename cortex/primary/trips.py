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
        SPEED_THRESHOLD = 10.0
        TIME_THRESHOLD = 600 
        #stationary = True #initial state is not moving (in case gps points are very close together)
        log.info(f'create copy of gps_data')
        #labeled_data = gps_data.copy()
        print(gps_data)        
    
        gps_data['dt'] = (gps_data['timestamp'] - gps_data['timestamp'].shift()) / (1000*3600)
        gps_data['dx'] = haversine_np(
            gps_data.latitude.shift(fill_value=0), gps_data.longitude.shift(fill_value=0),
            gps_data.loc[1:, 'latitude'], gps_data.loc[1:, 'longitude']
        )
        gps_data['speed'] = gps_data['dx'] / gps_data['dt']
        gps_data['stationary'] = ((gps_data['speed'] < SPEED_THRESHOLD) | (gps_data['dt'] > TIME_THRESHOLD))
        gps_data['stationary_1'] = gps_data['stationary'].shift()
        gps_data['idx'] = gps_data.index
        new = gps_data[gps_data['stationary'] != gps_data['stationary_1']]
        new['idx_shift'] = new['idx'].shift(-1, fill_value=0)
        new[new['stationary'] == False]
        new = new[new['idx_shift'] != 0]
        new['distance'] = new.apply(lambda row: distance(gps_data, 'dx', row['idx'], row['idx_shift']), axis=1)
        new['end'] = new.apply(lambda row: end_timestamp(gps_data, row['idx_shift']), axis=1)
        new = new[['timestamp', 'end', 'latitude', 'longitude', 'distance']]
        new.columns = ['start', 'end', 'latitude', 'longitude','distance']
        return list(new.T.to_dict().values())

    ### ####
    
    
    log.info(f'Modifying DataFrame')
    start = time.time()
    df = pd.DataFrame.from_dict(list(reversed(gps(**kwargs)['data'])))
    log.info(f'Labeling GPS')
    labeled_gps = label_gps_points(df)
    print(time.time() - start)
    print(len(labeled_gps))
    return labeled_gps