import datetime
import pandas as pd
from functools import reduce
import LAMP

def all_(participant):
    
#     jewels_a_events, jewels_b_events = [], []
#     game_id = 1
#     activity_events = LAMP.ActivityEvent.all_by_participant(participant)['data']
#     for event in activity_events:
#         if len(LAMP.Activity.view(event['activity'])['data']) == 0:
#             continue
            
#         activity = LAMP.Activity.view(event['activity'])['data'][0]
#         if activity['spec'] == 'lamp.jewels_a':
#             event['game_id'] = game_id 
#             print(event)
#             game_id += 1
#             jewels_a_events.append(event)
            
#         if activity['spec'] == 'lamp.jewels_b':
#             event['game_id'] = game_id 
#             game_id += 1
#             jewels_b_events.append(event)
    
#     jewelsADf = pd.DataFrame.from_dict(jewels_a_events)
#     jewelsBDf = pd.DataFrame.from_dict(jewels_b_events)
    
#     jewelsADf.to_csv('/home/ryan/LAMP-cortex/sample_jewels_a.csv')
#     jewelsBDf.to_csv('/home/ryan/LAMP-cortex/sample_jewels_b.csv')

    jewelsADf = pd.read_csv('/home/ryan/LAMP-cortex/sample_jewels_a.csv')
    jewelsBDf = pd.read_csv('/home/ryan/LAMP-cortex/sample_jewels_b.csv')
    
    ## 11. beta value
    ## 11.1 transform the raw data to a format required in survival analysis (censored or not, number of mistakes)
    # the function filters out games with level<6
    
    #Select unique game ids
    jewels_data = []
    max_level = 25
    for game_id, gameDf in jewelsADf.groupby('game_id'):
        temp = eval(gameDf["temporal_slices"][gameDf.index[0]])#.tolist()

        level = sum([1 for t in temp if t['type']]) + 1
        if level < 6: continue
        
        mistakes = 0
        t = 0
        for act in temp: 
            t += act['duration']
            if act['type']: #then correct touch;
                jewels_data.append([game_id, level, t, 1, mistakes])
            else:
                mistakes += 1
            
            if level < max_level: #Normalize to 25 jewels
                for l in range(level + 1, max_level):
                    t += 100
                    jewels_data.append([game_id, level, t, 0, mistakes])
    
    gamesDf = pd.DataFrame(jewels_data, columns=['game_id','game_lv','time','status','mistakes'])
    
    ## 11.2 create a reference group (which is the baseline for every analysis, keep it fixed) and 
    # append the pseudo data at the end of surv_data
    m = 25
    pseudo = pd.DataFrame([[0, m, list(range(1000, 1000*m, 1000)), 1, 0]], columns=['game_id','game_lv','time','status','mistakes'])
    
    all_dataDf = pd.concat([pseudo, gamesDf])
    print(all_dataDf)
    
#     add_reference = function(surv_data){
#       m = 25
#       pseudo = cbind(0,m,seq(1000,1000*m,1000),1,0)
#       pseudo=data.frame(pseudo)
#       colnames(pseudo)=c('game_id','game_lv','time','status','mistakes')
#       all_data = rbind(pseudo,surv_data)
#       all_data$game_id=as.numeric(as.character(all_data$game_id))
#       all_data
#     }

        
        
def test1():
    LAMP.connect("admin", "LAMPLAMP")
    studies =  [study['id'] for study in LAMP.Study.all_by_researcher("rzhd6cwztfqw0tagx0s5")['data']]

    participants = reduce(lambda x, y: x + [part['id'] for part in LAMP.Participant.all_by_study(y)['data']], 
                     studies[1:], 
                     [part['id'] for part in LAMP.Participant.all_by_study(studies[0])['data']])
    
    all_(participants[1])
    
    
    
    
if __name__ == "__main__":
    test1()

    
    
