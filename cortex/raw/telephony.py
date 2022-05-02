""" Module for raw feature telephony """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.telephony",
    dependencies=["lamp.telephony"]
)
def telephony(_limit=10000,
        cache=False,
        recursive=True,
        **kwargs):
    """ Get all telephony data bounded by time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request
    Returns:
        timestamp (int): The UTC timestamp for the sms event.
    """
    return
