""" Module for raw feature cats_and_dogs """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.cats_and_dogs",
    dependencies=["lamp.cats_and_dogs"]
)
def cats_and_dogs(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    """ Get cats_and_dogs data bounded by time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the event.
        duration (int): the duration in ms
        activity (str): the activity id
        static_data (dict): a dict which includes game information
        temporal_slices (list): list of dicts which include the 'duration',
                'item', 'level', 'status', and 'value' for each attempt
    """
    return
