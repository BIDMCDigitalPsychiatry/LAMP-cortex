""" Module for computing the significant locations using gps data """
import math
from sklearn.cluster import KMeans, DBSCAN
import pandas as pd
import numpy as np
import LAMP
from ..feature_types import primary_feature, log
from ..raw.gps import gps


@primary_feature(
    name='cortex.significant_locations',
    dependencies=[gps]
)
def significant_locations(k_max=10,
                          eps=1e-5,
                          max_clusters=-1,
                          min_cluster_size=0.01,
                          max_dist=300,
                          method='mode',
                          attach=False,
                          **kwargs):
    """Get the coordinates and proportional time of significant locations visited by the participant.


    This method uses the the KMeans clustering method.
    NOTE: Via DBSCan, this algorithm first reduces the amount of gps readings
    used to generate significant locations. If there is a large amount of new
    gps data to reduce, this step can take a long time
    NOTE: DBScan uses O(n*k) memory. If you run it on a large GPS dataframe
    (>100k points), a memory crash could occur

    NOTE: This algorithm does NOT return the centroid radius and thus cannot
    be used to coalesce multiple SigLocs into one.

    Args:
        k_max (int): The maximum KMeans clusters to test (FIXME).
        max_clusters (int): The number of clusters to create using
            method='mode'. Note: default is to use min_cluster_size when
            max_clusters=-1.
        min_cluster_size (float): The percentage of points that must be in
            a cluster for it to be significant.
        max_dist (int): The farthest distance, in m, that two points can be separated by.
        method (string): 'mode' or 'k_means'. Method for computing sig_locs.
        attach (boolean): Indicates whether to use LAMP.Type.attachments in calculating the feature.
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.

    Returns:
        A dict containing the fields:
            data (list): A list of sig locs, in the time periods, with the fields:
                latitude (float): The latitude of the SigLoc centroid.
                longitude (float): The longitude of the SigLoc centroid.
                radius (float): The radius of the SigLoc centroid (in meters).
                proportion (float): The proportion of GPS events located within
                    this centeroid compared to all GPS events over the entire time window.
                duration (int): The duration of time spent by the participant in
                    the centroid.
            has_raw_data (int): Indicates whether there is raw data present.
    """
    if method == 'k_means':
        return _significant_locations_kmeans(k_max, eps, **kwargs)
    return _significant_locations_mode(max_clusters, min_cluster_size, max_dist, **kwargs)

def euclid(gps0, gps1):
    """ Calculates euclidean distance

        Args:
            gps0, gps1 the two gps points in lattitude and longitude
        Returns:
            The euclidean distance

        Calculates straight-line (not great-circle) distance between two GPS
        points on Earth in kilometers; equivalent to roughly ~55% - 75% of the
        Haversian (great-circle) distance. 110.25 is conversion metric marking
        the length of a spherical degree.

        Reference:
        https://jonisalonen.com/2014/computing-distance-between-coordinates-can-be-simple-and-fast/
    """
    def _euclid(lat, lng, lat0, lng0):  # degrees -> km
        return 110.25 * ((((lat - lat0) ** 2) + (((lng - lng0) * np.cos(lat0)) ** 2)) ** 0.5)
    return _euclid(gps0[0], gps0[1], gps1[0], gps1[1])


def distance(cluster1, cluster2):
    """ Function to find the distance

        Args:
            cluster1 (tuple): Geo coordinate
            cluster2 (tuple) Geo Coordinate
        Returns:
            A float, the distance in meters.
    """
    R = 6378.137
    d_lat = cluster2[0] * math.pi / 180 - cluster1[0] * math.pi / 180
    d_lon = cluster2[1] * math.pi / 180 - cluster1[1] * math.pi / 180
    val1 = math.sin(d_lat / 2) * math.sin(d_lat / 2)
    val2 = math.cos(cluster1[0] * math.pi / 180) * math.cos(cluster2[0] * math.pi / 180)
    val3 = math.sin(d_lon / 2) * math.sin(d_lon / 2)
    val4 = val1 + (val2 * val3)
    dist = 2 * math.atan2(math.sqrt(val4), math.sqrt(1 - val4))
    dist_m = R * dist
    return dist_m * 1000

def remove_clusters(clusters, max_dist):
    """ Function to remove clusters that are less than specified distance
        (MAX_DIST) away from at least one other cluster

        Args:
            clusters (list): Each item a dict containing a significant location.
            max_dist (int): Maximum distance allowed between clusters (in meters).
            
        Returns:
            A list, the same as clusters, with {'rank'} fields added.
    """
    n = len(clusters)
    for i in range(n - 1):
        big_cluster_prop = clusters[i]['proportion']
        if big_cluster_prop > 0:
            big_cluster_latlon = (clusters[i]['latitude'], clusters[i]['longitude'])
            for j in range(i + 1, n):
                small_cluster_latlon = (clusters[j]['latitude'], clusters[j]['longitude'])
                dist = distance(big_cluster_latlon, small_cluster_latlon)
                if dist < max_dist:
                    clusters[i]['proportion'] += clusters[j]['proportion']
                    clusters[j]['proportion'] = 0
                    clusters[i]['duration'] += clusters[j]['duration']
    clusters = [cl for cl in clusters if cl['proportion'] > 0]
    for i, cluster in enumerate(clusters):
        cluster['rank'] = i
    return clusters

