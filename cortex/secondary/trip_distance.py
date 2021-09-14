""" Module for trip distance from primary feature trips """
from ..primary.trips import trips
from ..feature_types import secondary_feature, log

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.trip_distance',
    dependencies=[trips]
)
def trip_distance(**kwargs):
    '''
    Distance Traveled - Meters
    '''
    log.info('Loading Trips data...')
    _trips = trips(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    if _trips['has_raw_data'] == 0:
        return {'timestamp': kwargs['start'], 'trip_distance': None}
    _trips = _trips["data"]
    log.info('Computing Trip Distance...')
    _distance = sum([trip['distance'] for trip in _trips])
    return {'timestamp': kwargs['start'], 'value': _distance}
