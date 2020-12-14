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
    
    # 11.3 run coxph model on the data, and record the results in a table and map the coef and var from 
    # different game levels to the same level using LMM the numbers are derived from the full data and 
    # the same numbers apply to every week. This step can be time consuming
    from lifelines import CoxPHFitter
    
    
    num_mistake = all_dataDf['mistakes'].max()
    if num_mistake == 0:
        all_dataDf.loc[:, 'cat_mistake'] = [0] * len(all_dataDf)
    elif num_mistake == 1:
        all_dataDf.loc[:, 'cat_mistake'] = [1] * len(all_dataDf)
    else: 
        all_dataDf.loc[:, 'cat_mistake'] = [2] * len(all_dataDf)
        
    cph = CoxPHFitter()
    if len(all_dataDf['cat_mistake'].unique()) == 1:
        fit = cph.fit(all_dataDf,
                      duration_col='time',
                      event_col='status',
                      strata=['game_id'])
    elif len(all_dataDf['cat_mistake'].unique()) != 1 and num_stakes != 0:
        fit = cph.fit(all_dataDf,
              duration_col='time',
              event_col='status',
              strata=['game_id', 'cat_mistake'])
        
    elif len(all_dataDf['cat_mistake'].unique()) != 1 and num_stakes != 0:
        fit = cph.fit(all_dataDf,
              duration_col='time',
              event_col='status',
              strata=['game_id'])
        
    coef_vec = fit.params_
    var_vec = np.diag(fit.variance_matrix_)
    result = []
    uniq_id = all_dataDf['game_id'].unique()
    for i in uniq_id.values:
        temp = all_dataDf.loc[all_dataDf['game_id'] == i, :]
        num_mis = temp['mistakes'].max()
        tag = ''.join(['factor(game_id)', i])
            
            
    
    
    
    
    coxph_result = function(all_data,game){
#       num_mistake = max(all_data$mistakes)
#       if (num_mistake==0){all_data$cat_mistake=rep(0,nrow(all_data))}
#       if (num_mistake==1){all_data$cat_mistake=rep(1,nrow(all_data))}
#       if (num_mistake>=2){all_data$cat_mistake=rep(2,nrow(all_data))}
#       if(length(unique(all_data$cat_mistake))==1){
#         fit = coxph(Surv(time, status) ~ factor(game_id), data = all_data)
#       }
#       if(length(unique(all_data$cat_mistake))!=1 & num_mistake!=0){
#         fit = coxph(Surv(time, status) ~ factor(game_id) + factor(cat_mistake), data = all_data) 
#       }
#       if(length(unique(all_data$cat_mistake))!=1 & num_mistake==0){
#         fit = coxph(Surv(time, status) ~ factor(game_id), data = all_data) 
#       }
      coef_vec = fit$coefficients
      var_vec = diag(fit$var)
      result = c()
      uniq_id=unique(all_data$game_id)
      for(i in 1:(length(uniq_id)-1)){
        temp = subset(all_data, game_id == uniq_id[i+1])
        num_mis = max(temp$mistakes)
        tag = paste0('factor(game_id)',uniq_id[i+1])
        loc = which(names(coef_vec)==tag)
        result = rbind(result,c(uniq_id[i+1],temp$game_lv[1],coef_vec[loc],var_vec[loc],num_mis))
      }
      result=data.frame(result)
      colnames(result)=c('game_id','game_lv','coef','var','mistakes')
      result$game_id = as.numeric(as.character(result$game_id))
      result$game_lv = as.numeric(as.character(result$game_lv))
      result$coef = as.numeric(as.character(result$coef))
      result$var = as.numeric(as.character(result$var))
      result$mistakes = as.numeric(as.character(result$mistakes))
      if(game=='a'){
        a_coef = -0.069}
      if(game=='b'){
        a_coef = -0.161}
      max_level = 25
      result$adjusted_coef = result$coef + (max_level-result$game_lv)*a_coef
      if(length(coef_vec)==nrow(result)){
        result$final_est = result$adjusted_coef
        result$final_var = result$var
      }
      if(length(coef_vec)-nrow(result)==1){
        result$final_est = result$adjusted_coef+coef_vec[length(coef_vec)]*(result$mistakes==1)
        result$final_var = result$var + var_vec[length(coef_vec)]*(result$mistakes==1)
      }
      if(length(coef_vec)-nrow(result)==2){
        result$final_est = result$adjusted_coef+ 
          coef_vec['factor(cat_mistake)1']*(result$mistakes==1)+
          coef_vec['factor(cat_mistake)2']*(result$mistakes>1)
        result$final_var = result$var + 
          var_vec[nrow(result)+1]*(result$mistakes==1)+
          var_vec[nrow(result)+2]*(result$mistakes>1)
      }
      result
    }


        
        
def test1():
    LAMP.connect("admin", "LAMPLAMP")
    studies =  [study['id'] for study in LAMP.Study.all_by_researcher("rzhd6cwztfqw0tagx0s5")['data']]

    participants = reduce(lambda x, y: x + [part['id'] for part in LAMP.Participant.all_by_study(y)['data']], 
                     studies[1:], 
                     [part['id'] for part in LAMP.Participant.all_by_study(studies[0])['data']])
    
    all_(participants[1])
    
    
    
    
if __name__ == "__main__":
    test1()

    
    
