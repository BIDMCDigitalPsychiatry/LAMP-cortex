from lamp_cortex.features.primary.primary import primary_feature
import pandas as pd
from sklearn.cluster import KMeans

@primary_feature(
    name='cortex.feature.significant_locations',
    dependencies=['lamp.gps']
)
def significant_locations(k_max=10, **kwargs):
    """
    Get the coordinates of significant locations visited by the participant in the
    specified timeframe.

    :return centers (): TODO.
    :return df (pd.DataFrame): GPS data with each reading labeled as significant or not.
    """

    # Prepare input parameters.
    df = kwargs['sensor_data']['lamp.gps']
    df2 = df[['latitude', 'longitude']].values
    K_clusters = range(1, min(k_max, len(df)))
    kmeans = [KMeans(n_clusters=i) for i in K_clusters]

    # Determine number of clusters to score.
    score = [kmeans[i].fit(df2).score(df2) for i in range(len(kmeans))]
    for i in range(len(score)):
        if i == len(score) - 1:
            k = i +1
            break
        elif abs(score[i + 1] - score[i] < .01):
            k = i + 1
            break

    # Compute KMeans clusters. 
    kmeans = KMeans(n_clusters=k, init='k-means++')
    kmeans.fit(df2)
    df.loc[:, 'cluster_label'] = kmeans.fit_predict(df2)
    centers = kmeans.cluster_centers_ 

    return centers, df
