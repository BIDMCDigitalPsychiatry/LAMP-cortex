from ..feature_types import secondary_feature
from ..primary.screen_active import screen_active

import numpy as np

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.screen_duration',
    dependencies=[screen_active]
)
def screen_duration(resolution=MS_IN_A_DAY, **kwargs):
    """
    Screen active time
    """
    _screen_active = screen_active(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    _screen_duration = np.sum([active_bout['duration'] for active_bout in _screen_active['data']])
    return {'timestamp':kwargs['start'], 'screen_duration': _screen_duration}