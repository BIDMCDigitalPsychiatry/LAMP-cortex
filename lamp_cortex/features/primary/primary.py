import LAMP
import lamp_cortex

def primary_feature(name, sensors):
    def _wrapper1(func):
        def _wrapper2(*args, **kwargs):
            print("Something is happening before the function is called. " + arg1)
            #Get previously calculated primary feature results from attachments 
            try: 
                attachments=LAMP.Type.get_attachment(kwargs[participant_id],name)['data']
                attachments.remove(max(attachments, key=lambda x:x['end'])) #remove last in case interval still open 
                _from=max(a['end'] for a in attachments)
            except LAMP.ApiException:
                attachments=[]
                _from=0
            print(attachments)
            #Get new sensor data  
            sensor_data=lamp_cortex.ParticipantExt.sensors_results(participant_id, _from=_from) #ADD ORIGIN AND LOOP?
            
            #Calculate new primary features
            body_df=func(*args, **{**kwargs, 'cache':sensor_data})
            body_df.loc[:,['start','end']]=body_df.loc[:,['start','end']].applymap(lambda t: int(t.timestamp()*1000))

            #Upload new features as attachment
            body_new=list(body_df.to_dict(orient='index').values())
            attachment_key='cortex.'+primary_features[feature]+'.'+feature  #depends how it is named 
            body+=body_new
            LAMP.Type.set_attachment(participant, 'me', attachment_key=attachment_key, body=body)
        return _wrapper2
    return _wrapper1