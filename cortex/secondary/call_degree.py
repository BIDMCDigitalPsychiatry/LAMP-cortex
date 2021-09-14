from ..feature_types import secondary_feature
from ..raw.calls import calls

import numpy as np

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_degree',
    dependencies=[calls]
)
def call_degree(resolution=MS_IN_A_DAY, **kwargs):
    """
    How many phone numbers you were connecting with
    """
    _calls = calls(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])['data']
    _call_degree = np.unique([call['call_trace'] for call in _calls]).size
    return {'timestamp':kwargs['start'], 'call_degree': _call_degree}