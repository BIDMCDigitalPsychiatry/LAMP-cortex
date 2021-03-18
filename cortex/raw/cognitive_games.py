import pandas as pd 
import LAMP

LAMP_COGNITIVE_GAMES = ['lamp.jewels_a', 'lamp.jewels_b']

def cognitive_games_results(func):
    """
    Get dictionary of jewels data
    """
    def decorator(*args, **kwargs):
        participant_id = args[0]

        if 'origin' not in kwargs:
            cognitive_games_to_query = LAMP_COGNITIVE_GAMES

        elif isinstance(kwargs['origin'], str):
            cognitive_games_to_query = [kwargs['origin']]

        else:
            cognitive_games_to_query = kwargs['origin']

        participant_cognitive_games = {}
        for cognitive_game in cognitive_games_to_query:
            cognitive_game_ids = [activity['id'] for activity in LAMP.Activity.all_by_participant(participant_id)['data'] if activity['spec'] in cognitive_games_to_query]
            if not cognitive_game_ids: continue 

            cognitive_game_id = cognitive_game_ids[0]
            cg_results = func(participant_id, origin=cognitive_game_id, **{k: kwargs[k] for k in kwargs if k != 'origin'})
            if not cg_results.empty:
                participant_cognitive_games[cognitive_game] = cg_results

        return participant_cognitive_games

    return decorator

@cognitive_games_results
def results(id, **kwargs):
    
    cognitive_game_results_new = [{'timestamp':res['timestamp'],
                                'duration':res['duration'],
                                'activity':res['activity'],
                                'activity_name':LAMP.Activity.view(res['activity'])['spec'], 
                                'static_data':res['static_data'], 
                                'temporal_slices':res['temporal_slices']} for res in LAMP.ActivityEvent.all_by_participant(id, **kwargs)['data']]

    cognitive_game_results = []
    while cognitive_game_results_new: 
        cognitive_game_results += cognitive_game_results_new
        kwargs['to'] = cognitive_game_results_new[0]['UTC_timestamp']
        cognitive_game_results_new = [{'timestamp':res['timestamp'],
                                'duration':res['duration'],
                                'activity':res['activity'],
                                'activity_name':LAMP.Activity.view(res['activity'])['spec'], 
                                'static_data':res['static_data'], 
                                'temporal_slices':res['temporal_slices']} for res in LAMP.ActivityEvent.all_by_participant(id, **kwargs)['data']]
        
    cognitiveGameDf = pd.DataFrame.from_dict(cognitive_game_results).drop_duplicates(subset='timestamp') #remove duplicates
    return cognitiveGameDf