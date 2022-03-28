""" Module for computing average survey scores """
import pandas as pd
from ..feature_types import secondary_feature
from ..primary.survey_scores import survey_scores

@secondary_feature(
    name="cortex.survey_results",
    dependencies=[survey_scores]
)
def survey_results(question_or_category, **kwargs):
    """ Returns the survey scores binned by resolution for a
        certain survey category.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for
                which the feature is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for
                which the feature is being generated. Required.
        question_or_category (str): The category / question to bin scores.
                Should be in scoring_dict.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The average score for this category.
    """
    all_scores = pd.DataFrame(survey_scores(**kwargs)['data'])
    survey_avg = None
    if len(all_scores) > 0:
        survey_avg = all_scores[all_scores["question"] == question_or_category]["score"].mean()
    return {'timestamp': kwargs['start'], 'value': survey_avg}
