from ..feature_types import raw_feature, log
import LAMP


@raw_feature(
    name="lamp.gyroscope",
    dependencies=["lamp.gyroscope"]
)
def gyroscope(resolution=None, 
              _limit=10000, 
              cache=False, 
              recursive=True, 
              **kwargs):
    """
    Get all gyroscope data bounded by time interval and optionally subsample the data.
    :param resolution (int): The subsampling resolution (TODO).
    :param limit (int): The maximum number of sensor events to query for (defaults to INT_MAX).
    :return timestamp (int): The UTC timestamp for the gyroscope event.
    :return x (float): The x component of gyroscope reading.
    :return y (float): The y component of gyroscope reading.
    :return z (float): The z component of gyroscope reading.
    """

    data = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                               origin="lamp.gyroscope",
                                               _from=kwargs['start'],
                                               to=kwargs['end'],
                                               _limit=_limit)['data']
    while data and recursive:
        to = data[-1]['timestamp']
        data_next = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                                        origin="lamp.gyroscope",
                                                        _from=kwargs['start'],
                                                        to=to,
                                                        _limit=_limit)['data']
        if not data_next: break
        if data_next[-1]['timestamp'] == to: break
        data += data_next
    return [{'timestamp': int(x['timestamp']), **x['data']} for x in data]