import LAMP
import lamp_cortex

def primary_feature(name, sensors):
    def _wrapper1(func):
        def _wrapper2(*args, **kwargs):
            participant_id = args[0]
            #Get previously calculated primary feature results from attachments 
            try: 
                attachments=LAMP.Type.get_attachment(participant_id, name)['data']
                attachments.remove(max(attachments, key=lambda x:x['end'])) #remove last in case interval still open 
                _from=max(a['end'] for a in attachments)
            except LAMP.ApiException:
                attachments=[]
                _from=0

            #Get new sensor data  
            sensor_data = lamp_cortex.sensors.results(participant_id, origin=sensors, _from=_from) #ADD ORIGIN AND LOOP?
            
            #Calculate new primary features
            body_df=func(*args, **{**kwargs, 'sensor_data':sensor_data})
            body_df.loc[:,['start','end']]=body_df.loc[:,['start','end']].applymap(lambda t: int(t.timestamp()*1000))

            #Upload new features as attachment
            body_new=list(body_df.to_dict(orient='index').values())
            attachment_key = name  #depends how it is named 
            body += body_new
            print(body)
            #LAMP.Type.set_attachment(participant, 'me', attachment_key=attachment_key, body=body)
        return _wrapper2
    return _wrapper1