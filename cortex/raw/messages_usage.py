""" Module for raw feature messages usage """
from ..feature_types import raw_feature

@raw_feature(
    name="com.apple.sensorkit.messages_usage",
    dependencies=["com.apple.sensorkit.messages_usage"]
)
def messages_usage(_limit=10000,
                  cache=False,
                  recursive=True,
                  **kwargs):
    """ Get all messages usage data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the accelerometer event.
        duration (int): The duration over which the report spans (seconds).
        totalUniqueContacts (int): Total number of unique contacts over the report span.
        totalIncomingMessages (int): Total number of incoming messages over the report span.
        totalOutgoingMessages (int): Total number of outgoing messages over the report span.

    Example:
        [{'timestamp': 1666494000034,
           'duration': 1800,
           'totalUniqueContacts': 2,
           'totalIncomingMessages': 0,
           'totalOutgoingMessages': 5},
         {'timestamp': 1666494000234,
           'duration': 1800,
           'totalUniqueContacts': 1,
           'totalIncomingMessages': 0,
           'totalOutgoingMessages': 1},
         {'timestamp': 1666494000428,
           'duration': 1800,
           'totalUniqueContacts': 3,
           'totalIncomingMessages': 0,
           'totalOutgoingMessages': 8}]
    """
    return
