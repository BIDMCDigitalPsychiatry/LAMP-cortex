""" Module to compute call duration from raw feature calls """
import numpy as np

from ..feature_types import secondary_feature, log
from ..raw.calls import calls

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_duration',
    dependencies=[calls]
)
def call_duration(incoming=True, **kwargs):
    """ Time spent talking on the phone.
    """
    incoming_dict = {True: 1, False: 2}
    label = incoming_dict[incoming]
    log.info('Loading raw calls data...')
    _calls = calls(id=kwargs['id'], start=kwargs['start'],
                   end=kwargs['end'])['data']
    log.info('Computing call duration...')
    _call_duration = np.sum([call['call_duration'] for call in _calls
                             if call['call_type'] == label])
    # if you have no call duration, this means you have no call data
    # over the period, should return None
    if _call_duration == 0:
        _call_duration = None
    return {'timestamp': kwargs['start'], 'value': _call_duration}
