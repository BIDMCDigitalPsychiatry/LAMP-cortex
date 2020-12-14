import datetime
import pandas as pd
from functools import reduce

def social_duration():
    """
    """
    pass

def conversational_degree():
    """
    """

    pass

def call_degree(data, times, resolution):
    """
    Find degree of call log (i.e. how many persons the user connected with over phone)
    """
    if 'lamp.calls' not in data:
        return pd.DataFrame({'Date': times, 'Call Degree': [0] * len(times)})
        
    #Remove duplicate entries by converting call data to set
    call_data = data['lamp.calls']
    sel_call_data = call_data.copy()
    
    #Map each call with corresponding time wdinwo 
    timesSeries = pd.Series(times)
    time_sel_call_data = sel_call_data.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)
    
    sel_call_data.loc[:, 'time'] = time_sel_call_data.values

    callDegreeDf = pd.DataFrame([[t, sel_call_data.loc[sel_call_data['time'] == t, 'call_trace'].nunique()] for t in times], columns=['Date', 'Call Degree'])
    
    return callDegreeDf
    
    


def call_duration(data, times, resolution, label=1):
    """
    Find call time

    :param
    :param
    :param label(int): indicates whether or not to query incoming calls (1) or outgoing calls (2)
    """
    if 'lamp.calls' not in data:
        return pd.DataFrame({'Date': times, 'Call Duration': [0] * len(times)})
        
    #Remove duplicate entries by converting call data to set
    call_data = data['lamp.calls']
    sel_call_data = call_data.loc[call_data['call_type'] == label, :]
    
    #Map each call with corresponding time wdinwo 
    timesSeries = pd.Series(times)
    time_sel_call_data = sel_call_data.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)
    
    sel_call_data.loc[:, 'time'] = time_sel_call_data
    
    callDurationDf = pd.DataFrame([[t, sel_call_data.loc[sel_call_data['time'] == t, 'call_duration'].mean()] for t in times], columns=['Date', 'Call Duration'])
    
    return callDurationDf
    


def call_number(data, times, resolution, label=1):
    """
    Find number of calls

    :param (str): 
    :param 
    :param label(int): indicates whether or not to query incoming calls (1), outgoing calls (2)
    """
    if 'lamp.calls' not in data:
        return pd.DataFrame({'Date': times, 'Call Number': [0] * len(times)})
        
    #Remove duplicate entries by converting call data to set
    call_data = data['lamp.calls']
    sel_call_data = call_data.loc[call_data['call_type'] == label, :]
    
    #Map each call with corresponding time wdinwo 
    timesSeries = pd.Series(times)
    time_sel_call_data = sel_call_data.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)
    
    sel_call_data.loc[:, 'time'] = time_sel_call_data
    
    callNumberDf = pd.DataFrame([[t, len(sel_call_data.loc[sel_call_data['time'] == t, :])] for t in times], columns=['Date', 'Call Number'])
    
    return callNumberDf
    
    
    
def all(sensor_data, dates, resolution):
    #print(sensor_data['lamp.calls'])
    incoming_calls, outgoing_calls = call_number(sensor_data, dates, resolution=resolution, label=1), call_number(sensor_data, dates, resolution=resolution, label=2)
    incoming_callduration, outgoing_callduration = call_duration(sensor_data, dates, resolution=resolution, label=1), call_duration(sensor_data, dates, resolution=resolution, label=2)

    total_call_degree = call_degree(sensor_data, dates, resolution)
    #print(incoming_calls)#, incoming_callduration, total_call_degree)
    
    df_list = [incoming_calls, outgoing_calls, incoming_callduration, outgoing_callduration]
    allDfs = reduce(lambda left, right: pd.merge(left, right, on=["Date"], how='left'), df_list)
    
    return allDfs
    
if __name__ == "__main__":
    pass
# def call_text_features(sensor_data, dates):
#     print('YO')
#     call_number(sensor_data, dates)
