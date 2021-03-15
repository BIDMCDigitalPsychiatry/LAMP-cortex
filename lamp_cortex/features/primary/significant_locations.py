from lamp_cortex.features.primary.primary import primary_feature
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from pprint import pprint

@primary_feature(
    name='cortex.feature.significant_locations',
    dependencies=['lamp.gps']
)
def significant_locations(k_max=10, **kwargs):
    """
    Get the coordinates of significant locations visited by the participant in the
    specified timeframe using the KMeans clustering method.
    NOTE: Running this feature on one large time window and running it on sub-windows
    of smaller sizes will result in different SigLocs.
    NOTE: This algorithm does NOT return the centroid radius and thus cannot be used
    to coalesce multiple SigLocs into one. 

    :return latitude (float): The latitude of the SigLoc centroid.
    :return longitude (float): The longitude of the SigLoc centroid.
    :return proportion (float): The proportion of GPS events located within this 
    centeroid compared to all GPS events over the entire time window.
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

    # Prepare input parameters.
    df = pd.DataFrame.from_dict(kwargs['sensor_data']['lamp.gps'])
    df = df.drop('data', 1).assign(**df.data.dropna().apply(pd.Series))
    df2 = df[['latitude', 'longitude']].values
    K_clusters = range(1, min(k_max, len(df)))
    kmeans = [KMeans(n_clusters=i) for i in K_clusters]

    # Determine number of clusters to score.
    score = [kmeans[i].fit(df2).score(df2) for i in range(len(kmeans))]
    for i in range(len(score)):
        if i == len(score) - 1:
            k = i + 1
            break
        elif abs(score[i + 1] - score[i] < .01):
            k = i + 1
            break

    # Compute KMeans clusters. 
    kmeans = KMeans(n_clusters=k, init='k-means++')
    kmeans.fit(df2)
    props = kmeans.fit_predict(df2)

    # Add proportion of GPS within each centroid and return output.
    return [{
        'latitude': center[0],
        'longitude': center[1],
        'radius': np.mean(euclid(center,

            # Transpose the points within the centroid and calculate the mean euclidean
            # distance (in km) from the center-point and convert that to meters.
            np.transpose(df2[np.argwhere(props == idx)].reshape((-1, 2)))
        ) * 1000),
        'proportion': props[props == idx].size / props.size,
    } for idx, center in enumerate(kmeans.cluster_centers_)]

# Example: SigLocs computed over an entire ~1 month period for a (sample) patient.
"""
# _ = significant_locations(id="U26468383", start=1583532346000, end=1585363115000)
array([[ 42.32011755, -71.05113325],
       [ 42.33987899, -71.10446228],
       [ 42.34322825, -71.0857992 ],
       [ 42.30937655, -71.10578291],
       [ 42.33444352, -71.05400716],
       [ 42.32805236, -71.06600307]])
"""

# Example: SigLocs computed per-day over the ~1 month period for the same patient.
"""
# for i in range(1583532346000, 1585363115000, 86400000):
#    _ = significant_locations(id="U26468383", start=i, end=i + 86400000)

array([[ 42.32016175, -71.0510776 ],
       [ 42.33856934, -71.10599289]])
array([[ 42.32007812, -71.05102733]])
array([[ 42.32448846, -71.06074402]])
array([[ 42.32075185, -71.05395988]])
array([[ 42.33979135, -71.10477587],
       [ 42.32212767, -71.05193698]])
array([[ 42.33981318, -71.1038989 ],
       [ 42.32138312, -71.05295787]])
array([[ 42.32123812, -71.05218815],
       [ 42.3392549 , -71.10401214]])
array([[ 42.32019111, -71.05118828],
       [ 42.34656321, -71.09004538],
       [ 42.34048674, -71.06239201]])
array([[ 42.31980536, -71.0515454 ]])
array([[ 42.32049219, -71.05114458]])
array([[ 42.32007902, -71.05108851]])
array([[ 42.32005604, -71.05103972]])
array([[ 42.32153811, -71.05218648],
       [ 42.3396881 , -71.10392909]])
array([[ 42.32107608, -71.05172118],
       [ 42.34007579, -71.10398997]])
array([[ 42.33002289, -71.05896144],
       [ 42.32021031, -71.05112548]])
array([[ 42.30874184, -71.1086577 ],
       [ 42.32024919, -71.05175284],
       [ 42.3227823 , -71.08434095]])
array([[ 42.32014529, -71.05111414]])
array([[ 42.3201982 , -71.05113788]])
array([[ 42.32067827, -71.05169023]])
array([[ 42.32012319, -71.05110073]])
array([[ 42.32077895, -71.05165099]])
"""
