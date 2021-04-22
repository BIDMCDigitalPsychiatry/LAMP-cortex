from ..feature_types import secondary_feature, log
from ..raw.calls import calls

import numpy as np

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_duration',
    dependencies=[calls]
)
def call_duration(resolution=MS_IN_A_DAY, incoming=True, **kwargs):
    """
    Time spent talking on the phone
    """
    INCOMING_DICT = {True: 1, False:2}
    label = INCOMING_DICT[incoming] 
    log.info(f'Loading raw calls data...')
    _calls = calls(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])['data']
    log.info(f'Computing call duration...')
    _call_duration = np.sum([call['call_duration'] for call in _calls if call['call_type'] == label])
    return {'timestamp':kwargs['start'], 'call_duration': _call_duration}