""" Module for text_number from raw feature messages_usage """
import numpy as np
from ..feature_types import secondary_feature, log
from ..raw.messages_usage import messages_usage

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.text_number',
    dependencies=[messages_usage]
)
def text_number(text_direction="all", **kwargs):
    """Returns the number of texts made.

    Args:
        text_direction (string): Returns all texts if "all",
            returns received texts if "incoming", returns
            sent texts if "outgoing".
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window
                for which the feature is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window
                for which the feature is being generated. Required.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window
            (same as kwargs['start']).
            value (float): The number of texts.
    """
    _texts = messages_usage(**kwargs)['data']

    incoming_text_count = np.sum(text['totalIncomingMessages'] for text in _texts)
    outgoing_text_count = np.sum(text['totalOutgoingMessages'] for text in _texts)
    
    if len(_texts) == 0:
        number = None
        return {'timestamp': kwargs['start'], 'value': number}
    elif text_direction == "all":
        number = incoming_text_count + outgoing_text_count
    elif text_direction == "incoming":
        number = incoming_text_count
    elif text_direction == "outgoing":
        number = outgoing_text_count
    else:
        number = None
        raise Exception(f"{text_direction} is not a proper argument. "
                        + "Must be incoming, outgoing, or all")

    return {'timestamp': kwargs['start'], 'value': number}
