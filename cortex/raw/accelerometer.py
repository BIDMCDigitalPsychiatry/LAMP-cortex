""" Module for raw feature accelerometer """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.accelerometer",
    dependencies=["lamp.accelerometer"]
)
def accelerometer(_limit=10000,
                  cache=False,
                  recursive=True,
                  **kwargs):
    """ Get all accelerometer data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the accelerometer event.
        x (float): The x component of accelerometer reading.
        y (float): The y component of accelerometer reading.
        z (float): The z component of accelerometer reading.

    Example:
        [{'timestamp': 1618016071621,
           'x': -0.0004425048828125,
           'y': 0.0001678466796875,
           'z': -1.001983642578125},
        {'timestamp': 1618016071421,
           'x': 0.00048828125,
           'y': 0.0020599365234375,
           'z': -1.0025177001953125},
        {'timestamp': 1618016071221,
           'x': -0.000579833984375,
           'y': 0.0006866455078125,
           'z': -1.00311279296875},]
    """
    return
