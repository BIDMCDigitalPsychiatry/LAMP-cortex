from ..feature_types import primary_feature, log
from ..raw.survey import survey
import LAMP
import numpy as np
from itertools import groupby

@primary_feature(
    name="cortex.survey_scores",
    dependencies=[survey],
    attach=False
)
def survey_scores(question_categories=None, **kwargs):
    """
    Get survey scores
    """

    # Grab the list of surveys and ALL ActivityEvents which are filtered locally.
    activities = LAMP.Activity.all_by_participant(kwargs['id'])['data']
    surveys = {x['id']: x for x in activities if x['spec'] == 'lamp.survey'}
    _grp = groupby(survey(replace_ids=False, **kwargs)['data'], lambda x: (x['timestamp'], x['survey']))
    participant_results = [{
        'timestamp': key[0],
        'activity': key[1],
        'temporal_slices': list(group)
    } for key, group in _grp]
    
    # maps survey_type to occurence of scores 
    _survey_scores = {}
    for result in participant_results:
        
        # Make sure the activity actually exists and is not deleted (this was a server issue)
        if result['activity'] not in surveys:
            continue
        result_settings = surveys[result['activity']]['settings']

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
            
            else:
                log.info('skipping!!')
                continue #no valid score to be used
                
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
                if event['survey'] not in survey_result:
                    survey_result[event['survey']] = []

                if score:
                    survey_result[event['survey']].append(score)
                
        #log.info(survey_result)
        #add mean to each cat to master dictionary           
        for category in survey_result: 
            survey_result[category] = np.mean(survey_result[category])
            _event = {
                'category': surveys[category]['name'], 
                'timestamp': survey_time, 
                'score': survey_result[category] 
            }
            if category not in _survey_scores: 
                _survey_scores[category] = [_event]
            else: 
                _survey_scores[category].append(_event)

    return [j for i in _survey_scores.values() for j in i]
