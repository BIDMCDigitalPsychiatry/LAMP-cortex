"""Module for creating participant-level visualizations"""
from datetime import datetime
import time
import re
import LAMP
import pandas as pd
import altair as alt
from ..utils.useful_functions import generate_ids,set_graph,shift_time
from ..run import run

MS_PER_HOUR = 1000*60*60

def create_sample_window(end_of_window, sample_length, set_to_utc_midnight):
    """ Create a relevant time window for LAMP analysis.

        Args:
            end_of_window (int, unit: days): the number of days ago to start the window
            sample_length (int, unit: days): the length of the sample in days
                the window goes backward in time sample_length from end_of_window
                ex: if end of window is 1 and sample length is 7 the window will be
                    the week of data ending yesterday (1 day ago) and ending a week
                    before yesterday (length is 7)
            set_utc_to_midnight (booleanl): whether to shift the start and end time to
                midnight utc on that day
        Returns:
            the start and end timestamp of the window in ms
    """
    start_timestamp = (int(time.time()) - (end_of_window + sample_length) * 24 * 60 * 60) *1000
    end_timestamp = (int(time.time()) - (end_of_window) * 24 * 60 * 60) *1000
    if set_to_utc_midnight:
        return shift_time(start_timestamp,0), shift_time(end_timestamp,0)
    return start_timestamp, end_timestamp

