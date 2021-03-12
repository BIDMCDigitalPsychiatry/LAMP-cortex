import datetime
import pandas as pd
from functools import reduce


def call_degree(data, times, resolution):
    """
    Find degree of call log (i.e. how many persons the user connected with over phone)
    """
    if 'lamp.calls' not in data:
        return pd.DataFrame({'Date': times})
        
    #Remove duplicate entries by converting call data to set
    call_data = data['lamp.calls']
    sel_call_data = call_data.copy()
    
    #Map each call with corresponding time wdinwo 
    timesSeries = pd.Series(times)
    time_sel_call_data = sel_call_data.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)
    
    if len(time_sel_call_data) == 0:
        return pd.DataFrame([[t, 0] for t in times], columns=['Date', 'Call Degree'])
        
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
        return pd.DataFrame({'Date': times})
        
    #Remove duplicate entries by converting call data to set
    call_data = data['lamp.calls']
    sel_call_data = call_data.loc[call_data['call_type'] == label, :]

    #Set labels
    if label == 1: column_labels = ['Date', 'Call Duration.Incoming']
    elif label == 2: column_labels = ['Date', 'Call Duration.Outgoing']
    else: column_labels = ['Date', '.'.join(['Call Duration', 'Unknown', str(label)])]
    
    #Map each call with corresponding time window
    timesSeries = pd.Series(times)
    time_sel_call_data = sel_call_data.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)

    if len(time_sel_call_data) == 0:
        return pd.DataFrame([[t, 0] for t in times], columns=column_labels)

    sel_call_data.loc[:, 'time'] = time_sel_call_data

    callDurationDf = pd.DataFrame([[t, sel_call_data.loc[sel_call_data['time'] == t, 'call_duration'].mean()] for t in times], columns=column_labels)
    
    return callDurationDf
    


def call_number(data, times, resolution, label=1):
    """
    Find number of calls

    :param (str): 
    :param 
    :param label(int): indicates whether or not to query incoming calls (1), outgoing calls (2)
    """
    if label == 1: column_labels = ['Date', 'Call Number.Incoming']
    elif label == 2: column_labels = ['Date', 'Call Number.Outgoing']
    else: column_labels = ['Date', '.'.join(['Call Number', 'Unknown', str(label)])]

    if 'lamp.calls' not in data:
        return pd.DataFrame({'Date': times})
        
    #Remove duplicate entries by converting call data to set
    call_data = data['lamp.calls']
    sel_call_data = call_data.loc[call_data['call_type'] == label, :]
    
    #Map each call with corresponding time wdinwo 
    timesSeries = pd.Series(times)
    time_sel_call_data = sel_call_data.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)
    
    if len(time_sel_call_data) == 0:
        return pd.DataFrame([[t, 0] for t in times], columns=column_labels)

    sel_call_data.loc[:, 'time'] = time_sel_call_data
    


    callNumberDf = pd.DataFrame([[t, len(sel_call_data.loc[sel_call_data['time'] == t, :])] for t in times], columns=column_labels)
    
    return callNumberDf
    
    
    
def all(sensor_data, dates, resolution):
    
    #If calls not available, return empty dataframe with only dates
    if 'lamp.calls' not in sensor_data:
        return pd.DataFrame({'Date':dates})

    incoming_calls, outgoing_calls = call_number(sensor_data, dates, resolution=resolution, label=1), call_number(sensor_data, dates, resolution=resolution, label=2)
    incoming_callduration, outgoing_callduration = call_duration(sensor_data, dates, resolution=resolution, label=1), call_duration(sensor_data, dates, resolution=resolution, label=2)

    total_call_degree = call_degree(sensor_data, dates, resolution)
    
    df_list = [incoming_calls, outgoing_calls, incoming_callduration, outgoing_callduration]
    allDfs = reduce(lambda left, right: pd.merge(left, right, on=["Date"], how='left'), df_list)
    
    return allDfs
    