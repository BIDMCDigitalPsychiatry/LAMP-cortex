""" Module for call_degree from raw feature calls """
import numpy as np
from ..feature_types import secondary_feature
from ..raw.telephony import telephony

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_degree',
    dependencies=[telephony]
)

def call_degree(call_type,**kwargs):
    """Returns the number of unique phone numbers a participant called
    Args:
        call_type: string that is "incoming" or "outgoing" or "all"
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
    temptemp = telephony(**kwargs)
    temp_calls = temptemp['data']

    _call_output = []

    for temp_dat in temp_calls:
        if call_type == 'incoming':
            if temp_dat['type'] == call_type:
                _call_output.append(temp_dat)

        elif call_type == "outgoing":
            if temp_dat['type'] == call_type:
                _call_output.append(temp_dat)

        elif call_type == "all":
            if temp_dat['type'] == call_type:
                _call_output.append(temp_dat)

    _call_degree = np.unique([call['trace'] for call in _call_output]).size

    return {'timestamp':kwargs['start'], 'value': _call_degree}
