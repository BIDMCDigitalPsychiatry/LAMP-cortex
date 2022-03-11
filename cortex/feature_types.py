""" Module to hold wrapper functions for raw, primary, and secondary features as
    well as auxillary functions for attachments and caching """
import os
import sys
import json
import logging
import argparse
from pprint import pprint
import inspect
from inspect import getfullargspec
import tarfile
import re
import copy
import time
import compress_pickle as pickle
import numpy as np
import pandas as pd
import yaml
import LAMP
# Get a universal logger to share with all feature functions.
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                    format="[%(levelname)s:%(module)s:%(funcName)s] %(message)s")
log = logging.getLogger('cortex')

# List all registered features (raw, primary, secondary).
__features__ = []
def all_features():
    return __features__

ACTIVITIES = ['lamp.survey', 'lamp.jewels_a', 'lamp.jewels_b']
MAX_RETURN_SIZE = 10000 #maximum number of events that the API will return

# Raw features.
def raw_feature(name, dependencies):
    """Determines whether caching should be performed upon raw data request.

    Also adds data quality metrics to the results after the request is successfully completed.
    This function decorates all of the functions in module 'cortex.raw'.

    Args:
        name (string): The name of the raw data-getting method being decorated.
        dependencies (list): The names of cortex methods that are being use within.
        TODO: event_type (string): Either "activity" or "sensor"; the correct API method
            is chosen accordingly.
        **kwargs:
            id (string): The Participant LAMP id. Required.
            start (int): The UNIX timestamp (in ms) to begin querying (i.e. "_from"). Required.
            end (int): The UNIX timestamp to end querying (i.e. "to"). Required.
            cache (boolean): If True raw data will be loaded from and saved
                    into the cache directory.

    Returns:
        A dict with a timestamp (kwargs['start']), duration (kwargs['end'] - kwargs['start']),
        and data (the result of calling 'name') fields.
        Data quality metrics are also added (see docstring for '_raw_data_quality').
        Example:

        {'timestamp': 1585355933805,
         'duration': 600009,
         'data': [{'timestamp': 1585355993800,
                   'x': 1.35382
                   'y': 3.812935
                   'z': 1.00002},
                   ...
                 ],
         'fs_mean': 0.991,
         'fs_var': 0.411,
        }

    Raises:
        API Error (500). Too many requests were sent to the server.
    """
    def _wrapper1(func):
        def _wrapper2(*args, **kwargs):


            # Verify all required parameters for the primary feature function.
            params = [

                # These are universally required parameters for all feature functions.
                'id', 'start', 'end',

                # These are the feature function's required parameters after removing parameters
                # with provided default values, if any are provided.
                *getfullargspec(func)[0][:-len(getfullargspec(func)[3] or ()) or None]
            ]
            for param in params:
                if kwargs.get(param, None) is None:
                    raise Exception(f"parameter `{param}` is required but missing")

            if kwargs['start'] > kwargs['end']:
                raise Exception("'start' argument must occur before 'end'.")

            # Connect to the LAMP API server.
            if not 'LAMP_ACCESS_KEY' in os.environ or not 'LAMP_SECRET_KEY' in os.environ:
                raise Exception("You configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY`" +
                                " (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.")
            LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                         os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))

            # Find a valid local cache directory
            # Get defaults
            def _get_default_args(func):
                """ Get the default arguments for the function.

                    Args:
                        func: the function
                    Returns:
                        a dictionary with key value pairs for the default arguments
                """
                signature = inspect.signature(func)
                return {
                    k: v.default
                    for k, v in signature.parameters.items()
                    if v.default is not inspect.Parameter.empty
                }

            kwgs = _get_default_args(func)
            kwgs.update(kwargs)
            cache = kwgs.get('cache')

            def _raw_caching(name, **kwargs):
                """ Finds and returns cached data for raw features.

                For a cached file to be considered for use, it must completely contain the
                [kwargs['start'], kwargs['end']] interval. The first valid file found in
                the directory will be used and the data from which will be immediately returned.

                A compression method can be specified in the environment variable
                'CORTEX_CACHE_COMPRESSION'.

                Methods can be of type ['gz', 'bz2', 'lzma', 'zip']. Please see
                documentation for the package 'compress_pickle' for more information
                on compatible methods.

                Args:
                    func (method): The raw data-getting method, called if no valid cached data
                        is available. If called, the resuting data will itself be cached.
                    name (string): The raw data type; used when searching the cache directory
                        for valid files.
                    **kwargs:
                        id (string): The Participant LAMP id. Required.
                        start (int): The starting UNIX timestamp (in ms). The cached file
                            must enclose this timestamp. Required.
                        end (int): The ending UNIX timestamp. The cached file must enclode
                            this timestamp. Required

                Returns:
                    A list containing raw data of type 'name'.
                    Example:

                    [{'timestamp': 1584137124130,
                      'latitude':13.9023491984,
                      'longitude':32.109390505,
                      'altitude':100,
                      'accuracy':1},
                      ...]

                Raises:
                    Exception: 'CORTEX_CACHE_DIR' is not defined in your environment
                        variables. Please set it to a valid path, or disable caching.
                    Exception: 'Caching directory ({cache_dir}) found in enviornmental
                        variables does not exist. Please set 'CORTEX_CACHE_DIR' to a
                        valid path, or disbale caching.
                    Exception: Compression method specified in 'CORTEX_CACHE_COMPRESSION\'
                        does not exist.
                """
                if os.getenv('CORTEX_CACHE_DIR') is None:
                    raise Exception("'CORTEX_CACHE_DIR' is not defined in your environment"
                                        + " variables. Please set it to a valid path, or disable "
                                        + "caching.")
                cache_dir = os.path.expanduser(os.getenv('CORTEX_CACHE_DIR'))
                assert os.path.exists(cache_dir), ("Caching directory (" + cache_dir + ") found in"
                                " enviornmental variables does not exist. Please set "
                                "'CORTEX_CACHE_DIR' to a valid path, or disbale caching.")

                log.info("Cortex caching directory set to: " + cache_dir)
                log.info("Processing raw feature " + name + "...")

                # local data caching TODO: combine pickle window with API data
                for file in [f for f in os.listdir(cache_dir) if f[-7:] == '.cortex']: # .lamp
                    path = cache_dir + '/' + file

                    if not re.match('^' + name.split('.')[1], file):
                        continue

                    _, rest = re.split('^'+name.split('.')[1]+'_', file)
                    saved = dict(zip(['id', 'start', 'end'],
                                     re.split('.cortex$', rest)[0].split('_')))
                    saved['name'] = name.split('.')[1]
                    try:
                        saved['start'] = int(saved['start'])
                        saved['end'] = int(saved['end'])
                    except:
                        continue

                    if (saved['start'] <= kwargs['start'] and
                        saved['end'] >= kwargs['end'] and
                        saved['id'] == kwargs['id']):
                        # if no compression extension, use standard pkl loading
                        if file.split('.')[-1] == 'cortex':
                            _result = pickle.load(path,
                                                  set_default_extension=False,
                                                  compression=None)
                        else:
                            _result = pickle.load(path)

                        log.info('Using saved raw data...')
                        return _result
                # If a cached file could not be found, use function to get new data and save

                log.info('No saved raw data found, getting new...')


                _result = _get_raw_feature(func, name, **kwgs)
                pickle_path = (cache_dir + '/' +
                               name.split('.')[-1] + '_' +
                               kwargs['id'] + '_' +
                               str(kwargs['start']) + '_' +
                               str(kwargs['end']) + '.cortex')

                if os.getenv('CORTEX_CACHE_COMPRESSION') is not None:

                    assert os.getenv('CORTEX_CACHE_COMPRESSION') in ['gz', 'bz2', 'lzma', 'zip'], (
                        "Compression method for caching does not exist.")
                    pickle_path += '.' + os.getenv('CORTEX_CACHE_COMPRESSION')

                pickle.dump(_result,
                            pickle_path,
                            compression=kwargs.get('compression'),
                            set_default_extension=False)

                log.info("Saving raw data as " + pickle_path + "...")
                return _result

            #Get cached data if specified; otherwise get data via API request
            if cache:
                _result = _raw_caching(name=name, **kwgs)
            else:
                _result = _get_raw_feature(func, name, **kwgs)

            _event = {'timestamp': kwargs['start'],
                      'duration': kwargs['end'] - kwargs['start'],
                      'data': [r for r in _result if r['timestamp'] >= kwargs['start'] and
                               r['timestamp'] <= kwargs['end']]}

            # Add data quality metrics
            def _raw_data_quality(event, *args, **kwgs):
                """ Add data quality metrics to raw data event.

                    Data frequency is estimated as the number of data points over time
                    for each 10 minute interval between kwgs["start"] and kwgs["end"].
                    These frequency estimates can then be averaged to compute a global estimate.
                    The variance is taken to give a sense of how frequency varies over time.
                    For a more granualar estimate of data quality, please see the
                        feature 'cortex.secondary.data_quality'.


                    Args:
                        event (dict): The data.
                        kwgs (dict): Includes the start and end timestamps.
                        **kwgs:
                            id (string): The Participant LAMP id.
                            start (int): The UNIX timestamp (in ms) to begin querying
                                (i.e. "_from").
                            end (int): The UNIX timestamp to end querying (i.e. "to").

                    Returns:
                        A dict containing the fields:
                            fs_mean (float): An estimate of the data quality in Hz as the
                                number of datapoints divided by time.
                            fs_var (float): the variance in the mean data frequencies for
                                each ten minute window.

                """
                ten_minutes = 1000 * 60 * 10
                res = ten_minutes # set the window size
                idx = 0
                if len(event['data']) > 0:
                    start_time, end_time = kwgs['start'], kwgs["end"]
                    res_counts = np.zeros((len(range(end_time, start_time, -1 * res))))
                    if res_counts.shape[0] > 0:
                        for i, x in enumerate(range(end_time, start_time, -1 * res)):
                            while (idx + 1 < len(event['data']) and
                                   event['data'][idx]['timestamp'] > x - res):
                                res_counts[i] += 1
                                idx += 1
                        fs = res_counts / (res / 1000)
                        event["fs_mean"] = fs.mean()
                        event["fs_var"] = fs.var()
                    else:
                        event["fs_mean"] = len(event['data']) / (res / 1000)
                        event["fs_var"] = 0
                else:
                    event["fs_mean"] = 0
                    event["fs_var"] = 0

                return event

            _event = _raw_data_quality(_event, *args, **kwgs)

            return _event

        def _get_sensor_feature(name, **kwgs):
            """Function to call the LAMP.SensorEvent API and return data.

                Args:
                    name (str): the name of the raw feature (ex: "lamp.gps")
                    **kwgs:
                        id (str): the participant id
                        start (int): The UNIX timestamp (in ms) to begin querying (i.e. "_from")
                        end (int): The UNIX timestamp to end querying (i.e. "to")
                        _limit (int): The maximum number of sensor events to query for in a
                            single request
                        recursive (bool): if True, continue requesting data until all data is
                                returned; else just one request
                Returns:
                    A dict of the timestamps and raw data events
            """
            data_next = []
            data = LAMP.SensorEvent.all_by_participant(kwgs['id'],
                                               origin=name,
                                               _from=int(kwgs['start']),
                                               to=int(kwgs['end']),
                                               _limit=int(kwgs['_limit']))['data']
            while (kwgs['recursive'] and
                   (len(data) == MAX_RETURN_SIZE) or len(data_next) == MAX_RETURN_SIZE):
                to = data[-1]['timestamp']
                data_next = LAMP.SensorEvent.all_by_participant(kwgs['id'],
                                                        origin=name,
                                                        _from=int(kwgs['start']),
                                                        to=int(to),
                                                        _limit=int(kwgs['_limit']))['data']
                data += data_next
            # Special case for screen_ state and device state mapping to the same thing
            if name == "lamp.screen_state":
                data_next = []
                data_device_state = LAMP.SensorEvent.all_by_participant(kwgs['id'],
                                               origin="lamp.device_state",
                                               _from=int(kwgs['start']),
                                               to=int(kwgs['end']),
                                               _limit=int(kwgs['_limit']))['data']
                while (kwgs['recursive'] and
                       (len(data_device_state) == MAX_RETURN_SIZE) or len(data_next) == MAX_RETURN_SIZE):
                    to = data_device_state[-1]['timestamp']
                    data_next = LAMP.SensorEvent.all_by_participant(kwgs['id'],
                                                            origin="lamp.device_state",
                                                            _from=int(kwgs['start']),
                                                            to=int(to),
                                                            _limit=int(kwgs['_limit']))['data']
                    data_device_state += data_next
                data += data_device_state
            ret = [{'timestamp': x['timestamp'], **x['data']} for x in data]
            # Sort because of device_state / screen_state
            ret = (sorted(ret, key = lambda i: i['timestamp'], reverse=True))
            # some Androids have a motion field in accelerometer, unravel that
            if name == "lamp.accelerometer":
                ret = [{'timestamp': x['timestamp'], **x["motion"]} if "motion" in x else x for x in ret]
            return ret

        def _get_raw_feature(func, name, **kwgs):
            """ Function to call the LAMP API and get the raw data.

                Args:
                    func (method): The raw function to call. Needed if not a
                        sensor event.
                    name (str): The name of the raw feature (ex: "lamp.gps").
                    **kwgs:
                        id (str): The participant id
                        start (int): The UNIX timestamp (in ms) to begin querying (i.e. "_from")
                        end (int): The UNIX timestamp to end querying (i.e. "to")
                        _limit (int): The maximum number of sensor events to query for in a
                            single request
                        recursive (bool): if True, continue requesting data until all data is
                                returned; else just one request
                Returns:
                    A dict of the timestamps and raw data events
            """
            if name in ACTIVITIES:
                return func(**kwgs)
            else:
                return _get_sensor_feature(name, **kwgs)

        # When we register/save the function, make sure we
        # save the decorated and not the RAW function.
        _wrapper2.__name__ = func.__name__
        __features__.append({'name': name,
                             'type': 'raw',
                             'dependencies': dependencies,
                             'callable': _wrapper2})
        return _wrapper2
    return _wrapper1

