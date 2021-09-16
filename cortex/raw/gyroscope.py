from ..feature_types import raw_feature, log
import LAMP


@raw_feature(
    name="lamp.gyroscope",
    dependencies=["lamp.gyroscope"]
)
def gyroscope(_limit=10000, 
              cache=False, 
              recursive=True, 
              **kwargs):
    """
    Get all gyroscope data bounded by time interval
    
    :param _limit (int): The maximum number of sensor events to query for in a single request
    :param cache (bool): Indicates whether to save raw data locally in cache dir
    :param recursive (bool): if True, continue requesting data until all data is returned; else just one request
    
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