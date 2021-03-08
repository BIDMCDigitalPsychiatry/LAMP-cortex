import primary 


SENSORS = ['lamp.gps']
def trips(participant_id):
    attachment_key = "cortex.feature.trips"

    primary(participant_id, attachment_key, process_fn=process_trips) 

def process_trips(sensor_data):
    """
    Create primary features
    """
    return trips 