# Primary features.
def primary_feature(name, dependencies):
    """Checks LAMP attachments to see if primary feature has previously processed data saved.

    Primary feature data in the appropriate [kwargs['start'], kwargs['end']] will be returned,
    and, if kwargs['attach'] is True, attachments will be updated.

    Args:
        name (string): The name of the primary feature-getting method being decorated.
        dependencies (list): The cortex.raw methods used to query sensor/activity data
            to be processed.
        **kwargs:
            id (string): The Participant LAMP id. Required.
            start (int): The UNIX timestamp (in ms) from which returned results are
                bound. (i.e. "_from"). Earier data may be processed in order to
                correctly updates attachments, but this out-of-bounds data will not
                be included in the return. Required.
            end (int): The UNIX timestamp (in ms) to end processing (i.e. "to"). Required.

    Returns:
        A dict with timestamp (kwargs['start']), duration (kwargs['end'] - kwargs['start']),
        and data (the result of calling 'name') fields. A 'has_raw_data' field is included,
        indicating whether there exists raw data to be processed in the
        [kwargs['start'], kwargs['end']] window.
        Example:

        {'timestamp': 1585346933781,
         'duration': 300000
         'data': [{'start': 1585347000000,
                   'end': 1585347013742,
                   'latitude': 47.34053109130787,
                   'longitude': -71.08687582117113,
                   'distance': 0.0192},
                   ...]
         'has_raw_data': 1
        }

    Raises:
        Exception: You must configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY`
            (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.
    """
    def _wrapper1(func):
        def _wrapper2(*args, **kwargs):

            # Verify all required parameters for the primary feature function.
            params = [

                # These are universally required parameters for all feature functions.
                'id', 'start', 'end',

                # These are the feature function's required parameters after removing parameters
                # with provided default values, if any are provided.
                *getfullargspec(func)[0][:-len(getfullargspec(func)[3] or ()) or None]
            ]
            for param in params:
                if kwargs.get(param, None) is None:
                    raise Exception(f"parameter `{param}` is required but missing")

            if kwargs['start'] > kwargs['end']:
                raise Exception("'start' argument must occur before 'end'.")

            # Connect to the LAMP API server.
            if not 'LAMP_ACCESS_KEY' in os.environ or not 'LAMP_SECRET_KEY' in os.environ:
                raise Exception("You must configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY`"
                                + " (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.")
            LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                        os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))

            log.info(f"Processing primary feature \"{name}\"...")
            # TODO: Require primary feature dependencies to be raw features!
            # -> Update: Not require but add a param to allow direct 2ndary to be calculated or not

            # Get previously calculated primary feature results from attachments, if you do attach.
            has_raw_data = -1

            def _get_default_args(func):
                """ Get the default arguments for the function.

                    Args:
                        func: the function
                    Returns:
                        a dictionary with key value pairs for the default arguments
                """
                signature = inspect.signature(func)
                return {
                    k: v.default
                    for k, v in signature.parameters.items()
                    if v.default is not inspect.Parameter.empty
                }

            kwgs = _get_default_args(func)
            kwgs.update(kwargs)

            def _primary_filter(_res, has_raw_data, **kwargs):
                """ Filter out primary feature results that do not belong in interval
                    [kwargs['start'], kwargs['end']].

                For each event in _res, only one of the {event['start'], event['end']}
                must be in the interval. Before that final filtering, only the two bounding
                events can have a start, ends that are outside the interval; these (start, end)
                points are changed to be kwargs['start'], kwargs['end'], respectively.

                *** NOTE: Currently we are not adjusting the event data based on the
                    (start, end adjustment).
                    E.g. if a trip is of time interval [1, 9], but is changed to be [3, 9]
                    because kwargs['start'] == 3, the distance traveled is not reduced to
                    reflect that lost time travelling. ***

                Args:
                    _res (list): The result returned by the primary featurization.
                    _has_raw_data (int): 1 if True; -1 else
                    **kwargs:
                        start (int): The start UNIX timestamp (in ms). All events in
                            _res that occur before this are filtered out.
                        end (int): The end UNIX timestamp. All events that occur after
                            this are filtered out.

                Returns:
                    A list of filtered primary feature events. The same format as
                        what primary feature results.
                """
                _body_new_copy = copy.deepcopy(_res)
                _event = { 'timestamp': kwargs['start'],
                           'duration': kwargs['end'] - kwargs['start'],
                           'data':
                            [b for b in _body_new_copy if
                                    ((b['start'] >= kwargs['start'] and b['end'] <= kwargs['end'])
                                  or (b['start'] < kwargs['start'] and
                                      kwargs['start'] < b['end'] <= kwargs['end'])
                                  or (kwargs['start'] < b['start'] < kwargs['end'] and
                                      b['end'] > kwargs['end']))],
                          'has_raw_data': has_raw_data }

                # make sure start and end match kwargs
                if len(_event['data']) > 0:
                    if _event['data'][0]['start'] < kwargs['start']:
                        _event['data'][0]['start'] = kwargs['start']
                        _event['data'][0]['duration'] = (_event['data'][0]['end']
                                                         - _event['data'][0]['start'])
                    if _event['data'][len(_event['data']) - 1]['end'] > kwargs['end']:
                        _event['data'][len(_event['data']) - 1]['end'] = kwargs['end']
                        _event['data'][len(_event['data']) - 1]['duration'] = (
                                    _event['data'][len(_event['data']) - 1]['end']
                                  - _event['data'][len(_event['data']) - 1]['start'])

                return _event

            def _primary_attach(func, name, *args, **kwargs):
                """Utilize and update LAMP attachments to speed up processing of primary feature.
                
                Based on both (kwargs['start'], kwargs['end']) timestamps and previously 
                saved attachments, primary featurization occurs and attachments are updated 
                to include these newly generated events.
                
                Args:
                    func (method): The raw data-getting method, called if attached data needs to
                        be updated.
                    **kwargs:
                        start (int): The start UNIX timestamp (in ms).
                        end (int): The end UNIX timestamp (in ms).

                Returns:
                    A list of both previously saved (in the the form of LAMP attachments) and newly generated 
                    primary feature events.
                    
                Raises:
                    LAMP.ApiException:
                """
                try:
                    attachments = LAMP.Type.get_attachment(kwargs['id'], name)['data']
                    # remove last in case interval still open
                    # but make sure there is data
                    if len(attachments) > 0:
                        attachments.remove(max(attachments, key=lambda x: x['end']))
                        _from = max(a['end'] for a in attachments)
                        if _from > kwargs['start'] and _from < kwargs['end']:
                            has_raw_data = 1
                    else:
                        _from = kwargs['end']
                    log.info(f"Using saved \"{name}\"...")
                except LAMP.ApiException:
                    attachments = []
                    _from = 0
                    log.info(f"No saved \"{name}\" found...")
                except Exception:
                    attachments = []
                    _from = 0
                    log.info("Saved " + name + " could not be parsed, discarding...")

                start = kwargs['start']
                if _from > kwargs['end']:
                    _result = []
                    has_raw_data = -1
                else:
                    _result = func(*args, **{**kwargs, 'start':_from})
                    if 'has_raw_data' in _result:
                        has_raw_data = _result['has_raw_data']
                    else:
                        has_raw_data = -1
                    _result = _result['data']

                # Combine old attachments with new results
                unique_dict = _result + attachments
                unique_dict = [k for j, k in enumerate(unique_dict) if k not in unique_dict[j + 1:]]
                _body_new = sorted((unique_dict),key=lambda x: x['start'])
                # need to use a copy so you don't overwrite the original
                _event = _primary_filter(_body_new, has_raw_data, *args, **kwargs)

                # Upload new features as attachment.
                log.info(f"Saving primary feature \"{name}\"...")
                LAMP.Type.set_attachment(kwargs['id'], 'me', attachment_key=name, body=_body_new)

                return _event

            attach = kwgs['attach']
            if attach:
                _event = _primary_attach(func=func, name=name, *args, **kwgs)

            else:
                has_raw_data = -1
                _result_init = func(*args, **kwgs)
                _result = _primary_filter(_result_init['data'],
                                          _result_init['has_raw_data'], *args, **kwgs)
                diff = [e for e in _result['data'] if e not in _result_init['data']]
                for d in diff:
                    if d['start'] < kwgs['start']:
                        print("START")
                    elif d['end'] > kwgs['end']:
                        if d['start'] < kwgs['end']:
                            print('BORDER')
                        else:
                            print("END")
                    else:
                        pass
                        #print("NEITHER", d, kwgs['start'], kwgs['end'])                

                if 'has_raw_data' in _result:
                    has_raw_data = _result['has_raw_data']
                _event = {'timestamp': kwgs['start'],
                          'duration': kwgs['end'] - kwgs['start'],
                          'data': _result['data'],
                          'has_raw_data': has_raw_data}

            return _event

        # When we register/save the function, make sure we save the
        # decorated and not the RAW function.
        _wrapper2.__name__ = func.__name__
        __features__.append({ 'name': name,
                             'type': 'primary',
                             'dependencies': dependencies,
                             'callable': _wrapper2 })
        return _wrapper2
    return _wrapper1

