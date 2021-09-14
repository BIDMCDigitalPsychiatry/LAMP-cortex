""" Module to compute hometime from primary feature signficant locations """
from ..feature_types import secondary_feature
from ..primary.significant_locations import significant_locations

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.hometime',
    dependencies=[significant_locations]
)
def hometime(**kwargs):
    """ Compute the time spent in the most visited location in ms.
    """
    _significant_locations = significant_locations(id=kwargs['id'],
                                                   start=kwargs['start'],
                                                   end=kwargs['end'])
    if len(_significant_locations['data']) == 0:
        _hometime = None
    else:
        _hometime = [loc['duration'] for loc in _significant_locations['data']
                     if loc['rank'] == 0][0]
    return {'timestamp': kwargs['start'], 'value': _hometime}
