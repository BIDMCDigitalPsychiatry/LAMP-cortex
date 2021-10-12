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
    """The time (in ms) spent talking on the phone.

    Args:
        incoming (boolean): If True the duration of received calls is returned;
            else the duration of sent calls is returned.
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The time spent in a call.
    """
    incoming_dict = {True: 1, False: 2}
    label = incoming_dict[incoming]
    log.info('Loading raw calls data...')
    _calls = calls(**kwargs)['data']
    log.info('Computing call duration...')
    _call_duration = np.sum([call['call_duration'] for call in _calls
                             if call['call_type'] == label])
    # if you have no call duration, this means you have no call data
    # over the period, should return None
    if _call_duration == 0:
        _call_duration = None
    return {'timestamp': kwargs['start'], 'value': _call_duration}
