from ..feature_types import secondary_feature, log
from ..primary.significant_locations import significant_locations
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="test_app")
import pandas as pd
import logging

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.geocoded_data',
    dependencies=[significant_locations]
)
def geocoded_data(resolution=MS_IN_A_DAY, **kwargs):
    """
    Find geocoded data (usually contains address, county, etc.) 
    """
    log.info(f'Finding data')
    _significant_locations = significant_locations(id=kwargs['id'], start=kwargs['start'], end=kwargs['end'])
    
    return {'timetamp':kwargs['start'], 'entropy': _entropy}
