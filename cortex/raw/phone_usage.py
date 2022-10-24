""" Module for raw feature phone usage """
from ..feature_types import raw_feature

@raw_feature(
    name="com.apple.sensorkit.phone_usage",
    dependencies=["com.apple.sensorkit.phone_usage"]
)
def phone_usage(_limit=10000,
                  cache=False,
                  recursive=True,
                  **kwargs):
    """ Get all phone usage data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the accelerometer event.
        duration (int): The duration over which the report spans (seconds)
        totalUniqueContacts (int): Total number of unique contacts over the report span.
        totalIncomingCalls (int): Total number of incoming calls over the report span.
        totalOutgoingCalls (int): Total number of outgoing calls over the report span.
        totalPhoneCallDuration (float): Total phone call duration (seconds).

    Example:
         [{'timestamp': 1666411200036,
           'totalIncomingCalls': 0,
           'totalOutgoingCalls': 4,
           'duration': 86400,
           'totalPhoneCallDuration': 39.51534700393677,
           'totalUniqueContacts': 1},
          {'timestamp': 1666411200033,
           'totalPhoneCallDuration': 39.51534700393677,
           'totalIncomingCalls': 0,
           'duration': 86400,
           'totalOutgoingCalls': 4,
           'totalUniqueContacts': 1},
          {'timestamp': 1666411200031,
           'totalPhoneCallDuration': 39.51534700393677,
           'totalUniqueContacts': 1,
           'totalOutgoingCalls': 4,
           'totalIncomingCalls': 0,
           'duration': 86400}]
    """
    return
