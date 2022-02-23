""" Module to compute step count from raw feature steps """
import pandas as pd

from ..feature_types import secondary_feature
from ..raw.steps import steps
from ..raw.analytics import analytics

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.step_count',
    dependencies=[steps, analytics]
)
def step_count(**kwargs):
    """Number of steps.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The number of steps.
    """
    _steps = steps(**kwargs)['data']
    if len(_steps) == 0:
        return {'timestamp': kwargs['start'], 'value': None}
    _steps = pd.DataFrame(_steps)

    # get device type
    _analytics = analytics(**kwargs)
    _device_types = [_event['device_type'] for _event in _analytics['data']
                     if 'device_type' in _event]
    _device_type = 'iOS' # default to ios

    for device in _device_types:
        if device not in ['iOS', 'Android']: # ignore non-smartphone reads
            continue
        _device_type = device
        break

    if len(_device_types) == 0:
        if "source" in _steps and len(_steps[_steps["source"] == "com.google.android.gms"]) > 0:
            _device_type = "Android"

    if _device_type == "iOS":
        if "unit" in _steps:
            _steps = _steps[_steps["unit"] == "count"]
            _steps = _steps.rename(columns={"value": "steps"})
        else:
            return {'timestamp': kwargs['start'], 'value': None}

    # Remove duplicates
    _steps = _steps[_steps['timestamp'] != _steps['timestamp'].shift()]

    return {'timestamp': kwargs['start'], 'value': _steps["steps"].sum()}
