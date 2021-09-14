""" Module for screen duration from primary feature screen active """
import numpy as np
from ..feature_types import secondary_feature
from ..primary.screen_active import screen_active

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.screen_duration',
    dependencies=[screen_active]
)
def screen_duration(**kwargs):
    """ Computes screen_duration by summing the screen_active periods over a
        given time.
    """
    _screen_active = screen_active(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    _screen_duration = np.sum([active_bout['duration'] for active_bout in _screen_active['data']])
    # screen duration should be None if there is no data
    if _screen_active['has_raw_data'] == 0:
        _screen_duration = None
    return {'timestamp':kwargs['start'], 'value': _screen_duration}
