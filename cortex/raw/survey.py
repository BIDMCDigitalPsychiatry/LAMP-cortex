from ..feature_types import raw_feature
import LAMP

@raw_feature(
    name='lamp.survey',
    dependencies=['lamp.survey']
)
def survey(limit=2147483647, **kwargs):
    """
    Get survey events for participant
    
    :param participant (str): the LAMP ID for participant. If not provided, then take participant id
    :param question_categories (dict): maps text in active event responses to a domain (str) and reverse_scoring parameter (bool)
    """
    participant_activities = LAMP.Activity.all_by_participant(kwargs['id'], _limit=limit)['data']
    participant_activities_surveys = [activity for activity in participant_activities if activity['spec'] == 'lamp.survey'] 
    participant_activities_surveys_ids = [survey['id'] for survey in participant_activities_surveys]        
    
    raw_results = LAMP.ActivityEvent.all_by_participant(
                                kwargs['id'],
                                _from= kwargs['start'],
                                to= kwargs['end'],
                                _limit=limit
                            )['data']
    participant_results = [result for result in raw_results if 'activity' in result and result['activity'] in participant_activities_surveys_ids and len(result['temporal_slices']) > 0]
    return participant_results
    

