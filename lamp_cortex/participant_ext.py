import pandas as pd 
import numpy as np
import datetime
import os
import math
import LAMP 
import sys
import lamp_cortex
import itertools
from functools import reduce
from tzwhere import tzwhere
import pytz
from dateutil.tz import tzlocal



class ParticipantExt():
    """
    Create participant dataframe
    """
    def __init__(self, 
                 id, 
                 domains=None, 
                 age=None, 
                 race=None, 
                 sex=None, 
                 df_props={}):

        self.id = id
        self.domains = domains
        self.age = age
        self.race = race
        self.sex = sex

        self.df = self.create_df(**df_props)

        self.impute_status = False
        self.bin_status = False
        self.normalize_status = False	

    @property
    def id(self):
        return self._id

    @property
    def age(self):
        return self._age

    @property
    def race(self):
        return self._race

    @property
    def sex(self):
        return self._sex

    @property
    def domains(self):
        return self._domains

    @id.setter
    def id(self, value):
        self._id = value

    @age.setter
    def age(self, value):
        self._age = value

    @race.setter
    def race(self, value):
        self._race = value

    @sex.setter
    def sex(self, value):
        self._sex = value

    @domains.setter 
    def domains(self, value):
        self._domains = value 

    def reset(self):
        """
        Resets the participant's df to be the original version
        """
        self.df = self.create_df()
        self.impute_status, self.bin_status, self.normalize_status = False, False, False

    def domain_check(self, domains):
        """
        If domains is passed in, just return it.
        Else, see if domains is set as object attribute
        """
        if domains is None:
            if not hasattr(self, 'domains'):
                raise AttributeError('Domains were not set for cohort and were not provided.')
            domains = self.domains
        return domains

    @staticmethod
    def sensor_results(participant):
        """
        Get dictionary of sensor data
        """
        lamp_sensors = ["lamp.accelerometer", "lamp.accelerometer.motion", #"lamp.analytics", 
                        "lamp.blood_pressure", "lamp.bluetooth", "lamp.calls", "lamp.distance",
                        "lamp.flights", "lamp.gps", "lamp.gps.contextual", "lamp.gyroscope",
                        "lamp.heart_rate", "lamp.height", "lamp.magnetometer", "lamp.respiratory_rate",
                        "lamp.screen_state","lamp.segment", "lamp.sleep", "lamp.sms", "lamp.steps",
                        "lamp.weight", "lamp.wifi"]

        participant_sensors = {}
        for sensor in lamp_sensors:

            sens_results = sorted([{'UTC_timestamp':res['timestamp'], **res['data']} 
                                 for res in LAMP.SensorEvent.all_by_participant(participant, origin=sensor, _limit=25000)['data']], key=lambda x: x['UTC_timestamp'])

            if len(sens_results) == 0:
                continue 

            sens_event_oldest = sens_results[0]['UTC_timestamp']
            while len(sens_results) == 25000:
                sens_results += sorted([{'UTC_timestamp':res['timestamp'], **res['data']} for res in LAMP.SensorEvent.all_by_participant(participant, origin=sensor, to=sens_event_oldest, _limit=25000)['data']], key=lambda x: x['UTC_timestamp'])
                if len(sens_results) == 0:
                    break
                sens_event_oldest = sens_results[0]['UTC_timestamp']

            participant_sensors[sensor] = pd.DataFrame.from_dict(sens_results).drop_duplicates(subset='UTC_timestamp') #remove duplicates

        #Edge case of lamp.gps.contextual
        if 'lamp.gps.contextual' in participant_sensors and 'lamp.gps' not in participant_sensors:
            gps_context = participant_sensors['lamp.gps.contextual'].copy()
            if len(gps_context[['UTC_timestamp', 'latitude', 'longitude', 'accuracy']].dropna()) > 0:
                participant_sensors['lamp.gps'] = gps_context[['UTC_timestamp', 'latitude', 'longitude', 'accuracy']].dropna()

        return participant_sensors

    @staticmethod
    def cognitive_game_results(participant):
        """
        Get dictionary of jewels data
        """

        participant_activities = LAMP.Activity.all_by_participant(participant)['data']
        participant_activities_cgs = [activity for activity in participant_activities if activity['spec'] in ['lamp.jewels_a', 'lamp.jewels_b']]
        participant_activities_cg_ids = {cg['id']:cg for cg in participant_activities_cgs}        
        
        raw_results = sorted(LAMP.ActivityEvent.all_by_participant(participant, _limit=25000)['data'], key=lambda x: x['timestamp'])
        cg_results = [res for res in raw_results if 'activity' in res and res['activity'] in participant_activities_cg_ids]

        cg_data = {}
        if len(raw_results) == 0:
            return cg_data
        res_oldest = raw_results[0]['timestamp']

        while len(raw_results) == 25000:
            raw_results = sorted(LAMP.ActivityEvent.all_by_participant(participant, to=res_oldest, _limit=25000)['data'], key=lambda x: x['timestamp'])
            cg_results += [res for res in raw_results if 'activity' in res and res['activity'] in participant_activities_cg_ids]
            if len(raw_results) == 0:
                break
            res_oldest = raw_results[0]['timestamp']

        cg_results_dict = sorted([{'UTC_timestamp':res['timestamp'],
                                   'duration':res['duration'],
                                   'activity':res['activity'],
                                   'activity_name':participant_activities_cg_ids[res['activity']]['spec'], 
                                   'static_data':res['static_data'], 
                                   'temporal_slices':res['temporal_slices']} for res in cg_results], key=lambda x: x['UTC_timestamp'])
           
        if len(cg_results_dict) > 0:
            for cg, cgDf in pd.DataFrame.from_dict(cg_results_dict).drop_duplicates(subset='UTC_timestamp').groupby('activity_name'):
                cg_data[cg] = cgDf
        
        return cg_data


    @staticmethod
    def survey_results(participant, question_categories=None):
        """
        Get survey events for participant
        
        :param participant (str): the LAMP ID for participant. If not provided, then take participant id
        :param question_categories (dict): maps text in active event responses to a domain (str) and reverse_scoring parameter (bool)
        """
        participant_activities = LAMP.Activity.all_by_participant(participant)['data']
        participant_activities_surveys = [activity for activity in participant_activities if activity['spec'] == 'lamp.survey'] 
        participant_activities_surveys_ids = [survey['id'] for survey in participant_activities_surveys]        
        
        raw_results = sorted(LAMP.ActivityEvent.all_by_participant(participant, _limit=25000)['data'], key=lambda x: x['timestamp'])
        participant_results = [result for result in raw_results if 'activity' in result and result['activity'] in participant_activities_surveys_ids and len(result['temporal_slices']) > 0]

        if len(raw_results) > 0:
            res_oldest = raw_results[0]['timestamp']
            while len(raw_results) == 25000:
                raw_results = sorted(LAMP.ActivityEvent.all_by_participant(participant, to=res_oldest, _limit=25000)['data'], key=lambda x: x['timestamp'])
                participant_results += [result for result in raw_results if 'activity' in result and result['activity'] in participant_activities_surveys_ids and len(result['temporal_slices']) > 0]
                if len(raw_results) == 0:
                    break
                res_oldest = raw_results[0]['timestamp']
        
        participant_surveys = {} #maps survey_type to occurence of scores 
        for result in participant_results:
            #Check if it's a survey event
            if result['activity'] not in participant_activities_surveys_ids or len(result['temporal_slices']) == 0: 
                continue
            
            activity = LAMP.Activity.view(result['activity'])['data'][0]
            result_settings = activity['settings']

            survey_time = result['timestamp']
            survey_result = {} #maps question domains to scores
            for event in result['temporal_slices']: #individual questions in a survey
                question = event['item']
                
                exists = False
                for i in range(len(result_settings)) : #match question info to question
                    if result_settings[i]['text'] == question: 
                        current_question_info=result_settings[i]
                        exists = True
                        break

                if not exists: #question text is different from the activity setting; skip
                    continue
                    
                #score based on question type:
                event_value = event.get('value') #safely get event['value'] to protect from missing keys
                score = None #initialize score if, in the case of list parsing, it can't find a proper score
                
                if event_value == 'NULL' or event_value is None: continue # invalid (TO-DO: change these events to ensure this is not being returned)
                
                elif current_question_info['type'] == 'likert' and event_value != None:
                    score = float(event_value)
                        
                elif current_question_info['type'] == 'boolean':
                    if event_value.upper() == 'NO': score = 0.0 #no is healthy in standard scoring
                    elif event_value.upper() == 'YES' : score = 3.0 # yes is healthy in reverse scoring

                elif current_question_info['type'] == 'list' :
                    for option_index in range(len(current_question_info['options'])) :
                        if event_value == current_question_info['options'][option_index] :
                            score = option_index * 3 / (len(current_question_info['options'])-1)

                # elif current_question_info['type'] == 'text':  #skip
                #     continue
                
                else: continue #no valid score to be used
                    
                #add event to a category, either user-defined or default activity
                if question_categories:
                    if question not in question_categories: #See if there is an extra space in the string
                        if question[:-1] in question_categories:
                            question = question[:-1]
                        else:
                            continue

                    event_category = question_categories[question]['category']
                    #flip score if necessary
                    if question_categories[question]['reverse_scoring']: 
                        score = 3.0 - score

                    if event_category in survey_result: survey_result[event_category].append(score) 
                    else: survey_result[event_category] = [score]

                else:
                    if activity['name'] not in survey_result:
                        survey_result[activity['name']] = []

                    if score:
                        survey_result[activity['name']].append(score)
                    

            #add mean to each cat to master dictionary           
            for category in survey_result: 
                survey_result[category] = np.mean(survey_result[category])
                if category not in participant_surveys: 
                    participant_surveys[category] = [[survey_time, survey_result[category]]]
                else: 
                    participant_surveys[category].append([survey_time, survey_result[category]])

        #Sort surveys by time
        for activity_category in participant_surveys:
            participant_surveys[activity_category] = pd.DataFrame(data=sorted(participant_surveys[activity_category], key=lambda x: x[0]),
                                                                  columns=['UTC_timestamp', 'score'])
        return participant_surveys
        

    @staticmethod
    def timezone_correct(results, gps_sensor='lamp.gps'):
        """
        Convert timestamps to appropriate local time; use GPS if it exists
        """
        for dom in results:

            if gps_sensor in results and len(results[gps_sensor].dropna(subset=['latitude', 'longitude'])) > 0:

                if 'timezone' not in results[gps_sensor].columns: #Generate timezone for every gps readings and convert timestamps
                    tz = tzwhere.tzwhere(forceTZ=True) #force timezone if ambigiuous
                    try:
                        results[gps_sensor].loc[:, 'timezone'] = results[gps_sensor].apply(lambda x: tz.tzNameAt(x['latitude'], 
                                                                                                                x['longitude'], 
                                                                                                                forceTZ=True), 
                                                                                        axis=1)
                    except:
                        tz = pytz.timezone(datetime.datetime.now(tzlocal()).tzname()) 
                        matched_gps_readings = pd.Series([tz] * len(results[dom]))
                        results[gps_sensor].loc[:, 'timezone'] = matched_gps_readings

                    gps_converted_datetimes = pd.Series([datetime.datetime.fromtimestamp(t/1000, tz=pytz.timezone(results[gps_sensor]['timezone'][idx])) for idx, t in results[gps_sensor]['UTC_timestamp'].iteritems()])
                    gps_converted_timestamps = gps_converted_datetimes.apply(lambda t: t.timestamp() * 1000)
                    
                    results[gps_sensor].loc[:, 'local_timestamp'] = gps_converted_timestamps.values
                    try:
                        results[gps_sensor].loc[:, 'local_datetime'] = gps_converted_datetimes.dt.tz_localize(None).values
                    except:
                        results[gps_sensor].loc[:, 'local_datetime'] = pd.Series([dt.replace(tzinfo=None) for dt in gps_converted_datetimes.values])

                    results[gps_sensor].reset_index(drop=True, inplace=True)

                if dom == gps_sensor: continue
                    
                matched_gps_readings = results[dom]['UTC_timestamp'].apply(lambda t: results[gps_sensor].loc[(results[gps_sensor]['UTC_timestamp'] - t).idxmin, 'timezone'])
                converted_datetimes = pd.Series([datetime.datetime.fromtimestamp(t/1000, tz=pytz.timezone(matched_gps_readings[idx])) for idx, t in results[dom]['UTC_timestamp'].iteritems()])

            else:
                tz = pytz.timezone(datetime.datetime.now(tzlocal()).tzname()) #pytz.timezone('America/New_York')
                matched_gps_readings = pd.Series([tz] * len(results[dom]))
                converted_datetimes = results[dom]['UTC_timestamp'].apply(lambda t: datetime.datetime.fromtimestamp(t/1000, tz=tz))


            converted_timestamps = converted_datetimes.apply(lambda t: t.timestamp() * 1000)
            
            results[dom].loc[:, 'timezone'] = matched_gps_readings
            results[dom].loc[:, 'local_timestamp'] = converted_timestamps.values
            results[dom].loc[:, 'local_datetime'] = converted_datetimes.dt.tz_localize(None).values
            results[dom].reset_index(drop=True, inplace=True)

    def create_df(self, 
                  days_cap=120, 
                  day_first=None, 
                  day_last=None, 
                  resolution=datetime.timedelta(days=1), 
                  start_monday=False, 
                  start_morning=True, 
                  time_centered=False, 
                  question_categories=None):
        """
        Create participant dataframe
        :param day_first (datetime.Date)
        """

        sensors = self.sensor_results(self.id) # sensor SensorEvents
        cognitive_games = self.cognitive_game_results(self.id) #cognitive game ActivityEvents
        surveys = self.survey_results(self.id, question_categories=question_categories) #survey ActivityEvents
        
        results = {**surveys, **sensors, **cognitive_games} 
        
        self.timezone_correct(results)

        #Save data
        self.survey_events = surveys
        self.sensor_events = sensors
        self.result_events = results
        
        #If no data, return empty dataframe
        if len(results) == 0: return pd.DataFrame({})

        #Find the first, last date
        concat_datetimes = pd.concat([results[dom] for dom in results])['local_datetime'].sort_values()
        if day_first is None: day_first = concat_datetimes.min()
        else: day_first = datetime.datetime.combine(day_first, datetime.time.min) #convert to datetime

        if day_last is None: day_last = concat_datetimes.max()
        else: day_last = datetime.datetime.combine(day_last, datetime.time.min) #convert to datetime

        #Clip days based on morning and weekday parameters
        if start_monday:
            if day_first.weekday() > 0: 
                day_first += datetime.timedelta(days = - day_first.weekday())

        if start_morning: 
            day_first, day_last = day_first.replace(hour=9, minute=0, second=0), day_last.replace(hour=9, minute=0, second=0)
            
        days_elapsed = (day_last - day_first).days 
        
        #Create based on resolution
        date_list = [day_first + (resolution * x) for x in range(0, math.ceil(min(days_elapsed, days_cap) * datetime.timedelta(days=1) / resolution))]

        #Create dateframe for the number of time units that have data; limited by days; cap at 'days_cap' if this number is large
        df = pd.DataFrame({'Date': date_list, 'id':self.id})

        # Short circuit if no dates to parse
        if len(df['Date']) == 0: return df

        ### Featurize result events and add to df
        #Surveys
        surveyDf = lamp_cortex.activities.survey_features.featurize(surveys, date_list, resolution=resolution)
        
        #Jewels
        jewelsDf = lamp_cortex.activities.jewels_features.featurize(results, date_list, resolution=resolution)

        #Parse sensors and convert them into passive features
        #Single sensor features
        callTextDf = lamp_cortex.sensors.call_text_features.all(results, date_list, resolution=resolution)
        accelDf = lamp_cortex.sensors.accelerometer_features.all(results, date_list, resolution=resolution)
        gpsDf = lamp_cortex.sensors.gps_features.all(sensors, date_list, resolution=resolution)
        #screenDf = lamp_cortex.sensors.screen_features.all(sensors, date_list, resolution)

        # #Merge dfs
        df = reduce(lambda left, right: pd.merge(left, right, on=["Date"], how='left'), 
                    [surveyDf, jewelsDf, accelDf, callTextDf, gpsDf]) #screenDf])

        #Trim columns if there are predetermined domains
        if self.domains is not None: 
            df = df.loc[:, ['Date', 'id'] + [d for d in self.domains if d in df.columns.values]]

        return df

 
    def impute(self, domains):
        """
        Get value for each column for each window
        """
        if self.impute_status:
            print('Dataframe already imputed.')
            return

        weighted_dict = [0.05, 0.20, 0.40, 1.5, 0.4, 0.20, 0.05]

        #Get indices of all middle bin values; add them to new df
        for dom in domains:
            if dom not in self.df:
                continue

            dom_values = []

            for ind in range(len(self.df.index)):

                #Get indices
                middle_weight_index = 3
                starting_index = max(ind -3, 0)
                ending_index = min(ind + 4, 90)

                #Get slice values
                subj_slice = self.df.iloc[starting_index:ending_index]

                #Remove na
                subj_slice_no_nan = subj_slice[dom].dropna()
                slice_indices = subj_slice_no_nan.index

                if len(slice_indices) == 0:
                    dom_values.append(np.nan)
                    continue

                #Match slice index with weight index
                weighted_dict_vals = [weighted_dict[middle_weight_index - (ind - slice_i)] for slice_i in slice_indices]

                #Find total in bin
                slice_val = sum(subj_slice_no_nan * [val / sum(weighted_dict_vals) for val in weighted_dict_vals])
                dom_values.append(slice_val)

            self.df[dom] = dom_values

        self.impute_status = True

    def normalize(self, domains, domain_means={}, domain_vars={}):
        """
        Normalize columns values to 0 mean/ unit variance
        :param domain_means (dict): the mean for each column value
        :param domain_vars (dict): the variance for each column value
        If mean/var not provided, resort to in-sample normalization
        """
        if self.normalize_status: return
 
        domains = self.domain_check(domains)
        if domain_means == {} and domain_vars == {}:
            for dom in domains:
                if dom in self.df.columns:
                    domain_means[dom] = self.df[dom].mean()
                    domain_vars[dom] = self.df[dom].std()

        for dom in domains:
            if dom in self.df.columns and dom in domain_means and dom in domain_vars:
                self.df[dom] = (self.df[dom] - domain_means[dom]) / domain_vars[dom]

            self.normalize_status = True

    def create_transition_dict(self, level):
        """
        Create nested dictionary structure 
        :param level (int): the level dictionary structure. Must be >= 0
        """
        trans_dict = {}
        for comb in itertools.product(('elevated', 'stable'), repeat=level):
            trans_dict[comb] = {comb2:0 for comb2 in itertools.product(('elevated', 'stable'), repeat=level)}
        return trans_dict


    def assign_transition_dict(self, trans_dict, row, row2):
        """
        Increment transition dict
        """
        label1 = tuple(['stable' if col < 1.0 else 'elevated' for col in row])
        label2 = tuple(['stable' if col < 1.0 else 'elevated' for col in row2])
        trans_dict[label1][label2] += 1

    def get_transitions(self, domains=None, joint_size=1):
        """
        Count transition events for each col in subj_df
        """
        #domains = self.domain_check(domains)
        if domains == None:
            domains = self.df.loc[:, ~self.df.columns.isin(['Date', 'id'])].columns.values

        all_trans_dict = {}
        for dom_group in itertools.combinations(domains, r=joint_size):

            #Create trans dictionary
            group_dict = self.create_transition_dict(level=joint_size)

            #Find bins with values for each group
            df_nona = self.df.loc[:, list(dom_group)].dropna()

            #Assign
            row_iterator = df_nona.iterrows()
            try:
                last_i, last = next(row_iterator)
            except StopIteration:
                continue
            for index, row in row_iterator:
                if int(index) - int(last_i) <= 3:
                    self.assign_transition_dict(group_dict, last, row)
                last_i, last = index, row

            all_trans_dict[dom_group] = group_dict

        return all_trans_dict

    def domain_bouts(self, domains=None):
        """
        """
        def parse_bout_list(bout_list, state, stable_bouts, elevated_bouts):
            """
            Helper function to parse bout list at end of bout
            """
            if len(bout_list) == 1: bout_list.append(bout_list[-1] + 3) #edge case where last domain event is only one in its bout

            if state: stable_bouts.append(float(bout_list[-1]) - float(bout_list[0]))
            else: elevated_bouts.append(float(bout_list[-1]) - float(bout_list[0]))
            return stable_bouts, elevated_bouts

        #domains = self.domain_check(domains)
        if domains == None:
            domains = self.df.loc[:, ~self.df.columns.isin(['Date', 'id'])].columns.values

        bout_dict = {}
        for dom in domains:
            if dom not in self.df:
                continue

            bout_list = [] #temporary list that contains times of current bout
            subj_dom = self.df.loc[self.df[dom].notnull(), dom]
            row_iterator = subj_dom.iteritems()
            try:
                last_day, last_val = next(row_iterator)
                bout_list.append(last_day)
                if last_val < 1.0: last_state = True #set this back on first val
                else: last_state = False
            except StopIteration:
                continue

            bout_dict[dom] = {}
            stable_bouts, elevated_bouts = [], [] #duration of all in-range bouts
            stable_bouts_end, elevated_bouts_end = 0, 0 #counter the keep track of # of ended bout things
            for day, val in row_iterator:
                if val < 1.0: state = True
                else: state = False

                if last_state == state and day - last_day <= 6: #continue bout
                    bout_list.append(day)

                else: #discontinue bout
                    if day - last_day > 8: 
                        bout_list.append(last_day + 3) #If adjacent rows are day outside threshold, discontinue bout;cap last bout at 3 days past last activity	
                        if last_state: stable_bouts_end += 1
                        else: elevated_bouts_end += 1
                    else: bout_list.append(day) #then normal switch

                    stable_bouts, elevated_bouts = parse_bout_list(bout_list, last_state, stable_bouts, elevated_bouts)
                    bout_list = [day]

                last_day, last_val = day, val
                last_state = state

            stable_bouts, elevated_bouts = parse_bout_list(bout_list, last_state, stable_bouts, elevated_bouts) #parse last bout
            bout_dict[dom]['stable'], bout_dict[dom]['elevated'] = [float(b) for b in stable_bouts], [float(b) for b in elevated_bouts]
            bout_dict[dom]['stable ends'], bout_dict[dom]['elevated ends'] = stable_bouts_end, elevated_bouts_end

        return bout_dict