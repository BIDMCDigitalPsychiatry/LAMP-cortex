from ..primary.trips import trips
from ..feature_types import secondary_feature, log

import datetime

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.trip_distance',
    dependencies=[trips]
)
def trip_distance(resolution=MS_IN_A_DAY, **kwargs):
    '''
    Distance Traveled - Meters
    '''
    log.info(f'Loading Trips data...')
    _trips = trips(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    log.info(f'Computing Trip Distance...')
    _distance = sum([trip['distance'] for trip in _trips])
    return {'distance': _distance}