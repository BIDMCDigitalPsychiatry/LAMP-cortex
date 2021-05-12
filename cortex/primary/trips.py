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
    :return (list): all trips in the given timeframe; each one has (start, end) 
    """
    ### Helper functions ###
    
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
    
    def total_distance(df,col, idx1, idx2):
        return df[col][idx1:idx2].sum()
    
    def end_timestamp(df, idx2, col='timestamp'):
        idx  = idx2 - 1
        return df['timestamp'][idx]
    
    def get_trips(gps_data):
        """
        Get trips for a given GPS DataFrame

        :param gps_data (pd.DataFrame): Dataframe of raw GPS data
        
        :return (list): list of dicts, where each dict is a trip, with the following keys: 'start', 'end', 'latitude', 'longitude','distance'
        """
        SPEED_THRESHOLD = 10.0
        TIME_THRESHOLD = 600
    
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
        new['distance'] = new.apply(lambda row: total_distance(gps_data, 'dx', row['idx'], row['idx_shift']), axis=1)
        new['end'] = new.apply(lambda row: end_timestamp(gps_data, row['idx_shift']), axis=1)
        new = new[['timestamp', 'end', 'latitude', 'longitude', 'distance']]
        new.columns = ['start', 'end', 'latitude', 'longitude','distance']
        return list(new.T.to_dict().values())

    ### ####
    
    df = pd.DataFrame.from_dict(list(reversed(gps(**kwargs)['data'])))
    log.info(f'Labeling GPS')
    labeled_gps = get_trips(df)
    return labeled_gps