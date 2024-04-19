""" Module text_degree from raw feature messages_usage """
import numpy as np

from ..feature_types import secondary_feature, log
from ..raw.messages_usage import messages_usage

MS_IN_A_DAY = 86400000


@secondary_feature(
    name='cortex.feature.text_degree',
    dependencies=[messages_usage]
)
def text_degree(**kwargs):
    """The number of unique phone numbers a participant texted.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for
                which the feature is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for
                which the feature is being generated. Required.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as
            kwargs['start']).
            value (float): Number of unique phone numbers texted.
    """
    _texts = messages_usage(**kwargs)['data']
    
    if len(_texts) == 0:
        unique_contacts =  None
        return {'timestamp': kwargs['start'], 'value': unique_contacts} 
    else:
        unique_contacts = np.sum(text['totalUniqueContacts'] for text in _texts)
    
    return {'timestamp': kwargs['start'], 'value': unique_contacts}


