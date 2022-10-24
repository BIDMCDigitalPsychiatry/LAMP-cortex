""" Module for raw feature visits """
from ..feature_types import raw_feature

@raw_feature(
    name="com.apple.sensorkit.visits",
    dependencies=["com.apple.sensorkit.visits"]
)
def visits(_limit=10000,
                  cache=False,
                  recursive=True,
                  **kwargs):
    """ Get all visits data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the accelerometer event.
        distanceFromHome (float): Distance of location from home (meters).
        locationCategory (int): The type of location visited.
        depatureDateInterval (dict): The timestamp since 00:00:00 UTC on 1 January 2001 
            and error (seconds, seconds) of the departure time.
        arrivalDateInterval (dict): The UTC timestamp 00:00:00 UTC on 1 January 2001 
            and error (seconds, seconds) of the arrival time.

    Example:
         [{'timestamp': 1666451574083,
           'distanceFromHome': 2748.563657340416,
           'locationCategory': 0,
           'departureDateInterval': {'start': 688072500, 'duration': 900},
           'arrivalDateInterval': {'start': 688092500, 'duration': 900}},
          {'timestamp': 1666451584080,
           'distanceFromHome': 0,
           'arrivalDateInterval': {'start': 688084200, 'duration': 900},
           'locationCategory': 1,
           'departureDateInterval': {'start': 688124200, 'duration': 900}},
          {'timestamp': 1666451594080,
           'locationCategory': 0,
           'distanceFromHome': 2748.563657340416,
           'arrivalDateInterval': {'start': 688072500, 'duration': 900},
           'departureDateInterval': {'start': 688072500, 'duration': 900}}]
    """
    return