def _location_duration(df, cluster):
    """ Helper function to get location duration

        Args:
            df_cluster (pd.DataFrame): The original dataframe of GPS reads.
            cluster (int): The cluster index (i.e. rank).
            
        Returns:
            A float, duration in that cluster (in ms).
    """
    df = df[::-1].reset_index()
    arr_ext = np.r_[False, df['cluster'] == cluster, False]

    idx = np.flatnonzero(arr_ext[:-1] != arr_ext[1:])
    idx_list = list(zip(idx[:-1:2], idx[1::2] - int(True)))

    hometime_list = []
    for tup in idx_list:
        if tup[0] == tup[1]:
            continue
        duration = df['timestamp'][tup[1]] - df['timestamp'][tup[0]]

        hometime_list.append(duration)

    return sum(hometime_list)

def _significant_locations_kmeans(k_max=10, eps=1e-5, **kwargs):
    """Function to return significant locations using kmeans
        clustering.
        
        Args:
            k_max (int): The maximum number of clusters ot use.
            eps (float): The maximum distance separating points in the
                same cluster.
            **kwargs:
            
        Returns:
    """
    # Get DB scan metadata fir
    try:
        reduced_data = LAMP.Type.get_attachment(kwargs['id'],
                                'cortex.significant_locations.reduced')['data']
    except:
        reduced_data = {'end':0, 'data':[]}

    reduced_data_end = reduced_data['end']
    new_reduced_data = reduced_data['data'].copy()

    # update reduced data by getting new gps data and running dbscan
    if reduced_data_end < kwargs['end']:
        ### DBSCAN ###
        _gps = gps(**{**kwargs, 'start':reduced_data_end})['data']
        df_original = pd.DataFrame.from_dict(_gps)
        if len(df_original) == 0:
            return {'data': [], 'has_raw_data': 0}
        df_original = df_original[df_original['timestamp'] != df_original['timestamp'].shift()]

        # To prevent memory issues, limit size of db scan and perform iteratively
        cut_df = np.split(df_original,
                [30000 * i for i in range(math.ceil(len(df_original) / 30000))])
        for d in cut_df:
            if len(d) == 0:
                continue

            d.reset_index(drop=True)
            new_reduced_data = reduced_data['data'].copy()
            dbscan = DBSCAN(eps=eps)
            props = dbscan.fit_predict(d[['latitude', 'longitude']].values)
            db_points = []
            for l in np.unique(props):
                db_lats, db_longs = ([d.iloc[i]['latitude']
                                      for i in range(len(d)) if props[i] == l],
                                     [d.iloc[i]['longitude']
                                      for i in range(len(d)) if props[i] == l])
                # db_duration = [d.iloc[i]['timestamp'] for i in range(len(d)) if props[i] == l]
                if l == -1:
                    db_points += [{'latitude':db_lats[i],
                    'longitude':db_longs[i],
                    'count':1} for i in range(len(db_lats))]
                else:
                    lat_mean, long_mean = np.mean(db_lats), np.mean(db_longs)
                    if len(reduced_data['data']) == 0:
                        db_points += [{'latitude':lat_mean,
                                      'longitude':long_mean,
                                  'count':len(db_lats)}]

                    else:
                        min_dist_index = np.argmin([euclid((loc['latitude'],
                                                            loc['longitude']),
                                                           (lat_mean, long_mean))
                                                    for loc in reduced_data['data']])
                        if (euclid((reduced_data['data'][min_dist_index]['latitude'],
                                   reduced_data['data'][min_dist_index]['longitude']),
                              (lat_mean, long_mean)) < 20):
                            new_reduced_data[min_dist_index]['count'] += len(db_lats)
                        else:
                            db_points += [{'latitude':lat_mean,
                                          'longitude':long_mean,
                                      'count':len(db_lats)}]

            # Add new db points
            new_reduced_data += db_points
            reduced_data = {'end':kwargs['end'], 'data':new_reduced_data}

        LAMP.Type.set_attachment(kwargs['id'], 'me',
                    attachment_key='cortex.significant_locations.reduced',
                    body=reduced_data)
       ### ###

    # Prepare input parameters.
    expanded_data = []
    for point in reduced_data['data']:
        expanded_data.extend([{'latitude':point['latitude'],
                               'longitude':point['longitude']}
                                for _ in range(point['count'])])

    df_original = pd.DataFrame.from_dict(expanded_data)
    df2 = df_original[['latitude', 'longitude']].values
    k_clusters = range(1, min(k_max, len(df_original)))
    kmeans = [KMeans(n_clusters=i) for i in k_clusters]

    # Determine number of clusters to score.
    log.info('Calculating number of clusters to score with k_max=%d...', k_max)
    score = [kmeans[i].fit(df2).score(df2) for i in range(len(kmeans))]
    for i, val in enumerate(score):
        if i == len(score) - 1:
            k = i + 1
            break
        if abs(score[i + 1] - val < .01):
            k = i + 1
            break

    # Compute KMeans clusters.
    log.info('Computing KMeans++ with k=%d...', k)
    kmeans = KMeans(n_clusters=k, init='k-means++')
    kmeans.fit(df2)

    # Get gps data for this window
    _gps = gps(**kwargs)['data']
    if len(_gps) == 0: # return empty list if no data
        return {'data': [], 'has_raw_data': 0}

    newdf = pd.DataFrame.from_dict(_gps)
    newdf_coords = newdf[['latitude', 'longitude']].values
    props = kmeans.predict(newdf_coords)
    newdf.loc[:, 'cluster'] = props


    # Add proportion of GPS within each centroid and return output.
    return {'data': [{
        'start':kwargs['start'],
        'end':kwargs['end'],
        'latitude': center[0],
        'longitude': center[1],
        'rank': idx, #significant locations in terms of prevelance (0 being home)
        'radius': np.mean(euclid(center,

            # Transpose the points within the centroid and calculate the mean euclidean
            # distance (in km) from the center-point and convert that to meters.
            np.transpose(newdf_coords[np.argwhere(props == idx)].reshape((-1, 2)))
        ) * 1000) if props[props == idx].size > 0 else None,
        'proportion': props[props == idx].size / props.size,
        # props[props == idx].size * 200 #EXPECTED duration in ms
        'duration': _location_duration(newdf, idx)
    } for idx, center in enumerate(kmeans.cluster_centers_)], 'has_raw_data': 1}

