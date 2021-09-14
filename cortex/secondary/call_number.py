from ..feature_types import secondary_feature
from ..raw.calls import calls

import numpy as np

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_number',
    dependencies=[calls]
)
def call_number(resolution=MS_IN_A_DAY, incoming=True, **kwargs):
    """
    Number of calls made
    """
    INCOMING_DICT = {True: 1, False:2}
    label = INCOMING_DICT[incoming] 
    _calls = calls(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])['data']
    _call_number = len([call for call in _calls if call['call_type'] == label])
    return {'timestamp':kwargs['start'], 'call_number': _call_number}