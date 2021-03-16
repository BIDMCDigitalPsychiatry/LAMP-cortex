import lamp_cortex

def entropy(df, dates, resolution, k_max=10):
    """
    """
    _, df_sig_locs  = significant_locs(df, k_max=k_max)
    
    #Map each gps read with corresponding time window
    timesSeries = pd.Series(dates)
    time_sel_gps = df_sig_locs.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)
    
    df_sig_locs.loc[:, 'matched_time'] = time_sel_gps

    ent_df_data = []
    #For each window, calculate entropy
    for t in dates: 
        cluster_dict = {cluster:[] for cluster in df_sig_locs['cluster_label'].unique()}
        gps_readings = df_sig_locs.loc[df_sig_locs['matched_time'] == t, :].reset_index().sort_values(by='local_datetime')
        for idx, row in gps_readings.iterrows():            
            if idx == len(gps_readings) - 1: #If on last readings
                elapsed_time = (t + resolution) - gps_readings.loc[gps_readings.index[idx], 'local_datetime']
                #print(elapsed_time)
                if elapsed_time > datetime.timedelta(hours=1):
                    elapsed_time = datetime.timedelta(hours=1)
        
            else:
                elapsed_time = gps_readings.loc[gps_readings.index[idx + 1], 'local_datetime'] - gps_readings.loc[gps_readings.index[idx], 'local_datetime']
        
                if elapsed_time > datetime.timedelta(hours=1):
                    elapsed_time = datetime.timedelta(hours=1)

            # BUG: producing some negative elapsed times
            if elapsed_time < datetime.timedelta():
                continue

            cluster = gps_readings.loc[gps_readings.index[idx], 'cluster_label']
            cluster_dict[cluster].append(elapsed_time)
        
        total_time_locations_all = pd.concat([pd.Series(cluster_dict[c]) for c in cluster_dict]).sum()
        if total_time_locations_all == 0.0:
            total_time_locations_all = datetime.timedelta()

        entropy = 0.0
        for c in cluster_dict:
            c_time = pd.Series(cluster_dict[c]).sum()
            if c_time == 0:
                continue

            pctg = c_time / total_time_locations_all
            if pctg == 0:
                continue 
            
            prod = pctg * math.log(pctg)
            entropy -= entropy 

        if entropy == 0.0: #then add nan
            entropy = np.nan 

        ent_df_data.append([t, entropy])

    entDf = pd.DataFrame(ent_df_data, columns=['Date', 'Entropy'])

    return entDf

def significant_locations_visited(df, dates, resolution, k_max=10):
    centers, df_sig_locs  = significant_locs(df, k_max=k_max)
    
    #Map each gps read with corresponding time window
    timesSeries = pd.Series(dates)
    time_sel_gps = df_sig_locs.apply(lambda row: timesSeries[(timesSeries <= row['local_datetime']) & ((row['local_datetime'] - timesSeries) < resolution)].max(), axis=1)
    
    df_sig_locs.loc[:, 'matched_time'] = time_sel_gps

    sig_locs_visited_df_data = []
    #For each window, calculate entropy
    for t in dates:
        gps_readings = df_sig_locs.loc[df_sig_locs['matched_time'] == t, :].reset_index()
        
        if len(gps_readings) == 0:
            time_locs = []

        else:
            for idx, row in gps_readings.iterrows():            
                time_locs_labels = gps_readings['cluster_label'].unique()
                time_locs = [centers[l] for l in time_locs_labels]

        sig_locs_visited_df_data.append([t, time_locs])

    sigLocsDf = pd.DataFrame(sig_locs_visited_df_data, columns=['Date', 'Significant Locations'])
    return sigLocsDf

def all(sensor_data, dates, resolution):
    #Check one of two gps sensors
    if "lamp.gps" in sensor_data and len(sensor_data['lamp.gps']) > 1:
        gps_sensor = "lamp.gps"

    else: #no gps sensor; return empty df
        return pd.DataFrame({'Date': dates})

    labeled_data = label_gps_points(sensor_data, gps_sensor=gps_sensor)
    trip_data = get_trips(labeled_data)
    interval_range = pd.interval_range(labeled_data.loc[labeled_data.index[0], 'local_timestamp'], 
                                       labeled_data.loc[labeled_data.index[-1], 'local_timestamp'], 
                                       freq=resolution)

    tripDf = get_trip_features(trip_data, dates, freq=resolution)
    entropyDf = entropy(sensor_data[gps_sensor], dates, resolution)
    hometimeDf = hometime(sensor_data[gps_sensor], dates, resolution)
    sigLocsDf = significant_locations_visited(sensor_data[gps_sensor], dates, resolution)

    df_list = [tripDf, entropyDf, hometimeDf, sigLocsDf]
    allDfs = reduce(lambda left, right: pd.merge(left, right, on=["Date"], how='left'), df_list)
    
    return allDfs