# Secondary features.
def secondary_feature(name, dependencies):
    """Creates windows of the specified temporal resolution and processes data accordingly.

    Secondary features are densely-represented time-series data. They depend on raw data and/or
    on primary features (which are sparsely-represented time-series data). E.g. when called for
    some time interval [t0, t1] with resolution "w", there will be math.floor((t1 - t0) / w)
    values of (start, end) sequence:
    {(t0, t0 + w), (t0 + w, t0 + 2 * w), ..., (t0 + (math.floor((t1 - t2) / w) - 1) * w, t1)}

    Args:
        name (string): The name of the secondary feature-processing method being decorated.
        dependencies (list): The cortex.primary, cortex.raw methods used to query
            the sensor/activity features needed for processing.
        **kwargs:
            id (string): The Participant LAMP id. Required.
            start (int): The UNIX timestamp (in ms) from which returned results are
                bound (i.e. "_from"). The first temporal window starts at this
                timepoint. Required.
            end (int): The UNIX timestamp (in ms) to end processing (i.e. "to").
                The last temporal window ends at this timepoint. Required.
            resolution: The duration (in ms) of each requested time window. Required.

    Returns:
        A dict with a timestamp (kwargs['start']), duration (kwargs['end'] - kwargs['start']),
        and data (the result of calling 'name') fields.
        Example:

        {'timestamp': 1585346933781,
         'duration': 604800
         'data': [{'timestamp': 1585346933781, 'value': 11.93,},
                  {'timestamp':1585347020181 ,'value': 15.50},
                  ...,
                  {'timestamp':1585347452181, 'value': 13.32}]
        }

    Raises:
        Exception: You must configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY`
            (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.
    """
    def _wrapper1(func):
        def _wrapper2(*args, **kwargs):

            # Verify all required parameters for the primary feature function.
            params = [

                # These are universally required parameters for all feature functions.
                'id', 'start', 'end', 'resolution',

                # These are the feature function's required parameters after removing parameters
                # with provided default values, if any are provided.
                *getfullargspec(func)[0][:-len(getfullargspec(func)[3] or ()) or None]
            ]
            for param in params:
                if kwargs.get(param, None) is None:
                    raise Exception("parameter `" + param + "` is required but missing")

            if kwargs['start'] > kwargs['end']:
                raise Exception("'start' argument must occur before 'end'.")

            # Connect to the LAMP API server.
            if not 'LAMP_ACCESS_KEY' in os.environ or not 'LAMP_SECRET_KEY' in os.environ:
                raise Exception("You must configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY`"
                                + " (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.")
            LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                        os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))

            log.info("Processing secondary feature " + name + "...")
            def _get_default_args(func):
                """ Get the default arguments for the function.

                    Args:
                        func: the function
                    Returns:
                        a dictionary with key value pairs for the default arguments
                """
                signature = inspect.signature(func)
                return {
                    k: v.default
                    for k, v in signature.parameters.items()
                    if v.default is not inspect.Parameter.empty
                }

            kwgs = _get_default_args(func)
            kwgs.update(kwargs)
            timestamp_list = list(range(kwgs['start'], kwgs['end'], kwgs['resolution']))
            data = []
            for window in reversed([*zip(timestamp_list[:-1], timestamp_list[1:])]):
                window_start, window_end = window[0], window[1]
                _result = func(**{**kwgs, 'start':window_start, 'end':window_end})
                data.append(_result)

            # TODO: Require primary feature dependencies to be primary features (or raw features?)!
            data = sorted(data,key=lambda x: x['timestamp']) if data else []
            _event = {'timestamp': kwgs['start'],
                      'duration': kwgs['end'] - kwgs['start'],
                      'resolution':kwgs['resolution'],
                      'data': data}

            return _event
        # When we register/save the function, make sure we save the decorated
        # and not the RAW function.
        _wrapper2.__name__ = func.__name__
        __features__.append({ 'name': name,
                             'type': 'secondary',
                             'dependencies': dependencies,
                             'callable': _wrapper2 })
        return _wrapper2
    return _wrapper1

