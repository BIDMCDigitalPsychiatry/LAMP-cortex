""" Module sms_number from raw feature sms """
from ..feature_types import secondary_feature
from ..raw.sms import sms

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.sms_number',
    dependencies=[sms]
)
def sms_number(incoming=True, **kwargs):
    """ Number of texts sent or received
    """
    incoming_dict = {True: 1, False:2}
    label = incoming_dict[incoming]
    _sms = sms(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])['data']
    _sms_number = len([sms for sms in _sms if sms['sms_type'] == label])
    return {'timestamp':kwargs['start'], 'value': _sms_number}
