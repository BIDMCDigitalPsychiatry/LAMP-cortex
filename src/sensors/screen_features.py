import math 
import pandas as pd
import datetime
from geopy import distance

def charging_frequency(sensor_data, df):
    """
    Find time spent charging dervicer
    """
    #Remove duplicate entries by converting state data to set
    screen_data = set([(datetime.datetime.utcfromtimestamp(state[0] / 1000), tuple([(entry, state[1][entry]) for entry in state[1]])) for state in sensor_data['lamp.screen_state']])
    print([[min([t for t in times if t <= state[0]], key=lambda x: abs(x - state[0])), dict(state[1])['state']] for state in sensor_data['lamp.screen_state']])
    #Match each state with a corresponding time window
    screenDf = pd.DataFrame([[min([t for t in times if t <= state[0]], key=lambda x: abs(x - state[0])), dict(state[1])['state']] for state in sensor_data['lamp.screen_state'] if dict(state[1])['state'] in ['4', '5'] and state[0] >= sorted(times)[0] and state[0] <= sorted(times)[-1] + resolution], columns=['Date', 'Screen State'])
    print(screenDf)

def notification_checks(sensor_data, df):
    pass

def daily_device_usage(sensor_data, df):
    pass

def all(sensor_data, df, resolution):
    #charging_frequency(sensor_data, df)
    pass

if __name__ == "__main__":
    pass