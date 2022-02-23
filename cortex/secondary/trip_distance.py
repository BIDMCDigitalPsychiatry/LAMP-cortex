""" Module for trip distance from primary feature trips """
from ..primary.trips import trips
from ..feature_types import secondary_feature, log

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.trip_distance',
    dependencies=[trips]
)
def trip_distance(**kwargs):
    """Compute the distance of user trips (in km).

    The (kwargs['start'], kwargs['end']) timestamps used within the function are
    different than the ones that should be passed in as parameters --
    'cortex.feature_types.secondary_features' is being called first. Please
    see documentation there for more detail.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.

    Returns:
        A dict consisting of:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The distance (in km) the user spent taveling in the interval
                [kwargs['start'], kwargs['end']].

    """
    log.info('Loading Trips data...')
    _trips = trips(**kwargs)
    if _trips['has_raw_data'] == 0:
        return {'timestamp': kwargs['start'], 'trip_distance': None}
    _trips = _trips["data"]
    log.info('Computing Trip Distance...')
    _distance = sum([trip['distance'] for trip in _trips])
    return {'timestamp': kwargs['start'], 'value': _distance}
