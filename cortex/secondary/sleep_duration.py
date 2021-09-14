from ..feature_types import secondary_feature, log
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
    _sleep_periods = sleep_periods(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    #_sleep_duration = sum([res['duration'] for res in _sleep_periods['data']])
    _sleep_duration = sum([res['end'] - res['start'] for res in _sleep_periods['data']])
    # if there is no accelerometer data, sleep should be None
    if _sleep_periods['has_raw_data'] == 0:
        _sleep_duration = None
    return {'timestamp':kwargs['start'],
            'value': _sleep_duration}
