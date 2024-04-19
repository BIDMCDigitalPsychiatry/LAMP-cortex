""" Module for obtaining application usage data """
import numpy as np
import pandas as pd
from ..feature_types import secondary_feature, log
from ..raw.visits import visits
from .. import raw

@secondary_feature(
    name="cortex.visit_time",
    dependencies=[visits]
)
def visit_time(category=None, attach=False, **kwargs):
    """ Get app usage data from raw device_usage.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            category (string): The type of app to collect data on. Required.
    Returns:
        A dict consisting of:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The total time (in ms) spent using each app type.
    """
    category_list = ['gym', 'home', 'school', 'work', 'other']
    if category is None:
        raise Exception("Please specify the argument 'category' as one of: %s" % category_list)
    
    # the raw data uses a category named 'unknown', but 'other' is a more understandable name
    # for this category. so, take an argument option called 'other' then filter the raw data
    # for a category calle 'unknown.'
    if category == 'other':
        category = 'unknown'
        
    _visits = visits(**kwargs)['data']
    
    if len(_visits) == 0:
        return {'timestamp': kwargs['start'], 'value': None}
        
    value = np.sum([(f['departureDateInterval']['start'] - f['arrivalDateInterval']['start']) for f in _visits 
                    if f['locationCategoryRepresentation'] == category])
    
    return {'timestamp': kwargs['start'], 'value': value}