### Auxilliary functions ###

## Attach ##

def delete_attach(participant, features=None):
    """
    Deletes all saved primary features for a participant (requires LAMP-core 2021.4.7 or later)
    :param participant (str): LAMP id to reset for
    :param features (list): features to reset, defaults to all features (optional)
    """
    LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                 os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))
    attachments= LAMP.Type.list_attachments(participant)['data']
    if features is None: features=attachments
    for feature in attachments:
        if feature.startswith('cortex'):
            if feature in features:
                LAMP.Type.set_attachment(participant, 'me', attachment_key=feature, body=None)
                log.info("Reset " + feature + "...")

## Cache ##
def delete_cache(id, features=None, cache_dir=None):
    """
    Deletes all cached raw features for a participant (requires LAMP-core 2021.4.7 or later)
    :param participant (str): LAMP id to reset for
    :param features (list): features to reset, defaults to all features (optional)
    :param cache_dir (str): path to cache dir, where data will be deleleted
    """
    cache_dir = cache_finder(cache_dir)

    #Delete all 'features' in cache_dir for participant
    for file in [f for f in os.listdir(cache_dir) if f[-7:] == '.cortex']:  # .lamp
        path = cache_dir + '/' + file
        saved = dict(zip(['name', 'id', 'start', 'end'], file.split('.')[0].split('_')))
        if saved['name'] in features and saved['id'] == id:
            os.remove(path)

