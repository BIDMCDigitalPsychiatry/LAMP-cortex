from ..feature_types import secondary_feature
from ..primary.survey_scores import survey_scores
import numpy as np
import pandas as pd

@secondary_feature(
    name="cortex.survey_results",
    dependencies=[survey_scores]
)
def survey_results(category, **kwargs):
    """ Returns the survey scores binned by resolution for a
        certain survey category.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for
                which the feature is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for
                which the feature is being generated. Required.
        category (str): The category to bin scores. SHould be in scoring_dict.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The average score for this category.
    """
    all_scores = pd.DataFrame(survey_scores(**kwargs)['data'])
    survey_avg = None
    if len(all_scores) > 0:
        survey_avg = all_scores[all_scores["category"] == category]["score"].mean()
    return {'timestamp': kwargs['start'], 'value': survey_avg}