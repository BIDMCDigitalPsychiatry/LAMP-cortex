from ..feature_types import raw_feature
import LAMP

@raw_feature(
    name="lamp.gps",
    dependencies=["lamp.gps", "lamp.gps.contextual"]
)
def gps(resolution=None, **kwargs):
    """
    Get all GPS data bounded by time interval and optionally subsample the data.

    :param resolution (int): The subsampling resolution (TODO).
    :return timestamp (int): The UTC timestamp for the GPS event.
    :return latitude (float): The latitude for the GPS event.
    :return longitude (float): The longitude for the GPS event.
    :return altitude (float): The altitude for the GPS event.
    :return accuracy (float): The accuracy (in meters) for the GPS event.
    """

    data = LAMP.SensorEvent.all_by_participant(
        kwargs['id'],
        origin="lamp.gps",
        _from= kwargs['start'],
        to= kwargs['end'],
        _limit=2147483647 # INT_MAX
    )['data']
    return [{'timestamp': x['timestamp'], **x['data']} for x in data]