def _significant_locations_mode(max_clusters, min_cluster_size, max_dist, **kwargs):
    """ Function to assign points to k significant locations using mode method.

        Args:
            max_clusters: the maximum number of clusters to define
                          default (0) is to run until there are no clusters
                          left with greater than min_cluster_size points
                          ** set to -1 to use cluster_size only
            min_cluster_size: only applies if max_clusters is not set,
                          minumum number of points that can be classified
                          as a cluster, as a percentage of total number of
                          points
    """
    # get gps data
    _gps = gps(**kwargs)['data']
    if len(_gps) == 0:
        return {'data': [], 'has_raw_data': 0}

    df_original = pd.DataFrame.from_dict(_gps)
    df_original = df_original[df_original['timestamp'] != df_original['timestamp'].shift()]
    df_clusters = df_original.copy(deep=True)
    ind = df_original.shape[0] * [-1]
    df_clusters["cluster"] = ind
    cluster_locs = []

    df_clusters['latitude'] = df_clusters['latitude'].apply(lambda x: round(x, 3))
    df_clusters['longitude'] = df_clusters['longitude'].apply(lambda x: round(x, 3))
    top_counts = df_clusters[['latitude', 'longitude']].value_counts()
    top_points = top_counts.index.tolist()

    min_cluster_points = int(min_cluster_size * len(df_original))

    if max_clusters != -1:
        for k in range(max_clusters):
            if k < len(top_points):
                df_clusters.loc[(df_clusters["latitude"] == top_points[k][0]) &
                                (df_clusters["longitude"] == top_points[k][1]),
                                'cluster'] = k
                cluster_locs.append(top_points[k])
    else:
        k = 0
        while (k < len(top_counts) and top_counts.iloc[k] > min_cluster_points
               and k < len(df_original) - 1):
            df_clusters.loc[(df_clusters["latitude"] == top_points[k][0]) &
                            (df_clusters["longitude"] == top_points[k][1]),
                            'cluster'] = k
            cluster_locs.append(top_points[k])
            k += 1

    return {'data': remove_clusters([{
        'start':kwargs['start'],
        'end':kwargs['end'],
        'latitude': center[0],
        'longitude': center[1],
        'rank': idx,  # significant locations in terms of prevelance (0 being home)
        'radius': np.mean(euclid((center[1],center[0]),

            # Transpose the points within the centroid and calculate the mean
            # euclidean distance (in km) from the center-point and convert that
            # to meters.
            np.transpose(df_original.loc[(df_clusters['cluster'] == idx),
                        ['longitude','latitude']].values.reshape((-1, 2)))
        ) * 1000) if df_clusters[df_clusters['cluster'] != idx].size else None,
        'proportion': (df_clusters[df_clusters['cluster'] == idx].size /
                       df_clusters[df_clusters['cluster'] != -1].size),
        'duration': _location_duration(df_clusters, idx)
    } for idx, center in enumerate(cluster_locs)], max_dist), 'has_raw_data': 1}
