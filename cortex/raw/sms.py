""" Module for raw feature sms """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.sms",
    dependencies=["lamp.sms"]
)
def sms(_limit=10000,
        cache=False,
        recursive=False,
        **kwargs):
    """ Get all text messaging bounded by time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request
    Returns:
        timestamp (int): The UTC timestamp for the sms event.
    """
    return
