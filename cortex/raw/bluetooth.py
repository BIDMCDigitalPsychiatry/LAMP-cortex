from ..feature_types import raw_feature
import LAMP


@raw_feature(
    name="lamp.bluetooth",
    dependencies=["lamp.bluetooth"]
)
def bluetooth(resolution=None, limit=20000, cache=True, recursive=True, **kwargs):
    """
    Get all bluetooth data bounded by time interval and optionally subsample the data.

    :param resolution (int): The subsampling resolution (TODO).
    :param limit (int): The maximum number of Bluetooth events to query for (defaults to INT_MAX).
    :return timestamp (int): The UTC timestamp for the Bluetooth event.
    :return bt_rssi (int): The rssi for the Bluetooth event.
    :return bt_address (str): Address of Bluetooth event
    """

    data = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                               origin="lamp.bluetooth",
                                               _from=kwargs['start'],
                                               to=kwargs['end'],
                                               _limit=limit)['data']
    while data and recursive:
        to = data[-1]['timestamp']
        data_next = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                                        origin="lamp.bluetooth",
                                                        _from=kwargs['start'],
                                                        to=to,
                                                        _limit=limit)['data']
        if not data_next: break
        if data_next[-1]['timestamp'] == to: break
        data += data_next

    return [{'timestamp': x['timestamp'], **x['data']} for x in data]