def export_cache(cache_dir=None, export_dir=None):
    """
    Exports cached raw features as compressive *.tar.gz (saved as *.lamp)
    :param cache_dir (str): path to cache dir, where data will be read from
    :param export_dir (str): path to export directory
    """
    cache_dir = cache_finder(cache_dir)
    #Export as *.tar.gz
    tar = tarfile.open('cache_' + str(int(time.time())*1000) + '.lamp', 'w:gz') # check if override?
    if export_dir is None:
        export_dir = os.path.expanduser(cache_dir)
    else:
        export_dir = os.path.expanduser()

    tar.add(cache_dir, 'cache_' + str(int(time.time())*1000) + '.lamp')
    tar.close()

def import_cache(cache_dir=None, import_dir=None):
    """
    Imports cached raw features from *.tar.gz (saved as *.lamp)
    :param cache_dir (str): path to cache dir, where data will be
    :param import_dir (str): path to import directory
    """
    #Export as *.tar.gz
    if import_dir is not None:
        assert os.path.exists(import_dir), ("Import cache could not be found."
                            " Please provide a existing path to import_dir.")
        try:
            cache = tarfile.open(import_dir, 'r:gz') # check if override?
        except tarfile.ReadError:
            raise ("Cache file was found but could not be read. Please"
                   " check that it is of proper type *.tz")

    else:
        cache_dir = cache_finder(cache_dir)
        #find any cache in the folder
        for f in os.listdir(cache_dir):
            if f.endswith('cortex'):
                try:
                    cache = tarfile.open(os.path.join(cache_dir, f), 'r:gz')
                    return cache
                except:
                    log.info("Found a file with extension '.cortex' in"
                             + " cache_dir, but unable to read.")

        raise Exception("No cache found in cache_dir. Please provide a cache to" +
                        " import via 'import_dir' or provide a 'cache_dir' which" +
                        " contains a importable cache.")


