""" Module for call_number from raw feature calls """
from ..feature_types import secondary_feature
from ..raw.calls import calls

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_number',
    dependencies=[calls]
)
def call_number(incoming=True, **kwargs):
    """Returns the number of calls made.

    Args:
        incoming (boolean): If True the number of received calls is returned;
            else the number of sent calls is returned.
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The number of calls.
    """
    incoming_dict = {True: 1, False: 2}
    label = incoming_dict[incoming]
    _calls = calls(**kwargs)['data']
    _call_number = len([call for call in _calls if call['call_type'] == label])
    return {'timestamp':kwargs['start'], 'value': _call_number}
