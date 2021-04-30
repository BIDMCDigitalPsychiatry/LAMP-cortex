from ..feature_types import secondary_feature
from ..raw.sms import sms

import numpy as np

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.sms_number',
    dependencies=[sms]
)
def sms_number(resolution=MS_IN_A_DAY, incoming=True, **kwargs):
    """
    Number of calls made
    """
    INCOMING_DICT = {True: 1, False:2}
    label = INCOMING_DICT[incoming] 
    _sms = sms(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])['data']
    _sms_number = len([sms for sms in _sms if call['call_type'] == label])
    return {'timestamp':kwargs['start'], 'call_number': _call_number}