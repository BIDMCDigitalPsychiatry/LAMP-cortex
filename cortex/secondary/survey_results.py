from ..feature_types import secondary_feature, log
from ..primary.survey_scores import survey_scores
import numpy as np
import pandas as pd

@secondary_feature(
    name="cortex.survey_results",
    dependencies=[survey_scores]
)
def survey_results(**kwargs):
    """
    :param id (str): participant id.
    :param start (int): start timestamp UTC (ms).
    :param end (int): end timestamp UTC (ms).
    :param resolution (int): time step (ms).
    :return data (dict): TODO.
    """

    all_scores = pd.DataFrame(survey_scores(**kwargs)['data'])
    data = {}
    if len(all_scores) > 0:
        for survey in np.unique(all_scores["category"]):
            data[survey] = all_scores[all_scores["category"] == survey]["score"].mean()
    return {'timestamp': kwargs['start'],
            'duration': kwargs['end'] - kwargs['start'],
            **data}