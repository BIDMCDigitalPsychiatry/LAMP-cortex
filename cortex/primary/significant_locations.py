from ..feature_types import primary_feature, log
from ..raw.gps import gps
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np


from sklearn.cluster import DBSCAN
import LAMP 


@primary_feature(
    name='cortex.significant_locations',
    dependencies=[gps]
)
def significant_locations(k_max=10, eps=1e-5, **kwargs):
    """
    Get the coordinates of significant locations visited by the participant in the
    specified timeframe using the KMeans clustering method.
    NOTE: Running this feature on one large time window and running it on sub-windows
    of smaller sizes will result in different SigLocs.
    NOTE: This algorithm does NOT return the centroid radius and thus cannot be used
    to coalesce multiple SigLocs into one. 

    :param k_max (int): The maximum KMeans clusters to test (FIXME).
    :return latitude (float): The latitude of the SigLoc centroid.
    :return longitude (float): The longitude of the SigLoc centroid.
    :return radius (float): The radius of the SigLoc centroid (in meters).
    :return proportion (float): The proportion of GPS events located within this 
    centeroid compared to all GPS events over the entire time window.
    :return duration (int): The duration of time spent by the participant in the centroid.
    """

    # Calculates straight-line (not great-circle) distance between two GPS points on 
    # Earth in kilometers; equivalent to roughly ~55% - 75% of the Haversian (great-circle)
    # distance. 110.25 is conversion metric marking the length of a spherical degree.
    # 
    # https://jonisalonen.com/2014/computing-distance-between-coordinates-can-be-simple-and-fast/
    def euclid(g0, g1):
        def _euclid(lat, lng, lat0, lng0): # degrees -> km
            return 110.25 * ((((lat - lat0) ** 2) + (((lng - lng0) * np.cos(lat0)) ** 2)) ** 0.5)
        return _euclid(g0[0], g0[1], g1[0], g1[1])



    #Get DB scan metadata fir
    try:
        reduced_data = LAMP.Type.get_attachment(kwargs['id'], 'cortex.significant_locations.reduced')['data']
    except:
        reduced_data = []
        
    if len(reduced_data) == 0:
       reduced_data_end = 0
       new_reduced_data = []

    else: 
       reduced_data_end = reduced_data['end']
       new_reduced_data = reduced_data['data'].copy()

    if reduced_data_end < kwargs['end']: #update reduced data by getting new gps data and running dbscan
       ### DBSCAN ###
       _gps = gps(**{**kwargs, 'start':reduced_data_end})
       df = pd.DataFrame.from_dict(_gps)
       if len(df) == 0: return []
       df2 = df[['latitude', 'longitude']].values
       dbscan = DBSCAN(eps=eps)

       props = dbscan.fit_predict(df2)

       db_points = []
       for l in np.unique(props):
              
              db_lats, db_longs = [_gps[i]['latitude'] for i in range(len(_gps)) if props[i] == l], [_gps[i]['longitude'] for i in range(len(_gps)) if props[i] == l]
              db_duration = [_gps[i]['duration'] for i in range(len(_gps)) if props[i] == l]
              if l == -1:
                     db_points += [{'latitude':_gps[i]['latitude'],
                     'longitude':_gps[i]['longitude'],
                     'count':1} for i in range(len(_gps))]
              else:
                     lat_mean, long_mean = np.mean(db_lats), np.mean(db_longs)
                     if len(new_reduced_data) == 0:
                            db_points += [{'latitude':lat_mean, 
                                          'longitude':long_mean, 
                                          'count':len(db_lats)}]

                     min_dist_index = np.argmin([euclid((loc['latitude'], loc['longitude']), (lat_mean, long_mean)) for loc in reduced_data['data']])
                     if euclid((reduced_data[min_dist_index]['latitude'], reduced_data[min_dist_index]['longitude']), 
                              (lat_mean, long_mean)) < 20:
                              new_reduced_data[min_dist_index]['count'] += len(db_lats)
                     else:
                            db_points += [{'latitude':lat_mean, 
                                          'longitude':long_mean, 
                                          'count':len(db_lats)}]

       #Add new db points
       new_reduced_data += db_points
       reduced_data = {'end':kwargs['end'], 'data':new_reduced_data}

       #TODO: set attachment
       #LAMP.Type.set_attachment()
                            
       ### ###
    
    # Prepare input parameters.
    expanded_data = []
    for point in reduced_data['data']:
           expanded_data.extend([{'latitude':point['latitude'], 'longitude':point['longitude']} for _ in range(point['count'])])

    df = pd.DataFrame.from_dict(expanded_data)
    df2 = df[['latitude', 'longitude']].values
    K_clusters = range(1, min(k_max, len(df)))
    kmeans = [KMeans(n_clusters=i) for i in K_clusters]

    # Determine number of clusters to score.
    log.info(f'Calculating number of clusters to score with k_max={k_max}...')
    score = [kmeans[i].fit(df2).score(df2) for i in range(len(kmeans))]
    for i in range(len(score)):
        if i == len(score) - 1:
            k = i + 1
            break
        elif abs(score[i + 1] - score[i] < .01):
            k = i + 1
            break

    # Compute KMeans clusters. 
    log.info(f'Computing KMeans++ with k={k}...')
    kmeans = KMeans(n_clusters=k, init='k-means++')
    kmeans.fit(df2)

    #Get gps data for this window 
    _gps = gps(**kwargs)
    newdf = pd.DataFrame.from_dict(_gps)
    newdf2 = newdf[['latitude', 'longitude']].values
    props = kmeans.predict(newdf2)

    # Add proportion of GPS within each centroid and return output.
    return [{
        'latitude': center[0],
        'longitude': center[1],
        'radius': np.mean(euclid(center,

            # Transpose the points within the centroid and calculate the mean euclidean
            # distance (in km) from the center-point and convert that to meters.
            np.transpose(newdf2[np.argwhere(props == idx)].reshape((-1, 2)))
        ) * 1000),
        'proportion': props[props == idx].size / props.size,
        'duration': 0,
    } for idx, center in enumerate(kmeans.cluster_centers_)]

