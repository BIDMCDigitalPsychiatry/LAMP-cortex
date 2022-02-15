""" Module sms_number from raw feature sms """
from ..feature_types import secondary_feature
from ..raw.sms import sms

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.sms_number',
    dependencies=[sms]
)
def sms_number(incoming=True, **kwargs):
    """Compute the number of texts sent or received.


    The (kwargs['start'], kwargs['end']) timestamps used within the function are
    different than the ones that should be passed in as parameters --
    'cortex.feature_types.secondary_features' is being called first. Please
    see documentation there for more detail.

    Args:
        incoming (boolean): If True the number of received texts is returned;
            else the number of sent texts is returned.
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.

    Returns:
        A dict consisting of:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (int): The number of texts made in state 'incoming'.

    """
    incoming_dict = {True: 1, False:2}
    label = incoming_dict[incoming]
    _sms = sms(**kwargs)['data']
    _sms_number = len([sms for sms in _sms if sms['sms_type'] == label])
    return {'timestamp':kwargs['start'], 'value': _sms_number}
