""" Module for call_number from raw feature calls """
from ..feature_types import secondary_feature
from ..raw.calls import calls

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_number',
    dependencies=[calls]
)
def call_number(incoming=True, **kwargs):
    """ Returns the number of calls made.
    """
    incoming_dict = {True: 1, False:2}
    label = incoming_dict[incoming]
    _calls = calls(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])['data']
    _call_number = len([call for call in _calls if call['call_type'] == label])
    return {'timestamp':kwargs['start'], 'value': _call_number}
