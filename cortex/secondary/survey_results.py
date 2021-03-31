from ..feature_types import secondary_feature, log
from ..primary.survey_scores import survey_scores
import numpy as np

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

    all_scores=survey_scores(**kwargs)['data']
    data={}
    for survey in all_scores:
        data[survey]=np.nanmean([s['score'] for s in all_scores[survey]])
    return {'timestamp':kwargs['start'],
            'duration':kwargs['end']-kwargs['start'],   
            **data}   