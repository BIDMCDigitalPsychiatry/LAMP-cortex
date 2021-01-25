import datetime
import pandas as pd
from functools import reduce


def step_count(data, times, resolution):
    """
    Find number of calls

    :param (str): 
    :param 
    :param label(int): indicates whether or not to query incoming calls (1), outgoing calls (2)
    """
    if 'lamp.steps' not in data:
        return pd.DataFrame({'Date': times, 'Steps': [0] * len(times)})

    step_data = data['lamp.steps'].copy()
    
    #Map each step count with corresponding time wdinwo 
    timesSeries = pd.Series(times)
    time_sel_step_data = step_data.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)
    
    step_data.loc[:, 'time'] = time_sel_step_data
    
    stepsDf = pd.DataFrame([[t, step_data.loc[step_data['time'] == t, 'value'].sum()] for t in times], columns=['Date', 'Steps'])
            #Remove zero steps days and days less than 1000 steps
    stepsDf['Steps'].replace({0.0: np.nan}, inplace=True)
    stepsDf['Steps'].replace({np.inf: np.nan}, inplace=True)
    
    return stepsDf
    
    
    
def all(sensor_data, dates, resolution):
    #print(sensor_data['lamp.calls'])
    participant_step_count = step_count(sensor_data, dates, resolution=resolution)
    
    df_list = [participant_step_count]
    allDfs = reduce(lambda left, right: pd.merge(left, right, on=["Date"], how='left'), df_list)
    
    return allDfs
    
if __name__ == "__main__":
    pass

