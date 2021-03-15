from inspect import getargspec
import LAMP
import lamp_cortex
from pprint import pprint

# A list of all functions across the package that are declared with @primary_feature.
__primary_features__ = []

def primary_feature(name, dependencies):
    """
    Some explanation of how to use this decorator goes here.
    """
    def _wrapper1(func):
        __primary_features__.append(func)

        def _wrapper2(*args, **kwargs):

            # Verify all required parameters for the primary feature function.
            params = [
                
                # These are universally required parameters for all feature functions.
                'id', 'start', 'end',
                
                # These are the feature function's required parameters after removing parameters
                # with provided default values, if any are provided.
                *getargspec(func)[0][:-len(getargspec(func)[3] or ()) or None]
            ]
            for param in params:
                assert kwargs.get(param, None) is not None, "parameter `" + param + "` is required but missing"
            print(f"-> Processing primary feature \"{name}\"...")

            # Get previously calculated primary feature results from attachments.
            try: 
                attachments = LAMP.Type.get_attachment(kwargs['id'], name)['data']
                # remove last in case interval still open 
                attachments.remove(max(attachments, key=lambda x: x['end']))
                _from = max(a['end'] for a in attachments)
            except LAMP.ApiException:
                attachments = []
                _from = 0

            # Get new sensor data and calculate new primary features.
            # FIXME: ADD ORIGIN AND LOOP?
            sensor_data = lamp_cortex.sensors.results(kwargs['id'], origin=dependencies[0], _from=_from) 
            _result = func(*args, **{ **kwargs, 'sensor_data': sensor_data })

            # Upload new features as attachment.
            #_result.loc[:,['start','end']]=_result.loc[:,['start','end']].applymap(lambda t: int(t.timestamp()*1000))
            #body_new=list(_result.to_dict(orient='index').values())
            #LAMP.Type.set_attachment(participant, 'me', attachment_key=name, body=body_new)

            return _result
        return _wrapper2
    return _wrapper1
