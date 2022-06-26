""" Module for call_number from raw feature calls """
from ..feature_types import secondary_feature, log
from ..raw.telephony import telephony

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_number',
    dependencies=[telephony]
)
def call_number(call_direction="all", **kwargs):
    """Returns the number of calls made.

    Args:
        call_direction (string): Returns all calls if "all",
            returns received calls if "incoming", returns
            sent calls if "outgoing".
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window
                for which the feature is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window
                for which the feature is being generated. Required.
            incoming (boolean): If True the number of received calls
                is returned; else the number of sent calls is returned.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window
            (same as kwargs['start']).
            value (float): The number of calls.
    """
    _calls = telephony(**kwargs)['data']

    incoming = kwargs.get('incoming')

    # optional incoming variable sets call_direction in accordance with
    # previous version of call_number, in which function returned
    # incoming calls if incoming is True, else returned outgoing calls.

    if incoming is not None:
        if incoming is True:
            call_direction = "incoming"
        else:
            call_direction = "outgoing"

    if len(_calls) == 0:
        number = None

    elif call_direction == "all":
        number = len(_calls)

    elif call_direction in ("incoming", "outgoing"):

        group = [calls for calls in _calls if calls['type'] == call_direction]
        number = len(group)

    else:
        number = None
        log.info(""" %s was passed but is not an acceptable argument.
        Acceptable arguments include 'all','incoming', or 'outgoing'" """,
                 call_direction)

    return {'timestamp': kwargs['start'], 'value': number}