def cache_finder(cache_dir):
    """
    Helper function that finds the cache location
    """
    if cache_dir is not None:
        cache_dir = os.path.expanduser(cache_dir)
        assert os.path.exists(cache_dir), ("Caching directory (" + cache_dir +
                                ") specified as a keyword argument does not exist")
    elif os.getenv('CORTEX_CACHE_DIR') is not None:
        cache_dir = os.path.expanduser(os.getenv('CORTEX_CACHE_DIR'))
        assert os.path.exists(cache_dir), ("Caching directory (" + cache_dir +
                                ") found in enviornmental variables does not exist")
    elif cache_dir is None:
        cache_dir = os.path.expanduser('~/.cache/cortex')
        if not os.path.exists(cache_dir):
            log.info("Caching directory does not yet exist.")
            log.info("Creating default cache dir at ~/.cache/cortex")
            os.makedirs(cache_dir)
        assert os.path.exists(cache_dir), ("Error in default caching directory at ~/.cache/cortex."
                    + " Please specify an alternative locatiton as a keyword argument: 'cache_dir',"
                    + " or as an enviornmental variable: 'CORTEX_CACHE_DIR'")
    return cache_dir

# Allows execution of feature functions from the command line, with argument parsing.
def _main():
    superparser = argparse.ArgumentParser(prog="cortex",
                    description='Cortex data analysis pipeline for the LAMP Platform')
    superparser.add_argument('--version', action='version', version='Cortex 2021.3.1')
    superparser.add_argument('--format', dest='_format', choices=['json', 'csv', 'yaml'],
            help='the output format type (can also be set using the environment variable'
                             + ' CORTEX_OUTPUT_FORMAT)')
    superparser.add_argument('--access-key', dest='_access_key',
            help='the access key for the LAMP API Server (can also be set using the'
                             + ' environment variable LAMP_ACCESS_KEY)')
    superparser.add_argument('--secret-key', dest='_secret_key',
            help='the secret key for the LAMP API Server (can also be set using the'
                             + ' environment variable LAMP_SECRET_KEY)')
    superparser.add_argument('--server-address', dest='_server_address',
            help='the server address for the LAMP API Server (can also be set using the'
                             + ' environment variable LAMP_SERVER_ADDRESS)')
    subparsers = superparser.add_subparsers(title="features", dest='_feature', required=True,
                                            description="Available features for processing")
    funcs = {f['callable'].__name__: f['callable'] for f in all_features()}
    for name, func in funcs.items():

        # Add a sub-parser for this feature with the required (id, start, end).
        parser = subparsers.add_parser(name)
        parser.add_argument("--id", dest='id', type=str, required=True,
                            help='Participant ID')
        parser.add_argument("--start", dest='start', type=int, required=True,
                            help='time window start in UTC epoch milliseconds')
        parser.add_argument("--resolution", dest='resolution', type=int, required=True,
                             help='time window grouping resolution in milliseconds')
        parser.add_argument("--end", dest='end', type=int, required=True,
                            help='time window end in UTC epoch milliseconds')

        # Add feature-specific parameters and mark the parameter as required
        # if no default value is provided. Use the function docstring to get
        # the parameter's description.
        opt_idx = len(getfullargspec(func)[0]) - len(getfullargspec(func)[3] or ())
        for idx, param in enumerate(getfullargspec(func)[0]):
            desc = 'missing parameter description'
            parser.add_argument(f"--{param}", dest=param, required=idx < opt_idx,
                                help=desc + (' (required)' if idx < opt_idx else ''))

    # Dynamically execute the specific feature function with the parsed
    # arguments (removing all '_'-prefixed ones).
    kwargs = vars(superparser.parse_args())
    _format = os.getenv('CORTEX_OUTPUT_FORMAT', kwargs.pop('_format') or 'csv')
    if kwargs['_access_key'] is not None:
        os.environ['LAMP_ACCESS_KEY'] = kwargs.pop('_access_key')
    if kwargs['_secret_key'] is not None:
        os.environ['LAMP_SECRET_KEY'] = kwargs.pop('_secret_key')
    if kwargs['_server_address'] is not None:
        os.environ['LAMP_SERVER_ADDRESS'] = kwargs.pop('_server_address')
    _result = funcs[kwargs['_feature']](**{k: v for k, v in kwargs.items()
                                           if not k.startswith('_')})

    # Format and print the result to console (use bash redirection to output to a file).
    if _format == 'csv':

        # Use Pandas to auto-convert a list of dicts to a CSV string.
        # This may result in unexpected output
        # if the function returns something other than a dataframe-style object!
        print(pd.DataFrame.from_dict(_result).to_csv(index=False))
    elif _format == 'yaml':
        print(yaml.safe_dump(json.loads(json.dumps(_result)), indent=2,
                             sort_keys=False, default_flow_style=False))
    elif _format == 'json':
        print(json.dumps(_result, indent=2))
    else:
        pprint(_result)

"""
try:
    from flask import Flask
    app = Flask(__name__)
    @app.route('/<feature_name>', methods=['GET', 'POST'])
    def index(feature_name=None):
        if feature_name is None:
            # No feature was provided; return the list of functions and help info.
            return json.dumps({f['callable'].__name__: f['callable'] for f in all_features()}, indent=2)
        else:

            # A feature was selected; call it with query parameters as arguments.
            return json.dumps({}, indent=2)
    app.run()
except ImportError:
    raise Exception('Flask is not installed; cannot start web server!')
"""
