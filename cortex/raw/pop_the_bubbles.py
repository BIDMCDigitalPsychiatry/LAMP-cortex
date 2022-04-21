""" Module for raw feature pop_the_bubbles """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.pop_the_bubbles",
    dependencies=["lamp.pop_the_bubbles"]
)
def pop_the_bubbles(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    """ Get pop_the_bubbles data bounded by time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the pop_the_bubbles event.
        duration (int): the duration in ms
        activity (str): the activity id
        static_data (dict): a dict which includes game information
        temporal_slices (list): list of dicts which include the 'duration',
                'item', 'level', 'status', and 'value' for each attempt
    """
    return
