import lamp_cortex

def travel_duration(dates, freq=datetime.timedelta(days=1), **kwargs):
    '''
    Distance Traveled - Meters
    '''
    if 'trips' in kwargs and kwargs['trips'] is not None:
        trips = kwargs['trips']
    else:
        assert 'participant_id' in kwargs
        trips = lamp_cortex.features.primary.trips(kwargs['participant_id'])

    l = trips
    interval_range = dates

    trip_dict = lamp_cortex.sensors.gps.gen_trip_dict(interval_range)

    for i in range(len(dates)):
        if i == len(dates) - 1:
            date, next_date = dates[i], dates[i] + freq
        else:
            date, next_date = dates[i], dates[i+1]
        for idx, trip in trips.iterrows():
            if date <= trip['Trip Start'] and next_date >= trip['Trip End']:
                trip_dict[date]['Distance Traveled'] = trip['Distance']

    distTravelledDf = pd.DataFrame([[t, trip_dict[t]['Distance Traveled']] for t in trip_dict],
                          columns=['Date', 'Distance Traveled'])

    return distTravelledDf