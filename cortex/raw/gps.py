""" Module for raw feature gps """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.gps",
    dependencies=["lamp.gps", "lamp.gps.contextual"]
)
def gps(_limit=10000,
        cache=False,
        recursive=True,
        **kwargs):
    """ Get all GPS data bounded by time interval.

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
        [{'timestamp': 1618016071000,
           'altitude': -122.39560237705484,
           'longitude': -110.39560237705484,
           'latitude': 34.22454011010993},
         {'timestamp': 1618016070000,
           'altitude': -122.39560237705484,
           'longitude': -110.39560237705484,
           'latitude': 34.22454011010993},]
    """
    return
