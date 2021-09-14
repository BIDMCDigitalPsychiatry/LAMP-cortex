""" Module trip_duration from primary feature trips """
from ..primary.trips import trips
from ..feature_types import secondary_feature

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.trip_duration',
    dependencies=[trips]
)
def trip_duration(**kwargs):
    """ Duration of trips in ms
    """
    _trips = trips(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    _duration = sum([trip['end']['timestamp'] - trip['start']['timestamp'] for trip in _trips])
    return {'timestamp': kwargs['start'], 'value': _duration}
