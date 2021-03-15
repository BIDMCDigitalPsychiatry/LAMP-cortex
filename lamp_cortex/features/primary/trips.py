from lamp_cortex.features.primary.primary import primary_feature
import lamp_cortex
import numpy as np

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
    labeled_gps = lamp_cortex.sensors.gps.label_gps_points(df)
    trip_dict = lamp_cortex.sensors.gps.get_trips(labeled_gps)
    return trip_dict