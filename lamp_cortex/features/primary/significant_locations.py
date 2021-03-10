from lamp_cortex.features.primary.primary import primary_feature
import lamp_cortex
import numpy as np

@primary_feature(
    name="cortex.feature.significant_locations"
    dependencies=['lamp.gps']
)
def significant_locations(participant_id):
    """
    Create primary features
    """

    labeled_gps = lamp_cortex.sensors.label_gps_points(sensor_data, gps_sensor='lamp.gps')
    trip_dict = lamp_cortex.sensors.get_trips(labeled_gps)
    return trip_dict