""" Module for raw feature spatial_span """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.spatial_span",
    dependencies=["lamp.spatial_span"]
)
def spatial_span(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    """ Get spatial_span data bounded by time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the spatial_span event.
        duration (int): the duration in ms
        activity (str): the activity id
        static_data (dict): a dict which includes game information
        temporal_slices (list): list of dicts which include the 'duration',
                'item', 'level', 'status', and 'value' for each attempt
    """
    return
