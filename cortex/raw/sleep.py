""" Module for raw feature sleep """
from ..feature_types import raw_feature


@raw_feature(
    name="lamp.sleep",
    dependencies=["lamp.sleep"]
)
def sleep(_limit=10000,
          cache=False,
          recursive=False,
          **kwargs):
    """ Get all Healthkit sleep data bounded by time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the sleep event.
        value (int): The sleep data.

    Example:
         [{'timestamp': 1639056600436, 'value': 0,
         'source': 'com.apple.health.2D434BA3-4071-48C5-92BD-3598288D58A1',
         'representation': 'in_bed', 'duration': 23987436.727046967},
         {'timestamp': 1638970235252, 'value': 0,
         'source': 'com.apple.health.2D434BA3-4071-48C5-92BD-3598288D58A1',
         'representation': 'in_bed', 'duration': 3252.686023712158},
         {'timestamp': 1638970228000, 'value': 0,
         'source': 'com.apple.health.2D434BA3-4071-48C5-92BD-3598288D58A1',
         'representation': 'in_bed', 'duration': 23767000}]
    """
    return
