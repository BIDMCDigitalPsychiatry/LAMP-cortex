""" Module for call_degree from raw feature calls """
import numpy as np

from ..feature_types import secondary_feature
from ..raw.calls import calls

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_degree',
    dependencies=[calls]
)
def call_degree(**kwargs):
    """ Returns the number of unique phone numbers a participant called
    """
    _calls = calls(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])['data']
    _call_degree = np.unique([call['call_trace'] for call in _calls]).size
    return {'timestamp':kwargs['start'], 'value': _call_degree}
