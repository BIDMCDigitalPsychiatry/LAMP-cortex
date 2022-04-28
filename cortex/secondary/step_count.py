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
        Warning: Step collection may be cummulative making this feature invalid.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The number of steps.
    """
    _steps = steps(**kwargs)['data']
    if len(_steps) == 0:
        return {'timestamp': kwargs['start'], 'value': None}
    _steps = pd.DataFrame(_steps)

    if "type" not in _steps:
        # Older data, not supported
        return {'timestamp': kwargs['start'], 'value': None}

    _steps = _steps[_steps["type"] == "step_count"]
    if len(_steps) == 0:
        return {'timestamp': kwargs['start'], 'value': None}

    # Remove duplicates
    _steps = _steps[_steps['timestamp'] != _steps['timestamp'].shift()]

    return {'timestamp': kwargs['start'],
            'value': _steps[_steps["type"] == "step_count"]["value"].sum()}
