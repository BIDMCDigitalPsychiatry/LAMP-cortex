from ..primary.trips import trips
from ..feature_types import secondary_feature

import datetime

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.trip_duration',
    dependencies=[trips]
)
def travel_duration(resolution=MS_IN_A_DAY, **kwargs):
    '''
    Distance Traveled - Meters
    '''
    _trips = trips(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    _duration = sum([trip['end']['timestamp'] - trip['start']['timestamp'] for trip in _trips])
    return {'duration': _duration}