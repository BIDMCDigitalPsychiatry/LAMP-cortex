""" Module to compute healthkit sleep duration from raw feature sleep """
import pandas as pd

from ..feature_types import secondary_feature, log
from ..raw.sleep import sleep

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.healthkit_sleep_duration',
    dependencies=[sleep]
)
def healthkit_sleep_duration(duration_type="in_bed", **kwargs):
    """Time spent in bed (from healthkit).

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
        duration_type (str): "in_bed", "in_sleep", or "in_awake"

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The time in bed (or asleep or awake) (in ms).
    """
    _sleep = sleep(**kwargs)['data']
    if duration_type not in ["in_bed", "in_sleep", "in_awake"]:
        log.info(f"{duration_type} is not valid. Please choose from in_bed, in_sleep, or in_awake. Returning None.")
        return {'timestamp': kwargs['start'], 'value': None}

    _sleep = [x for x in _sleep if x["representation"] == duration_type]
    if len(_sleep) == 0:
        return {'timestamp': kwargs['start'], 'value': None}

    _sleep = pd.DataFrame(_sleep)
    # Remove duplicates
    _sleep = _sleep[_sleep['timestamp'] != _sleep['timestamp'].shift()]
    return {'timestamp': kwargs['start'], 'value': _sleep["duration"].sum()}
