""" Module for raw feature gyroscope """
import LAMP
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.gyroscope",
    dependencies=["lamp.gyroscope"]
)
def gyroscope(_limit=10000,
              cache=False,
              recursive=True,
              **kwargs):
    """ Get all gyroscope data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the gyroscope event.
        x (float): The x component of gyroscope reading.
        y (float): The y component of gyroscope reading.
        z (float): The z component of gyroscope reading.
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
        if not data_next or data_next[-1]['timestamp'] == to:
            break
        data += data_next
    return [{'timestamp': int(x['timestamp']), **x['data']} for x in data]
