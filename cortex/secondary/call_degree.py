""" Module for call_degree from raw features telephony and Apple SensorKit """
import numpy as np

from ..feature_types import secondary_feature
from ..raw.telephony import telephony
from ..raw.phone_usage import phone_usage

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_degree',
    dependencies=[telephony, phone_usage]
)
def call_degree(sensor='Telephony', call_direction='all', **kwargs):
    """Returns the number of unique phone numbers a participant called

    Args:
        sensor (string): Which call data source to use. Options are SensorKit for Apple Sensorkit or 
            Telephony
        call_direction (string): [Telephony Only] If "incoming" the duration of received calls
            is returned; if "outgoing" the duration of sent calls is returned;
            if "all" the duration of all calls is returned.
            Default parameter is "all".
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The number of unique phone numbers.
    """
    if sensor == 'Telephony':
        _calls = telephony(**kwargs)['data']
        # if no data, return none
        if len(_calls) == 0:
            _call_degree = None
        # if there is data, but not of the specified type, return 0
        elif call_direction not in ['incoming', 'outgoing', 'all']:
            raise Exception(f"{call_direction} is not a proper argument. "
                            + "Must be incoming, outgoing, or all")
        elif call_direction == 'all':
            _call_degree = np.unique([call['trace'] for call in _calls]).size
        else:
            _call_degree = np.unique([call['trace'] for call in _calls
                                      if call['type'] == call_direction]).size
        return {'timestamp': kwargs['start'], 'value': _call_degree}
    elif sensor == 'SensorKit':
        _calls = phone_usage(**kwargs)['data']

        if len(_calls) == 0:
            _call_degree = None
        else:
            _call_degree = np.sum(call['totalUniqueContacts'] for call in _calls)
        return {'timestamp': kwargs['start'], 'value': _call_degree}
    else:
        raise Exception(f"{sensor} is not a proper sensor value. "
                            + "Must be SensorKit or Telephony")