def passive(id_list,
            sensor_info=[{"sensor": "lamp.gps", 'target_hz': 0.1, 'display_name': "GPS_Quality"},
            {"sensor": "lamp.accelerometer", 'target_hz': 3, 'display_name':"Accel_Quality"}],
            show_graphs=True, attach_graphs=True, display_graphs=True,
            days_ago=0, sample_length=7,
            set_to_utc_midnight=True, reporter_func=print,
            return_dict=False, reset=False):
    """ Generates and attaches participant-level passive data quality graphs.
    Stores data from previous runs as attachments to speed up outputs.

        Args:
            id_list: a string or array of strings of LAMP ids
                    (participant, study, researcher)
            show_graphs: if True, graphs are displayed in the output
            attach_graphs: if True, graphs are attached to the participant
            display_graphs: if True, graphs are attached to the study and researcher for display
            days_ago: the number of days ago the analysis should end.
                        If 0, analysis ends on the current timestamp
            sample_length: The number of days to query data for
            set_to_utc_midnight: If True, timestamps are adjusted to UTC midnight
            reporter_func: The function that should output important logging info.
                        Use with a webhook, for example logging to slack
            return_dict: If true, returns a dictionary containing data output. Else returns None.
            reset: If true, data from previous runs will be deleted.
        Returns:
            summary_dictionary: a dictionary containing data about the data.
    """
    # We iterate over each id and each sensor
    try:
        id_list = generate_ids(id_list)
    except LAMP.ApiException as invalid_id:
        raise KeyError("One or more ids provided was invalid.") from invalid_id
    if len(id_list) == 0:
        return None
    #Create our relevant time window to call LAMP
    start_timestamp, end_timestamp = create_sample_window(days_ago,
                                                          sample_length,
                                                          set_to_utc_midnight)
    summary_dictionary={}
    def timestamp_from_date(value):
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").timestamp()*1000

    for participant in id_list:
        summary_dictionary[participant]={}
        #analyze each sensor
        for sensor in sensor_info:
            default = {'raw':None,'graph':{},'info':sensor}
            summary_dictionary[participant][sensor['display_name']]= default
            try:
                #try to retrieve any sensor data from prior runs
                name = f"lamp.analysis.{sensor['display_name']}_stored"
                saved_data = []
                excluded_intervals=[]
                if reset:
                    LAMP.Type.set_attachment(participant,'me',name,None)
                else:
                    try:
                        saved_data = LAMP.Type.get_attachment(participant,name)['data']
                    except LAMP.ApiException:
                        print(f"Found no {participant} data under {name}")

                # if data is saved, we may need to query less data
                # thus, we make a list of excluded intervals
                if len(saved_data)!=0:
                    # extract a list of timestamps
                    # we intentionally exclude any timestamps with 0 counts of data
                    # since they are trivial to re-run if they are actually 0
                    timestamp_list = [timestamp_from_date(x['Time']) for x in
                                      saved_data if 'Counts' in x and x['Counts']!=0]
                    timestamp_counts = {x['Time']:x['Counts'] for x in
                                        saved_data if 'Counts' in x and x['Counts']!=0}
                    excluded_intervals = [datetime.
                                          fromtimestamp(x/1000).
                                          strftime("%Y-%m-%dT%H:%M:%SZ")
                                          for x in
                                          list(filter(lambda time:
                                                      start_timestamp <= time <= end_timestamp,
                                                      timestamp_list))
                                          if x<datetime.now().timestamp()*1000-60*60*1000]
                    excluded_intervals.sort()
                reporter_func(f"Querying for {participant} - {sensor['display_name']}")
                if len(excluded_intervals)!=0:
                    reporter_func(f"""Previous data was found.
                    {len(excluded_intervals)} chunks were excluded.""")
                    excluded_intervals = [timestamp_from_date(x) for x in excluded_intervals]
                target_sample_rate=sensor['target_hz']*60*60
                query = f'''
                    ($bucketedData := function($participant_id,$sensor,$start_timestamp,$end_timestamp){{(
                            $iter := function($newData, $acc){{(
                            ($count($newData)<1000 ? $append($acc,$newData) :
                            $iter($LAMP.SensorEvent.list($participant_id,$sensor,$start_timestamp,$newData[$count($newData)-1]).timestamp,[$append($acc,$newData)]));
                            )}};
                            $iter($LAMP.SensorEvent.list($participant_id,$sensor,$start_timestamp,$end_timestamp).timestamp,[])
                            )
                          }};
                        $existing_timestamps := {excluded_intervals};
                        $floor_timestamp := function($timestamp){{$fromMillis($timestamp,'[Y0001]-[M01]-[D01]T[H01]:00:00Z')}};
                        $end:= $toMillis($floor_timestamp({end_timestamp}));
                        $activity_counts := $map([0..(23+24*{sample_length-1})],function($hours){{(
                            $chunkStart := $end-(($hours+1)*1000*60*60);
                            $chunkEnd := $end-(($hours)*1000*60*60);
                            $temp := $chunkStart in $existing_timestamps ? [1] : $bucketedData('{participant}','{sensor['sensor']}',$chunkStart,$chunkEnd);
                            $floor_timestamp($chunkStart) in $existing_timestamps ? {{}} : {{"Time":$floor_timestamp($chunkStart),"Counts":$count($temp)}}
                            )}});
                        )
                    '''
                res = LAMP.API.query(query)
                # if no saved data existed
                if saved_data == []:
                    LAMP.Type.set_attachment(participant,'me',name,res)
                # saved data existed
                else:
                    times = [x['Time'] for x in res]
                    for val in res:
                        if val['Time'] in timestamp_counts:
                            val['Counts'] = timestamp_counts[val['Time']]

                    for entry in saved_data:
                        if entry['Time'] not in times:
                            res+=[entry]

                    res.sort(key = lambda entry: timestamp_from_date(entry['Time']))
                    LAMP.Type.set_attachment(participant,'me',name,res)
                print('\n')
                if len(res):
                    summary_dictionary[participant][sensor['display_name']]['raw']=res
            except Exception:
                reporter_func(f"Failed to analyze {sensor} for {participant}")

            #Create Result Dataframe
            result_dataframe = pd.DataFrame(res)

            #Create scatter chart pieces
            title = f"""Amount of {sensor['sensor']} data received over time"""
            chart = alt.Chart(result_dataframe).mark_line().encode(
                        x=alt.X('Time:T', axis=alt.Axis(title='Time')),
                        y=alt.X('Counts', axis=alt.Axis(title='Data entries received'))
                    ).properties(title={'text':title.capitalize()})
            line = alt.Chart(pd.DataFrame({'y': [target_sample_rate],
                                       'label':[f"Target Sample Rate ({sensor['target_hz']} Hz)"
                                               ]})).mark_rule(color='red').encode(y=alt.Y('y'))
            text = line.mark_text(
                align='left',
                baseline='middle',
                dy=-10,dx=-10).encode(text='label')
            #Assemble scatter plot
            scatter = chart+line+text

            #Create heatmap chart
            if result_dataframe['Counts'].max()>target_sample_rate:
                colors=['grey','blue','blue']
                domain=[0,target_sample_rate,result_dataframe['Counts'].max()]
            else:
                colors=['grey','blue']
                domain=[0,target_sample_rate]

            chart = alt.Chart(result_dataframe).mark_rect().encode(
                alt.X('hours(Time):T', title='Hour'),
                alt.Y('monthdate(Time):N', title='Day'),
                alt.Color('Counts', title='Data',
                          scale=alt.Scale(range=colors,
                                          domain=domain)),
                ).properties(title={'text':title.capitalize()})
            # Configure text
            text = chart.mark_text(baseline='middle',dx=10).encode(
                text='significant:N',
                color=alt.value('white')
            ).transform_calculate(significant=f'datum.Counts>{target_sample_rate}? "*" :""')
            #Assemble heatmap plot
            heatmap = (chart+text)

            if show_graphs:
                scatter.display()
                heatmap.display()
            (summary_dictionary[participant]
             [sensor['display_name']]['graph']['scatter'])=scatter.to_dict()

            (summary_dictionary[participant]
             [sensor['display_name']]['graph']['heatmap'])=heatmap.to_dict()

            if attach_graphs:
                name = f"lamp.dashboard.experimental.{sensor['display_name']}"
                set_graph(participant,
                         key=name+'_scatter',
                         graph=scatter.to_dict(),
                         display_on_patient_portal=display_graphs,
                         set_on_parents=True)
                set_graph(participant,
                         key=name+"_heatmap",
                         graph=heatmap.to_dict(),
                         display_on_patient_portal=display_graphs,
                         set_on_parents=True)

    reporter_func("All done, bye bye!")
    if return_dict:
        return summary_dictionary
    return None

