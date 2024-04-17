""" Module for obtaining application usage data """
import numpy as np
import pandas as pd
from ..feature_types import secondary_feature, log
from ..raw.device_usage import device_usage
from .. import raw

@secondary_feature(
    name="cortex.app_time",
    dependencies=[device_usage]
)
def app_time(category="all", attach=False, **kwargs):
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
    
    category_map = {"books": "SRDeviceUsageCategoryBooks", 
                    "business": "SRDeviceUsageCategoryBusiness",
                    "catalogs": "SRDeviceUsageCategoryCatalogs",
                    "developer": "SRDeviceUsageCategoryDeveloperTools",
                    "education": "SRDeviceUsageCategoryEducation",
                    "entertainment": "SRDeviceUsageCategoryEntertainment", 
                    "finance": "SRDeviceUsageCategoryFinance",
                    "dining": "SRDeviceUsageCategoryFoodAndDrink",
                    "games": "SRDeviceUsageCategoryGames",
                    "design": "SRDeviceUsageCategoryGraphicsAndDesign",
                    "health": "SRDeviceUsageCategoryHealthAndFitness",
                    "kids": "SRDeviceUsageCategoryKids",
                    "lifestyle": "SRDeviceUsageCategoryLifestyle",
                    "medical": "SRDeviceUsageCategoryMedical",
                    "misc": "SRDeviceUsageCategoryMiscellaneous",
                    "music": "SRDeviceUsageCategoryMusic",
                    "navigation": "SRDeviceUsageCategoryNavigation",
                    "news": "SRDeviceUsageCategoryNews",
                    "applenews": "SRDeviceUsageCategoryNewsstand",
                    "photo_video": "SRDeviceUsageCategoryPhotoAndVideo",
                    "productivity": "SRDeviceUsageCategoryProductivity",
                    "reference": "SRDeviceUsageCategoryReference",
                    "shopping": "SRDeviceUsageCategoryShopping",
                    "social": "SRDeviceUsageCategorySocialNetworking",
                    "sports": "SRDeviceUsageCategorySports",
                    "stickers": "SRDeviceUsageCategoryStickers",
                    "travel": "SRDeviceUsageCategoryTravel",
                    "utilities": "SRDeviceUsageCategoryUtilities",
                    "weather": "SRDeviceUsageCategoryWeather"}
    
    if category != "all" and category not in category_map.keys():
        raise Exception("Please specify the argument 'category' as either 'all' or one of: %s" % list(category_map.keys()))
    
    _device_usage = device_usage(**kwargs)['data']
    
    if len(_device_usage) == 0:
        return {'timestamp': kwargs['start'], 'value': None}
        
    app_usage = [f['applicationUsageByCategory'] for f in _device_usage
                 if len(f['applicationUsageByCategory']) > 0]
    
    if category == 'all':
        type_usage = [f[j] for f in app_usage for j in category_map.values() if j in f.keys()]
    else:
        category_id = category_map[category]
        type_usage = [f[category_id] for f in app_usage if category_id in f.keys()]
    
    value = np.sum(dur['usageTime'] for f in type_usage for dur in f)
    
    # After this time, data was reported in ms, not s. Change the unit from s to ms if data was collected before this time.
    cutoff_time = 1677088485*1000
    if kwargs['end'] <= cutoff_time:
        value *= 1000
    
    return {'timestamp': kwargs['start'], 'value': value}
