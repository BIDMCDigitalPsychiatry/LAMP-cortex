import LAMP 

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
