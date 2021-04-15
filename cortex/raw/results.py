import LAMP 
import pandas as pd

LAMP_SENSORS = ["lamp.accelerometer", "lamp.accelerometer.motion", #"lamp.analytics", 
                    "lamp.blood_pressure", "lamp.bluetooth", "lamp.calls", "lamp.distance",
                    "lamp.flights", "lamp.gps", "lamp.gps.contextual", "lamp.gyroscope",
                    "lamp.heart_rate", "lamp.height", "lamp.magnetometer", "lamp.respiratory_rate",
                    "lamp.screen_state","lamp.segment", "lamp.sleep", "lamp.sms", "lamp.steps",
                    "lamp.weight", "lamp.wifi"]

def sensors_results(func):
    def decorator(*args, **kwargs):
        participant_id = args[0]
        if 'origin' not in kwargs:
            sensors_to_query = LAMP_SENSORS
    
        elif isinstance(kwargs['origin'], str):
            sensors_to_query = [kwargs['origin']]

        else:
            sensors_to_query = kwargs['origin']

        participant_sensors = {}
        for sensor in sensors_to_query:
            if '_limit' not in kwargs: kwargs['_limit'] = 25000
            sens_results = func(participant_id, origin=sensor, **{k: kwargs[k] for k in kwargs if k != 'origin'})
            if len(sens_results) > 0:
                participant_sensors[sensor] = sens_results

        #Edge case of lamp.gps.contextual
        # if 'lamp.gps.contextual' in participant_sensors and 'lamp.gps' not in participant_sensors:
        #     gps_context = participant_sensors['lamp.gps.contextual'].copy()
        #     if len(gps_context[['timestamp', 'latitude', 'longitude', 'accuracy']].dropna()) > 0:
        #         participant_sensors['lamp.gps'] = gps_context[['timestamp', 'latitude', 'longitude', 'accuracy']].dropna()

        return participant_sensors

    return decorator


@sensors_results
def results(id, **kwargs):
    """
    Get sensor events and put in Df
    """
    print(kwargs['origin'])
    sens_results_new = [{'timestamp':res['timestamp'], **res['data']} 
                        for res in LAMP.SensorEvent.all_by_participant(id, **kwargs)['data']]        
    # sens_results = [] 
    # while sens_results_new: 
    #     print(sens_results_new)
    #     sens_results += sens_results_new
    #     kwargs['to'] = sens_results_new[-1]['timestamp']
    #     sens_results_new = [{'timestamp':res['timestamp'], **res['data']} for res in LAMP.SensorEvent.all_by_participant(id, **kwargs)['data']]
        
    #sensorDf = pd.DataFrame.from_dict(sens_results).drop_duplicates(subset='timestamp') #remove duplicates
    return sens_results_new

