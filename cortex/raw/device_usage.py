""" Module for raw feature device_usage """
from ..feature_types import raw_feature

@raw_feature(
    name="com.apple.sensorkit.device_usage",
    dependencies=["com.apple.sensorkit.device_usage"]
)
def device_usage(_limit=10000,
                  cache=False,
                  recursive=True,
                  **kwargs):
    """ Get all device usage data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the accelerometer event.
        totalScreenWakes (int): Total number of times the screen wakes up.
        totalUnlockDuration (int): Total amount of time the phone is unlocked (seconds).
        totalUnlocks (int): Total number of times the phone is unlocked.
        duration (int): Duration of which the report spans (seconds).

    Example:
        [{'timestamp': 1666494900006,
          'totalScreenWakes': 7,
          'totalUnlockDuration': 298,
          'duration': 900,
          'totalUnlocks': 5},
         {'timestamp': 1666494900206,
          'totalUnlockDuration': 298,
          'duration': 900,
          'totalScreenWakes': 6,
          'totalUnlocks': 6},
         {'timestamp': 1666494000406,
          'totalScreenWakes': 0,
          'duration': 900,
          'totalUnlocks': 0,
          'totalUnlockDuration': 0}]
    """
    return
