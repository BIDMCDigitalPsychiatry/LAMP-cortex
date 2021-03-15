from inspect import getargspec
import LAMP
import lamp_cortex

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
            #try: 
            #    attachments = LAMP.Type.get_attachment(kwargs['id'], name)['data']
            #    # remove last in case interval still open 
            #    attachments.remove(max(attachments, key=lambda x: x['end']))
            #    _from = max(a['end'] for a in attachments)
            #except LAMP.ApiException:
            #    attachments = []
            #    _from = 0

            # Get all sensor data bounded by time interval per dependency to calculate new primary features.
            sensor_data = { sensor: LAMP.SensorEvent.all_by_participant(
                kwargs['id'],
                origin=sensor,
                _from=kwargs['start'],
                to=kwargs['end'],
                _limit=2147483647 # INT_MAX
            )['data'] for sensor in dependencies }
            _result = func(*args, **{**kwargs, 'sensor_data': sensor_data})
            _event = { 'timestamp': kwargs['start'], 'duration': kwargs['end'] - kwargs['start'], 'data': _result }

            # Upload new features as attachment.
            #_result.loc[:,['start','end']]=_result.loc[:,['start','end']].applymap(lambda t: int(t.timestamp()*1000))
            #body_new=list(_result.to_dict(orient='index').values())
            #LAMP.Type.set_attachment(participant, 'me', attachment_key=name, body=body_new)

            return _event
        return _wrapper2
    return _wrapper1
