from ..feature_types import primary_feature
from ..raw.survey import survey
import LAMP
import numpy as np

@primary_feature(
    name="cortex.survey_scores",
    dependencies=[survey]
)
def survey_scores(question_categories=None, **kwargs):
    """
    Get survey scores
    """
    participant_results = survey(**kwargs)
    _survey_scores = {} #maps survey_type to occurence of scores 
    for result in participant_results:
        #Check if it's a survey event
        
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
            _event = {'timestamp':survey_time, 'score':survey_result[category]}
            if category not in _survey_scores: 
                _survey_scores[category] = [_event]
            else: 
                _survey_scores[category].append(_event)

    return _survey_scores