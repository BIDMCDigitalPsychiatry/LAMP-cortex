""" Module for raw feature dcog """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.dcog",
    dependencies=["lamp.dcog"]
)
def dcog(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    """ Get dcog data bounded by time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the dcog event.
        duration (int): the duration in ms
        activity (str): the activity id
        static_data (dict): a dict which includes 'correct_answers', 'point', 'total_questions',
                'score', 'wrong_answers'
        temporal_slices (list): list of dicts which include the 'duration',
                'item', 'level', 'status', and 'value' for each round

    """
    return
