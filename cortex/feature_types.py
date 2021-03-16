import os
import LAMP
from inspect import getargspec

from ..raw import sensors_results, cognitive_games_results, surveys_results

# List all registered features (raw, primary, secondary).
__features__ = []
def all_features():
    return __features__

# Raw features.
def raw_feature(name, dependencies):
    """
    Some explanation of how to use this decorator goes here.
    """
    def _wrapper1(func):
        __features__.append({ 'name': name, 'type': 'raw', 'dependencies': dependencies, 'callable': func })

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
            print(f"-> Processing raw feature \"{name}\"...")

            # Connect to the LAMP API server.
            assert 'LAMP_ACCESS_KEY' in os.environ and 'LAMP_SECRET_KEY' in os.environ, "You must configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY` to use Cortex."
            LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'))

            # Get all sensor data bounded by time interval per dependency to calculate new primary features.
            assert check_something(), "Incorrect data"
            sensor_data = { sensor: LAMP.SensorEvent.all_by_participant(
                kwargs['id'],
                origin=sensor,
                _from=kwargs['start'],
                to=kwargs['end'],
                _limit=2147483647 # INT_MAX
            )['data'] for sensor in dependencies }
            _result = func(*args, **{**kwargs, 'sensor_data': sensor_data})
            _event = { 'timestamp': kwargs['start'], 'duration': kwargs['end'] - kwargs['start'], 'data': _result }

            return _event
        return _wrapper2
    return _wrapper1

# Primary features.
def primary_feature(name, dependencies):
    """
    Some explanation of how to use this decorator goes here.
    """
    def _wrapper1(func):
        __features__.append({ 'name': name, 'type': 'primary', 'dependencies': dependencies, 'callable': func })

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

            # Connect to the LAMP API server.
            assert 'LAMP_ACCESS_KEY' in os.environ and 'LAMP_SECRET_KEY' in os.environ, "You must configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY` to use Cortex."
            LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'))

            # TODO: Require primary feature dependencies to be raw features!

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

# Secondary features.
def secondary_feature(name, dependencies):
    """
    Some explanation of how to use this decorator goes here.
    """
    def _wrapper1(func):
        __features__.append({ 'name': name, 'type': 'secondary', 'dependencies': dependencies, 'callable': func })

        def _wrapper2(*args, **kwargs):

            # Verify all required parameters for the primary feature function.
            params = [
                
                # These are universally required parameters for all feature functions.
                'id', 'start', 'end', 'resolution'
                
                # These are the feature function's required parameters after removing parameters
                # with provided default values, if any are provided.
                *getargspec(func)[0][:-len(getargspec(func)[3] or ()) or None]
            ]
            for param in params:
                assert kwargs.get(param, None) is not None, "parameter `" + param + "` is required but missing"
            print(f"-> Processing secondary feature \"{name}\"...")

            # Connect to the LAMP API server.
            assert 'LAMP_ACCESS_KEY' in os.environ and 'LAMP_SECRET_KEY' in os.environ, "You must configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY` to use Cortex."
            LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'))

            timestamp_list = list(range(kwargs['start'], kwargs['end'], kwargs['resolution']))
            # TODO: Require primary feature dependencies to be primary features (or raw features?)!

            _result = func(*args, **{**kwargs, 'timestamp_list':timestamp_list})
            #_event = { 'timestamp': kwargs['start'], 'duration': kwargs['end'] - kwargs['start'], 'data': _result }

            return _result
        return _wrapper2
    return _wrapper1
