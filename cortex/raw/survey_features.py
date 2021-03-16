import datetime 
import pandas as pd 
import numpy as np
from functools import reduce

def survey_score(survey, dates, resolution, date_key='local_datetime'):#df, day_first, day_last):
    """
    Convert survey scores into dense representation ("df")
    
    :param surveys
    :param df
    :param day_first
    :param day_last
    """
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
    """
    Features all surveys
    """
    survey_df_list = [survey_score(surveys[s], dates, resolution).rename({'score':'.'.join([s, 'score'])}) for s in surveys] 
    allDfs = reduce(lambda left, right: pd.merge(left, right, on=["Date"], how='left'), survey_df_list)
    return allDfs