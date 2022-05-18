""" Module to compute call duration from raw feature calls """
import numpy as np

from ..feature_types import secondary_feature, log
from ..raw.telephony import telephony

MS_IN_A_DAY = 86400000


@secondary_feature(
    name='cortex.feature.call_duration',
    dependencies=[telephony]
)
def call_duration(call_direction="all", **kwargs):
    """The time (in ms) spent talking on the phone.

    Args:
        call_direction (string): If "incoming" the duration of received calls is returned;
            if "outgoing" the duration of sent calls is returned;
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
            value (float): The time spent in a call.
    """
    _calls = telephony(**kwargs)['data']

    incoming = kwargs.get('incoming')

    # optional incoming variable sets call_direction in accordance with
    # previous version of call_duration, in which function returned
    # incoming calls if incoming is True, else returned outgoing calls.

    if incoming is not None:
        if incoming is True:
            call_direction = "incoming"
        else:
            call_direction = "outgoing"

    if call_direction == "all":
        call_duration = np.sum(call['duration'] for call in _calls)

    elif call_direction == "incoming":
        call_duration = np.sum(call['duration'] for call in _calls 
                               if call['type'] == "incoming")
    elif call_direction == "outgoing":
        call_duration = np.sum(call['duration'] for call in _calls
                               if call['type'] == "outgoing")
    else:
        call_duration = None
        log.info('"' + call_direction + "' was passed but is not an acceptable argument. Acceptable arguments include 'all','incoming', or 'outgoing'")

    # if you have no call duration of any kind, this means you have no call data
    # in this case, return None.

    if np.sum(call['duration'] for call in _calls) == 0:
        call_duration = None
    log.info('Computing call duration ...')

    return {'timestamp': kwargs['start'], 'value': call_duration}
