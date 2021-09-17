""" Module for raw feature bluetooth """
import LAMP
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.bluetooth",
    dependencies=["lamp.bluetooth"]
)
def bluetooth(_limit=10000, 
              cache=False, 
              recursive=True, 
              **kwargs):
    """
    Get all bluetooth data bounded by time interval and optionally subsample the data.

    :param _limit (int): The maximum number of sensor events to query for in a single request
    :param cache (bool): Indicates whether to save raw data locally in cache dir
    :param recursive (bool): if True, continue requesting data until all data is returned; else just one request
    
    :return timestamp (int): The UTC timestamp for the Bluetooth event.
    :return bt_rssi (int): The rssi for the Bluetooth event.
    :return bt_address (str): Address of Bluetooth event
    """

    data = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                               origin="lamp.bluetooth",
                                               _from=kwargs['start'],
                                               to=kwargs['end'],
                                               _limit=_limit)['data']
    while data and recursive:
        to = data[-1]['timestamp']
        data_next = LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                                        origin="lamp.bluetooth",
                                                        _from=kwargs['start'],
                                                        to=to,
                                                        _limit=_limit)['data']
        if not data_next or data_next[-1]['timestamp'] == to:
            break
        data += data_next

    return [{'timestamp': x['timestamp'], **x['data']} for x in data]
