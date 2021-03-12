from lamp_cortex.features.primary.primary import primary_feature
import lamp_cortex
import numpy as np
from sklearn import KMeans

@primary_feature(
    name="cortex.feature.significant_locations"
    dependencies=['lamp.gps']
)
def significant_locs(participant_id, k_max=10, **kwargs):
    """
    Get the coordinates of the significant locations

    :return centers ()
    :return df (pd.DataFrame): gps data with each readings labeled with a sig loc
    """
    K_clusters = range(1, min(k_max, len(df)))
    kmeans = [KMeans(n_clusters=i) for i in K_clusters]
    df_arr = df[['latitude', 'longitude']].values
    score = [kmeans[i].fit(df_arr).score(df_arr) for i in range(len(kmeans))]
    for i in range(len(score)):
        if i == len(score) - 1:
            k = i +1
            break
        
        elif abs(score[i + 1] - score[i] < .01):
            k = i + 1
            break

    kmeans = KMeans(n_clusters=k, init='k-means++')
    kmeans.fit(df_arr)  # Compute k-means clustering.
    df.loc[:, 'cluster_label'] = kmeans.fit_predict(df[['latitude', 'longitude']])
    centers = kmeans.cluster_centers_  # Coordinates of cluster centers.

    return centers, df