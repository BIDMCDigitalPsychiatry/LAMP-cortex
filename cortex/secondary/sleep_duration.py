from ..feature_types import secondary_feature
from ..primary.sleep_periods import sleep_periods

import math 
import pandas as pd
import numpy as np
import datetime
from geopy import distance
from functools import reduce

@secondary_feature(
    name="cortex.feature.sleep_duration",
    dependencies=[sleep_periods]
)
def sleep_duration(**kwargs):
    """Compute the time (in hours) spent sleeping during nightime periods.


    The (kwargs['start'], kwargs['end']) timestamps used within the function are
    different than the ones that should be passed in as parameters --
    'cortex.feature_types.secondary_features' is being called first. Please
    see documentation there for more detail.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.

    Returns:
        A dict consisting of:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The time (in hours) spent sleeping during nightime periods.

    """
    _sleep_periods = sleep_periods(**kwargs)
    _sleep_duration = sum([res['end'] - res['start'] for res in _sleep_periods['data']])
    # if there is no accelerometer data, sleep should be None
    if _sleep_periods['has_raw_data'] == 0:
        _sleep_duration = None
    return {'timestamp':kwargs['start'],
            'value': _sleep_duration}