def active(id_list,
             target_array=[''],exclude_array=None, exclude_groups=True,
             show_graphs=True, attach_graphs=True, display_graphs=True,
              graph_name='lamp.dashboard.experimental.activity_counts',
              days_ago=0, sample_length=30,
               reporter_func=print, return_dict=False):
    """ Generates and attaches participant-level active data quality graphs.

        Args:
            id_list: a string or array of strings of LAMP ids
                    (participant, study, researcher)
            target_array: a list of specs, names, or ids to display.
                Default is all. Include '' to show all activities.
            exclude_array: a list of names to exclude. Default is None.
            exclude_groups: attempt to exclude group completions
            show_graphs: if True, graphs are displayed in the output
            attach_graphs: if True, graphs are attached to the participant
            display_graphs: if True, graphs are attached to the study and researcher for display
            graph_name: set to another string to override the default name
            days_ago: the number of days ago the analysis should end.
                        If 0, analysis ends on the current timestamp
            sample_length: The number of days to query data for
            reporter_func: The function that should output important logging info.
                        Use with a webhook, for example logging to slack
            return_dict: If true, returns a dictionary containing data output. Else returns None.
        Returns:
            summary_dictionary: a dictionary containing data about the data
    """

    def get_active(_id, start, end, target_identifier='',
                   exclude_groups=True, exclude_unknowns=True,
                   overwrite_name=False, to_datetime=True,
                   limit=20000,recursive=True):
        """
        Get all Active data bounded by time interval.
        Optional "target" variable can be a name, id, or spec
        """

        target = ''
        target_ids = []
        activity_data = LAMP.Activity.all_by_participant(_id)['data']
        id_to_name = {x['id']:x['name'] for
                      x in activity_data if 'id' in x and 'name' in x}
        group_ids = [x['id'] for x in activity_data if x['spec']=='lamp.group']
        # if a filter was provided
        if len(target_identifier)>0:
            #check if the filter is an ID
            filtered_activities = [x for x in activity_data
                                  if x['name']==target_identifier]
            if len(filtered_activities)>0:
                target=filtered_activities[0]['id']
            else:
                # if it wasn't, we assume it was a name
                target_ids = [x['id'] for x in activity_data
                             if x['spec'] == target_identifier]
                if len(target_ids)==0:
                    return pd.DataFrame({})

        data = LAMP.ActivityEvent.all_by_participant(_id,
                                                   origin=target,
                                                   _from=start,
                                                   to=end,
                                                   _limit=limit)['data']
        while data and recursive:
            end = data[-1]['timestamp']
            data_next = LAMP.ActivityEvent.all_by_participant(_id,
                                                            origin=target,
                                                            _from=start,
                                                            to=end,
                                                            _limit=limit)['data']
            if not data_next:
                break
            if data_next[-1]['timestamp'] == end:
                break
            data += data_next

        if len(target_ids)>0:
            data = [x for x in data if x['activity'] in target_ids]

        if exclude_groups:
            data = [x for x in data if x['activity'] not in group_ids]

        # We filter out any timestamp before 2015, since it is invalid.
        # This is largely to prevent erroneous data from appearing on 'Jan 1st, 1970'
        data_df = pd.DataFrame.from_dict(list(reversed([{'timestamp': x['timestamp'],
                                                    'id':x['activity'],
                                                    'activity':id_to_name[x['activity']]
                                                    if x['activity'] in id_to_name and
                                                    not overwrite_name else
                                                    'UNKNOWN' if not overwrite_name
                                                    else target_identifier}
                                                   for x in data if x['timestamp']>1420070400])))

        if not data_df.empty and exclude_unknowns:
            data_df = data_df[~(data_df['activity']=="UNKNOWN")]


        if to_datetime and not data_df.empty:
            data_df['timestamp'] = pd.to_datetime(data_df['timestamp'], unit='ms').dt.normalize()
        elif data_df.empty:
            return pd.DataFrame({})


        data_df['count'] = data_df.groupby(['timestamp','id'])['activity'].transform('count')
        data_df = data_df.drop_duplicates()

        return data_df


    #Takes an array of ids
    def create_active_validity_df(id_set,
                                  start_timestamp, end_timestamp,
                                  target_array=[''],exclude_groups=True):
        """Creates a df using active data"""
        coll_dict = {}
        counter = 0
        empty = 0

        for part in id_set:
            temp = []
            counter+=1
            for target in target_array:
                try:
                    data_df = get_active(_id=part,
                                    start=start_timestamp,
                                    end=end_timestamp,
                                    target_identifier=target,
                                    exclude_groups=exclude_groups)
                    if not data_df.empty:
                        temp+= [data_df]
                except Exception as error:
                    empty+=1
                    print(f"Error in {target}")
                    print(error)
            if len(temp)>0:
                coll_dict[part] = (pd.concat(temp,ignore_index=True).
                                   drop_duplicates())
        if empty > 0:
            print(f"""Warning! {str(empty)} of {str(len(id_set))}
            participants had no active data for this time frame""")
        return coll_dict


    #generate our list of ids
    id_list = generate_ids(id_list)

    #Create our relevant time window to call LAMP
    start_timestamp, end_timestamp = create_sample_window(days_ago,
                                                          sample_length,
                                                          set_to_utc_midnight=False)

    reporter_func('Pulling data from LAMP server for all participants...')
    active_counts = create_active_validity_df(id_list, start_timestamp, end_timestamp,
                                              target_array=target_array,
                                              exclude_groups=exclude_groups)

    # we should now have an dict where the key is a id
    # and the value is a df of different active targets
    if isinstance(exclude_array, list):
        for _id,data_df in active_counts.items():
            active_counts[_id] = data_df[~data_df['activity'].isin(exclude_array)]
    chart_dict = {}
    reporter_func("Finished pulling data. Generating graphs...")

    def condense_name(string):
        first_character = string[0]
        string_remainder = string[1:]
        return (first_character.upper()+re.sub(r'[aeiou ]+','',string_remainder))[0:3]
    for part_id, data_df in active_counts.items():
        print(f"{part_id} data:")

        #this boolean helps us display data more nicely if there are a lot of different activities
        too_much_data = data_df.groupby('timestamp')['count'].transform('sum').max()>=9
        #if the columns will be too narrow, we don't display text
        graph_too_wide = (data_df.groupby('activity')['timestamp'].transform('count').max()>=30)
        data_df['activity_subname'] = data_df['activity'].apply(condense_name)

        final = alt.Chart(data_df).mark_bar().encode(
                x = alt.X('timestamp:T', title='Date'),
                y = alt.Y('count:Q', stack='zero',title='Activity Breakdown'),
                color=alt.Color('activity:N'),
                order=alt.Order('activity',sort='ascending'),
                tooltip=[alt.Tooltip(field='activity',title='Activity Name',type='nominal'),
                         alt.Tooltip(field='count',title='Times Completed',type='quantitative'),
                         alt.Tooltip(field='timestamp',title="Date",type='temporal')]
        )
        if not graph_too_wide:
            text = alt.Chart(data_df).mark_text(dy=0,
                                                dx=-5 if too_much_data else -20,
                                                angle=270, color='white').encode(
                x=alt.X('timestamp:T'),
                y=alt.Y('count:Q', stack='zero'),
                order=alt.Order('activity',sort='ascending'),
                text=alt.Text('text_output:N'),
                    tooltip=[alt.Tooltip(field='activity',
                                         title='Activity Name',
                                         type='nominal'),
                             alt.Tooltip(field='count',
                                         title='Times Completed',
                                         type='quantitative'),
                             alt.Tooltip(field='timestamp',
                                         title="Date",
                                         type='temporal')]
            ).transform_calculate(text_output='datum.count' if too_much_data
                                  else 'datum.activity_subname+":"+datum.count')
            final = final+text
        if show_graphs:
            (final).display()
        chart_dict[part_id]=(final).to_dict()

    if attach_graphs:
        reporter_func("Graphs generated. Attaching Graphs...")
        for participant,graph in chart_dict.items():
            set_graph(participant, key=graph_name,graph=graph,
                 display_on_patient_portal=display_graphs,
                 set_on_parents=True)
    reporter_func("Analysis complete")
    return active_counts if return_dict else None

