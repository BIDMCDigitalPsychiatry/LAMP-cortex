""" Module trip_duration from primary feature trips """
from ..primary.trips import trips
from ..feature_types import secondary_feature

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.trip_duration',
    dependencies=[trips]
)
def trip_duration(**kwargs):
    """Compute the duration of user trips (in ms).

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
            value (float): The time (in ms) the user spent taveling in the interval
                [kwargs['start'], kwargs['end']].

    """
    _trips = trips(**kwargs)
    _duration = sum([trip['end'] - trip['start'] for trip in _trips['data']])
    return {'timestamp': kwargs['start'], 'value': _duration}
