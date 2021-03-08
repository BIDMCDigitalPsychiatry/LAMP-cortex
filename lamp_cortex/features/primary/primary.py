import lamp_cortex
#from trips import SENSORS as 
def primary(participant_id, attachment_key, process_fn):
    """
    Performs total primary featurization
    """

    #Attachments
    attachments = get_attachments()
    
    #Lookup SECOND MOST recent timestamp
    req_timestamps = recent_timestamp(attachments)

    req_sensors = "FIXME" #GET SENSORS FOR FN, DEFINED IN ITS FILE

    #Get needed sensor data
    data = []
    for sensor in req_sensors:
        #How to import relevant sensor file using name "sensor"?
        sens_data = lamp_cortex.sensors.     .results(req_timestamps[sensor])
        data.append(sens_data)

    processed_data = process_fn(data)

    upload_attachments(processed_data)



def get_attachments():

def upload_attachments():