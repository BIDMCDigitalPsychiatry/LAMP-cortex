""" Module for call_degree from raw feature calls """
import numpy as np

from ..feature_types import secondary_feature
from ..raw.calls import calls

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_degree',
    dependencies=[calls]
)
def call_degree(**kwargs):
    """Returns the number of unique phone numbers a participant called

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
            value (float): The number of unique phone numbers.
    """
    _calls = calls(**kwargs)['data']
    _call_degree = np.unique([call['call_trace'] for call in _calls]).size
    return {'timestamp':kwargs['start'], 'value': _call_degree}