# Example: SigLocs computed over an entire ~1 month period for a (sample) patient.
"""
# _ = significant_locations(id="U26468383", start=1583532346000, end=1585363115000)
array([[ 38.82011755, -65.25113325],
       [ 38.83987899, -65.30446228],
       [ 38.84322825, -65.2857992 ],
       [ 38.80937655, -65.30578291],
       [ 38.83444352, -65.25400716],
       [ 38.82805236, -65.26600307]])
"""

# Example: SigLocs computed per-day over the ~1 month period for the same patient.
"""
# for i in range(1583532346000, 1585363115000, 86400000):
#    _ = significant_locations(id="U26468383", start=i, end=i + 86400000)

array([[ 38.82016175, -65.2510776 ],
       [ 38.83856934, -65.30599289]])
array([[ 38.82007812, -65.25102733]])
array([[ 38.82448846, -65.26074402]])
array([[ 38.82075185, -65.25395988]])
array([[ 38.83979135, -65.30477587],
       [ 38.82212767, -65.25193698]])
array([[ 38.83981318, -65.3038989 ],
       [ 38.82138312, -65.25295787]])
array([[ 38.82123812, -65.25218815],
       [ 38.8392549 , -65.30401214]])
array([[ 38.82019111, -65.25118828],
       [ 38.84656321, -65.29004538],
       [ 38.84048674, -65.26239201]])
array([[ 38.81980536, -65.2515454 ]])
array([[ 38.82049219, -65.25114458]])
array([[ 38.82007902, -65.25108851]])
array([[ 38.82005604, -65.25103972]])
array([[ 38.82153811, -65.25218648],
       [ 38.8396881 , -65.30392909]])
array([[ 38.82107608, -65.25172118],
       [ 38.84007579, -65.30398997]])
array([[ 38.83002289, -65.25896144],
       [ 38.82021031, -65.25112548]])
array([[ 38.80874184, -65.3086577 ],
       [ 38.82024919, -65.25175284],
       [ 38.8227823 , -65.28434095]])
array([[ 38.82014529, -65.25111414]])
array([[ 38.8201982 , -65.25113788]])
array([[ 38.82067827, -65.25169023]])
array([[ 38.82012319, -65.25110073]])
array([[ 38.82077895, -65.25165099]])
"""
