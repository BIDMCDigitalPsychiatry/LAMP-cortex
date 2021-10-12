""" Module for raw feature calls """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.calls",
    dependencies=["lamp.calls"]
)
def calls(_limit=10000,
          cache=False,
          recursive=False,
          **kwargs):
    """ Get all call data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the calls event.
        call_trace (str): the call trace to identify a call.
        call_type (int): incoming = 1; outgoing = 2
        call_duration (int): the duration of the call in seconds

    Example:
        [{'timestamp': 1618007498408,
          'call_trace': '012CEDEB-FC58-4792-B202-412B17C5A34A',
          'call_type': 2,
          'call_duration': 17},
         {'timestamp': 1618002384809,
          'call_trace': 'EDCFF499-E077-4E13-9AD0-5CFB7D9FBE02',
          'call_type': 2,
          'call_duration': 102},]
    """
    return
