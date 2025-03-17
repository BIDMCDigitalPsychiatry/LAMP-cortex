""" Module for call_number from raw feature calls """
import numpy as np
from ..feature_types import secondary_feature, log
from ..raw.telephony import telephony
from ..raw.phone_usage import phone_usage

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_number',
    dependencies=[telephony, phone_usage]
)
def call_number(sensor='Telephony', call_direction="all", **kwargs):
    """Returns the number of calls made.

    Args:
        sensor (string): Which call data source to use. Options are SensorKit for Apple Sensorkit or 
            Telephony
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

    # optional incoming variable sets call_direction in accordance with
    # previous version of call_number, in which function returned
    # incoming calls if incoming is True, else returned outgoing calls.
    if sensor == 'Telephony':
        _calls = telephony(**kwargs)['data']

        incoming = kwargs.get('incoming')
    
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
            raise Exception(f"{call_direction} is not a proper argument. "
                            + "Must be incoming, outgoing, or all")

        return {'timestamp': kwargs['start'], 'value': number}
    elif sensor == 'SensorKit':
        _calls = phone_usage(**kwargs)['data']

        incoming_call_count = np.sum(call['totalIncomingCalls'] for call in _calls)
        outgoing_call_count = np.sum(call['totalOutgoingCalls'] for call in _calls)

        if len(_calls) == 0:
            number = None

        elif call_direction == "all":
            number = incoming_call_count + outgoing_call_count

        elif call_direction == "incoming":
            number = incoming_call_count

        elif call_direction == "outgoing":
            number = outgoing_call_count

        else:
            number = None
            raise Exception(f"{call_direction} is not a proper argument. "
                            + "Must be incoming, outgoing, or all")

        return {'timestamp': kwargs['start'], 'value': number}
    else:
        raise Exception(f"{sensor} is not a proper sensor value. "
                            + "Must be SensorKit or Telephony")