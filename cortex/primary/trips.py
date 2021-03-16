from ..feature_types import primary_feature
from ..raw import gps
import numpy as np
import pandas as pd

@primary_feature(
    name="cortex.feature.trips",
    dependencies=['lamp.gps']
)
def trips(participant_id, **kwargs):
    """
    Create primary features
    """
    df = pd.DataFrame.from_dict(kwargs['sensor_data']['lamp.gps'])
    df = df.drop('data', 1).assign(**df.data.dropna().apply(pd.Series))
    labeled_gps = gps.label_gps_points(df)
    trip_dict = gps.get_trips(labeled_gps)
    return trip_dict
