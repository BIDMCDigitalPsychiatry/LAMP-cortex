""" Module for raw feature ambient light """
from ..feature_types import raw_feature

@raw_feature(
    name="com.apple.sensorkit.ambient_light",
    dependencies=["com.apple.sensorkit.ambient_light"]
)
def ambient_light(_limit=10000,
                  cache=False,
                  recursive=True,
                  **kwargs):
    """ Get all ambient light data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the accelerometer event.
        placement (int): An integer representation of the position of the light source relative to the phone.
        chromaticity (dict): A dictionary containing an x, y pair describing hue and colorfulness of the light source.
        lux (dict): A dictionary describing the luminous flux (perceived power of observed light per unit time) 
            per unit area, in units of lux (lx).

    Example:
        [{'timestamp': 1666528657228,
            'placement': 1,
            'chromaticity': {'x': 0.4228740930557251, 'y': 0.35222673416137695},
            'lux': {'value': 0,
                    'unit': {'converter': {'coefficient': 1, 'constant': 0}, 
                    'symbol': 'lx'}}},
        {'timestamp': 1666528656036,
            'placement': 1,
            'lux': {'value': 0,
                    'unit': {'converter': {'coefficient': 1, 'constant': 0}, 
                    'symbol': 'lx'}},
            'chromaticity': {'x': 0.38883176445961, 'y': 0.382804811000824}},
        {'timestamp': 1666528654423,
            'placement': 1,
            'chromaticity': {'x': 0.37757551670074463, 'y': 0.36116909980773926},
            'lux': {'value': 0,
                    'unit': {'converter': {'coefficient': 1, 'constant': 0},
                    'symbol': 'lx'}}}]
    """
    return
