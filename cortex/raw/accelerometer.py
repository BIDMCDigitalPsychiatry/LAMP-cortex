from ..feature_types import raw_feature, log
import LAMP


@raw_feature(
    name="lamp.accelerometer",
    dependencies=["lamp.accelerometer"]
)
def accelerometer(resolution=None, limit=20000, cache=True, recursive=True, **kwargs):
    """
    Get all GPS data bounded by time interval and optionally subsample the data.

    :param resolution (int): The subsampling resolution (TODO).
    :param limit (int): The maximum number of sensor events to query for (defaults to INT_MAX).
    :return timestamp (int): The UTC timestamp for the GPS event.
    :return latitude (float): The latitude for the GPS event.
    :return longitude (float): The longitude for the GPS event.
    :return altitude (float): The altitude for the GPS event.
    :return accuracy (float): The accuracy (in meters) for the GPS event.
    """

    data = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                               origin="lamp.accelerometer",
                                               _from=kwargs['start'],
                                               to=kwargs['end'],
                                               _limit=limit)['data']
    while data and recursive:
        to = data[-1]['timestamp']
        data_next = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                                        origin="lamp.accelerometer",
                                                        _from=kwargs['start'],
                                                        to=to,
                                                        _limit=limit)['data']
        if not data_next: break
        if data_next[-1]['timestamp'] == to: break
        data += data_next
    return [{'timestamp': x['timestamp'], **x['data']} for x in data]
