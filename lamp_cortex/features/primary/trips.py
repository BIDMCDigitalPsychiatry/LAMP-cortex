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
    sensor_data = kwargs['sensor_data']

    if 'lamp.gps' not in sensor_data:
        return {}

    gps_data = sensor_data['lamp.gps']
    labeled_gps = lamp_cortex.sensors.gps.label_gps_points(gps_data)
    trip_dict = lamp_cortex.sensors.gps.get_trips(labeled_gps)
    return trip_dict