""" Module for call_degree from raw feature telephony """
import numpy as np

from ..feature_types import secondary_feature
from ..raw.telephony import telephony

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_degree',
    dependencies=[telephony]
)
def call_degree(call_direction='all', **kwargs):
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
    _calls = telephony(**kwargs)['data']
    # if no data, return none
    if len(_calls) == 0:
        _call_degree = None
    # if there is data, but not of the specified type, return 0
    elif call_direction not in ['incoming', 'outgoing', 'all']:
        raise Exception(f"{call_direction} is not a proper argument. "
                        + "Must be incoming, outgoing, or all")
    elif call_direction == 'all':
        _call_degree = np.unique([call['trace'] for call in _calls]).size
    else:
        _call_degree = np.unique([call['trace'] for call in _calls
                                  if call['type'] == call_direction]).size
    return {'timestamp': kwargs['start'], 'value': _call_degree}
