from ..feature_types import secondary_feature, log
from ..primary.significant_locations import significant_locations
import math 

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.entropy',
    dependencies=[significant_locations]
)
def entropy(resolution=MS_IN_A_DAY, **kwargs):
    """
    Calculate entropy
    """
    # log.info(f'Loading significant locations data...')
    if kwargs.get('method') is not None:
        _significant_locations = significant_locations(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'], method=kwargs['method'])
    else:
        _significant_locations = significant_locations(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])

    if len(_significant_locations['data']) == 0:
        _entropy = None
    # log.info(f'Computing entropy...')
    _entropy = -sum([loc['proportion'] * math.log(loc['proportion']) for loc in _significant_locations['data'] if 0 < loc['proportion'] <= 1])
    if _entropy == 0:  # no sig locs
        _entropy = None
    return {'timestamp': kwargs['start'], 'entropy': _entropy}
