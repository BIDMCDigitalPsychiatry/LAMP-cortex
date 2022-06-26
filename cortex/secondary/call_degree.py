""" Module for call_degree from raw feature calls """
import numpy as np
import logging
import pdb
from ..feature_types import secondary_feature
from ..raw.telephony import telephony

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_degree',
    dependencies=[telephony]
)

def call_degree(call_direction = 'incoming',**kwargs):
    """Returns the number of unique phone numbers a participant called
    Args:
        call_direction: string that is "incoming" or "outgoing" or "all"
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
    temp_calls = telephony(**kwargs)['data']

    _call_output = []
    
    if not temp_calls:
        
            return {'timestamp':kwargs['start'], 'value': None}
        
    else:
        
        for temp_dat in temp_calls:

            if call_direction == 'incoming':
                if temp_dat['type'] == call_direction:
                    _call_output.append(temp_dat)

            elif call_direction == "outgoing":
                if temp_dat['type'] == call_direction:
                    _call_output.append(temp_dat)

            elif call_direction == "all":
                _call_output.append(temp_dat)
            
            elif isinstance(call_direction, bool):
                if call_direction == True: 
                    if temp_dat['type'] == 'incoming':
                        _call_output.append(temp_dat)      
                else:
                    if temp_dat['type'] == 'outgoing':
                        _call_output.append(temp_dat)      
                
            else:
                logging.warning("call_direction can be incoming, outgoing, or all")

        _call_degree = np.unique([call['trace'] for call in _call_output]).size

        return {'timestamp':kwargs['start'], 'value': _call_degree}
