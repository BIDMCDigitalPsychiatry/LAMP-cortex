from ..feature_types import raw_feature, log
import LAMP
import pandas as pd 
import numpy as np
from functools import reduce

@raw_feature(
    name='lamp.survey',
    dependencies=['lamp.survey']
)
def survey(replace_ids=True, limit=2147483647, **kwargs):
    """
    Get survey events for participant
    
    :param replace_ids (bool): TODO.
    :param limit (int): TODO.
    :return timestamp (int): TODO.
    :return survey (str): TODO.
    :return item (str): TODO.
    :return value (any): TODO.
    :return duration (int): TODO.
    """
    
    # FIXME: This is old code preserved here for use later.
    def survey_score(survey, dates, resolution, date_key='local_datetime'):
        timesSeries = pd.Series(dates)
        time_sel_surveys = survey.apply(lambda row: timesSeries[(timesSeries <= row[date_key]) & ((row[date_key] - timesSeries) < resolution)].max(), axis=1)
        if len(time_sel_surveys) == 0:
            return pd.DataFrame([[d, np.nan] for d in dates], columns=['Date', 'score'])
        survey.loc[:, 'matched_time'] = time_sel_surveys
        survey_data = []
        for d in dates: 
            d_survey = survey.loc[survey['matched_time'] == d, :].reset_index().sort_values(by=date_key)
            survey_data.append([d, d_survey['score'].mean()])
        surveyDf = pd.DataFrame(survey_data, columns=['Date', 'Score'])
        return surveyDf
    def featurize(surveys, dates, resolution):
        survey_df_list = [survey_score(surveys[s], dates, resolution).rename({'score':'.'.join([s, 'score'])}) for s in surveys] 
        allDfs = reduce(lambda left, right: pd.merge(left, right, on=["Date"], how='left'), survey_df_list)
        return allDfs
    
    # Grab the list of surveys and ALL ActivityEvents which are filtered locally.
    # TODO: Once the API Server supports filtering origin by an ActivitySpec, we won't need this. 
    activities = LAMP.Activity.all_by_participant(kwargs['id'])['data']
    surveys = {x['id']: x for x in activities if x['spec'] == 'lamp.survey'}
    raw = LAMP.ActivityEvent.all_by_participant(
        kwargs['id'],
        #origin="lamp.survey", # TODO: not implemented in the backend yet!
        _from= kwargs['start'],
        to= kwargs['end'],
        _limit=limit
    )['data']

    # Unpack the temporal slices and flatten the dict, including the timestamp and survey.
    # Computing a per-event survey score requires a `groupby('timestamp', 'survey')` call.
    return [
        {
            'timestamp': x['timestamp'],
            'survey': surveys[x['activity']]['name'] if replace_ids else x['activity'],
            **y
        }
        for x in raw
        if 'activity' in x
            and x['activity'] in surveys
            and len(x['temporal_slices']) > 0
        for y in x['temporal_slices']
    ]
