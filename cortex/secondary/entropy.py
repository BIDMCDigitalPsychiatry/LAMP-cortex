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