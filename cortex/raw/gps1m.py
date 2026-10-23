""" Module for raw feature gps1m """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.gps1m",
    dependencies=["lamp.gps1m"]
)
def gps1m(_limit=10000,
          cache=False,
          recursive=True,
          **kwargs):
    """ Get all one-fix-per-minute GPS data bounded by time interval.

    `lamp.gps1m` is a separate sensor from `lamp.gps`: the device requests one
    high-accuracy fix every 60 seconds (a target, not a guarantee). Each event
    has the same data shape as `lamp.gps`.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the GPS event.
        latitude (float): The latitude for the GPS event.
        longitude (float): The longitude for the GPS event.
        altitude (float): The altitude for the GPS event.
        accuracy (float): The accuracy (in meters) for the GPS event.
    Example:
        [{'timestamp': 1790000220000,
           'latitude': 42.3389,
           'longitude': -71.1066,
           'altitude': 12.5,
           'accuracy': 4.8},
         {'timestamp': 1790000160000,
           'latitude': 42.3390,
           'longitude': -71.1064,
           'altitude': 12.1,
           'accuracy': 5.2},]
    """
    return