def cortex_tertiles(target_id,
                    cortex_measures=['acc_energy',
                                     'entropy',
                                     'hometime',
                                     'screen_duration'],
                    measure_params={},
                    use_cache=False,
                    show_graphs=True, attach_graphs=True, display_graphs=True,
                    days_ago=0, sample_length=7,
                    reporter_func=print,
                    set_to_utc_midnight=True,
                    return_dict=False,
                   **kwargs):
    """ Function to run an array of cortex functions on to generate cortex graphs.

        Args:
            target_id: Required. a string or array of LAMP user, study, or researcher ids.
                    All user ids below one or more ids in the list (if applicable) will be run
            cortex_measures: Default:['acc_energy','entropy','hometime','screen_duration'].
                    a string, list, or dict of cortex measures.
                    If a dict, keys will be used for the array fed into run
                    and the values will be used as labels. E.g. {'sleep_periods':'Sleep'}
            measure_params: Measure params to pass into cortex
            use_cache: If true, attempt to use cached data
            show_graphs:Default True. a boolean - whether to show graphs generated
                    to the user running the function call
            attach_graphs:Default True. a boolean - whether to attach graphs
                    to the participant as a tag
            display_graphs:Default True. a boolean - whether to display graphs to
                    the participant on their prevent page
            days_ago: Default 0. Number of days ago to end analysis.
                    Set to 0 to end analysis today
            sample_length: Default 7. Timespan for analysis, in days.
            reporter_func: Default 'print'. A function which should take one variable,
                    which are outputs from this function, and displays them to a user
            set_to_utc_midnight: Default True. Whether or not to set the utc time to true
            return_dict: Default False. Whether or not to return a dictionary
                    of all cortex outputs at the end.

        Returns:
            A dictionary containing all results and
            Vega specs for graphs if return_dict is true.
            Else none.
    """
    #generate our list of ids
    id_list = generate_ids(target_id)

    #Create our relevant time window to call LAMP
    start_timestamp, end_timestamp = create_sample_window(days_ago,
                                                          sample_length+1,
                                                          set_to_utc_midnight)
    coll_dict = {}

    for user in id_list:
        coll_dict[user] = {}

    # coerce cortex measures into dict format
    # this lets us use labels more easily
    if isinstance(cortex_measures, str):
        cortex_measures = [cortex_measures]

    if isinstance(cortex_measures, list):
        cortex_measures = {x:x for x in cortex_measures}

    print(cortex_measures)

    failed_to_cortex = []
    for _id in id_list:
        try:
            print(f"Attempting to run cortex analyses on {_id}")
            measure_list = cortex_measures.keys()
            coll_dict[_id]['raw']={}
            for cortex_measure in measure_list:
                print(f'Running {cortex_measure} on {_id}')
                try:
                    cortex_result = run(_id,
                                               [cortex_measure],
                                               feature_params=measure_params,
                                               start=start_timestamp,
                                               end=end_timestamp,
                                               resolution=MS_PER_HOUR,
                                               cache=use_cache, **kwargs)
                    for measure,result_df in cortex_result.items():
                        coll_dict[_id]['raw'][measure] = result_df
                except Exception as error: #pylint:disable=broad-except
                    print(f"""Failed to analyze {cortex_measure} for {_id}.
                    {error.__class__.__name__}:{error}""")
                    failed_to_cortex += [_id]
            print(f"Successfully completed cortex analyses for {_id}")
        except Exception as error:#pylint:disable=broad-except
            reporter_func(f'''Something went wrong while running
            cortex analyses for {_id}. {error.__class__.__name__}:{error}''')
            failed_to_cortex += [_id]

    failed_to_make_graph = []
    for _id in coll_dict:
        coll_dict[_id]['graphs']={}
        if 'raw' not in coll_dict[_id]:
            reporter_func(f'No data present for {_id}')
            continue
        for measure, measure_df in coll_dict[_id]['raw'].items():
            try:
                if measure_df.empty:
                    reporter_func(f"{measure} data frame empty for {_id}")
                    continue
                if 'value' not in measure_df:
                    reporter_func(f"""{measure} does not have have a 'value' column
                    and no alternate analysis method is available""")
                    continue
                df_max =  measure_df['value'].max()
                df_min = measure_df['value'].min()
                df_range = df_max-df_min
                df_avg = (df_max+df_min)/2
                df_lower_third = df_avg-df_range/6
                df_upper_third = df_avg+df_range/6

                measure_df['Tertile'] = [None if x is None else
                                         "Zero" if x==0 else
                                     "High" if x>df_upper_third else
                                     "Low" if x<df_lower_third else
                                     "Medium" for x in measure_df['value']]


                measure_df['val'] = [None if x is None else
                                         0 if x==0 else
                                     3 if  x>df_upper_third else
                                     1 if x<df_lower_third else
                                     2 for x in measure_df['value']]

                measure_df['raw_score'] = measure_df['value'].apply(str)


                tooltip = [alt.Tooltip(field='timestamp',title='Date',type='temporal'),
                           alt.Tooltip(field='Tertile',title='Relative Amount',type='nominal'),
                           alt.Tooltip(field='raw_score',title='Raw Score',type='nominal')]
                
                title = (f'{cortex_measures[measure]} tertiles'+
                f' over the past {len(measure_df["value"])} days').capitalize()

                if 0 not in measure_df['val']:
                    chart = (alt.Chart().
                                      mark_point().
                                      encode(alt.X('monthdate(timestamp):O',
                                                   axis =alt.Axis(title="Time")),
                                             alt.Y('val:Q',scale=alt.Scale(domain=(0,4)),
                                                   axis =alt.Axis(title="Relative Score",
                                                                  labels=False,grid=False)),
                                             tooltip=tooltip,
                                             color=alt.Color('Tertile',
                                                             scale=alt.Scale(
                                                                 domain=['High',
                                                                         'Medium',
                                                                         "Low"],
                                                                 range=["blue",
                                                                        "salmon",
                                                                        "goldenrod"]),
                                             sort=['High','Medium',"Low"])).
                             properties(title=title))

                    vert_lines = alt.Chart().mark_bar(width=1, orient='vertical').encode(
                        x=alt.X('monthdate(timestamp):O', axis =alt.Axis(title="Time")),
                        y=alt.Y('val:Q',scale=alt.Scale(domain=(0,4)),
                                axis =alt.Axis(title="Relative Score",
                                               labels=False,grid=False)),
                        color=alt.Color('Tertile',
                                        scale=alt.Scale(domain=['High','Medium',"Low"],
                                                        range=["blue","salmon","goldenrod"]),
                                             sort=['High','Medium',"Low"]))
                else:
                    chart = (alt.Chart().
                                      mark_point().
                                      encode(alt.X('monthdate(timestamp):O',
                                                   axis =alt.Axis(title="Time")),
                                             alt.Y('val:Q',scale=alt.Scale(domain=(0,4)),
                                                   axis =alt.Axis(title="Relative Score",
                                                                  labels=False,grid=False)),
                                             tooltip=tooltip,
                                             color=alt.Color('Tertile',
                                                             scale=alt.Scale(
                                                                 domain=['High',
                                                                         'Medium',
                                                                         "Low",
                                                                         "Zero"],
                                                                 range=["blue",
                                                                        "salmon",
                                                                        "goldenrod",
                                                                        'black']),
                                             sort=['High','Medium',"Low","Zero"])).
                             properties(title=title))

                    vert_lines = alt.Chart().mark_bar(width=1, orient='vertical').encode(
                        x=alt.X('monthdate(timestamp):O', axis =alt.Axis(title="Time")),
                        y=alt.Y('val:Q',scale=alt.Scale(domain=(0,4)),
                                axis =alt.Axis(title="Relative Score",
                                               labels=False,
                                               grid=False)),
                        color=alt.Color('Tertile',
                                        scale=alt.Scale(
                                            domain=['High','Medium',"Low","Zero"],
                                            range=["blue","salmon","goldenrod",'black']),
                                             sort=['High','Medium',"Low","Zero"]))
                final = alt.layer(chart,vert_lines,data=measure_df)
                coll_dict[_id]['graphs'][cortex_measures[measure]] = final.to_dict()
            except Exception as error: #pylint:disable=broad-except
                reporter_func(f'''Could not generate {measure}
                graph for {_id}. {error.__class__.__name__}:{error}''')
                failed_to_make_graph+=[_id]

    failed_to_attach_graphs =[]
    for user in coll_dict:
        if show_graphs:
            reporter_func(f"Graphs for {user}:")
        for name, item in coll_dict[user]["graphs"].items():
            if show_graphs:
                reporter_func(name)
                alt.Chart().from_dict(item).display()
            #attach graphs if required:
            if attach_graphs:
                set_graph(user,
                         key=f"lamp.dashboard.experimental.{name}_graph",
                         graph=item,
                         display_on_patient_portal=display_graphs,
                         set_on_parents=True)

    reporter_func(f"""Cortex Analysis Summary:\n
                  {len(id_list)-len(list(set(failed_to_attach_graphs+failed_to_make_graph+failed_to_cortex)))} participants encountered no issues.\n
                  {list(set(failed_to_cortex))} failed at some point during cortex generation.\n
                  {list(set(failed_to_make_graph))} failed to make one or more graphs.\n
                  {list(set(failed_to_attach_graphs))} failed to attach one or more graphs.""")

    return coll_dict if return_dict else None
