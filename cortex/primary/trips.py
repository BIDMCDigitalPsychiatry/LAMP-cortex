""" Module for computing trips from gps """
import numpy as np
import pandas as pd
from ..feature_types import primary_feature, log
from ..raw.gps import gps

# Constants
SPEED_THRESHOLD = 10.0
TIME_THRESHOLD = 600

@primary_feature(
    name="cortex.trips",
    dependencies=[gps]
)
def trips(attach=True,
          **kwargs):
    """Finds bouts of movement, based on the gps sensor.

    Args:
        attach
        **kwargs:
            d (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature 
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature 
                is being generated. Required.

    Returns:
        A dict with fields:
            data (list): All trips in the given timeframe; seach one has (start, end).
            has_raw_data (int): Indicates whether there is raw data.
    """
    ### Helper functions ###
    def haversine_np(lon1, lat1, lon2, lat2):
        """
        Source:
        https://stackoverflow.com/questions/42877802/pandas-dataframe-join-items-in-range-based-on-their-geo-coordinates-longitude
        """
        lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        val = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2

        val2 = 2 * np.arcsin(np.sqrt(val))
        km_dist = 6367 * val2
        return km_dist

    # def euclid_distance1(lat, lng, lat0, lng0): # degrees -> km
    #    """ Using this for convenience over GeoPy because it doesn't support our
    #        vectorized operations w/ Pandas
    #    """
    #    return 110.25 * ((((lat - lat0) ** 2) + (((lng - lng0) * np.cos(lat0)) ** 2)) ** 0.5)

    def total_distance(df_dist,col, idx1, idx2):
        """ Get the total distance traveled.
        """
        return df_dist[col][idx1:idx2].sum()

    def end_timestamp(df_dist, idx2, col='timestamp'):
        """ Return the end timestamp.
        """
        idx  = idx2 - 1
        return df_dist[col][idx]

    def get_trips(gps_data):
        """
        Get trips for a given GPS DataFrame

        :param gps_data (pd.DataFrame): Dataframe of raw GPS data

        :return (list): list of dicts, where each dict is a trip, with the
            following keys: 'start', 'end', 'latitude', 'longitude','distance'
        """
        gps_data.loc[:, 'dt'] = (gps_data['timestamp'] - gps_data['timestamp'].shift()) / (1000*3600)
        gps_data.loc[:, 'dx'] = haversine_np(
            gps_data.latitude.shift(fill_value=0), gps_data.longitude.shift(fill_value=0),
            gps_data.loc[1:, 'latitude'], gps_data.loc[1:, 'longitude']
        )
        gps_data.loc[:, 'speed'] = gps_data['dx'] / gps_data['dt']
        gps_data.loc[:, 'stationary'] = ((gps_data['speed'] < SPEED_THRESHOLD) |
                                  (gps_data['dt'] > TIME_THRESHOLD))
        gps_data.loc[:, 'stationary_1'] = gps_data['stationary'].shift()
        gps_data.loc[:, 'idx'] = gps_data.index
        new = gps_data[gps_data['stationary'] != gps_data['stationary_1']]
        new.loc[:, 'idx_shift'] = new['idx'].shift(-1, fill_value=0)
        new = new[new['stationary'] == False]
        new = new[new['idx_shift'] != 0]
        new.loc[:, 'distance'] = new.apply(lambda row:
                                total_distance(gps_data, 'dx',
                                row['idx'], row['idx_shift']), axis=1)
        new.loc[:, 'end'] = new.apply(lambda row: end_timestamp(gps_data, row['idx_shift']), axis=1)
        new = new[['timestamp', 'end', 'latitude', 'longitude', 'distance']]
        new.columns = ['start', 'end', 'latitude', 'longitude','distance']
        return list(new.T.to_dict().values())


    df_dist = pd.DataFrame.from_dict(list(reversed(gps(**kwargs)['data'])))
    if len(df_dist) == 0:
        return {'data': [], 'has_raw_data': 0}
    log.info('Labeling GPS')
    labeled_gps = get_trips(df_dist)
    return {'data': labeled_gps, 'has_raw_data': 1}
