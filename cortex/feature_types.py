import os
import sys
import json
import yaml
import LAMP
import logging
import argparse
import pandas as pd
from pprint import pprint
from inspect import getargspec, getfullargspec
import compress_pickle as pickle
import tarfile
import re
import copy
import numpy as np
#from .raw import sensors_results, cognitive_games_results, surveys_results # FIXME REMOVE LATER

# Get a universal logger to share with all feature functions.
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                    format="[%(levelname)s:%(module)s:%(funcName)s] %(message)s")
log = logging.getLogger('cortex')

# List all registered features (raw, primary, secondary).
__features__ = []
def all_features():
    return __features__

# Raw features.
def raw_feature(name, dependencies):
    """
    Determines whether caching should be performed upon raw data request. Also adds data quality metrics to the results after the request is successfully completed
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
                raise Exception(f"You configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY`" +
                                " (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.")
            LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                         os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))

            # Find a valid local cache directory
            cache = kwargs.get('cache')
                
            def _raw_caching(func, *args, **kwargs):
                """
                Finds cached data for raw features
                
                """
                
                if os.getenv('CORTEX_CACHE_DIR') is None:
                    raise Exception("'CORTEX_CACHE_DIR' is not defined in your environment variables. Please set it to a valid path, or disable caching.")
                cache_dir = os.path.expanduser(os.getenv('CORTEX_CACHE_DIR'))
                assert os.path.exists(cache_dir), f"Caching directory ({cache_dir}) found in enviornmental variables does not exist. Please set 'CORTEX_CACHE_DIR' to a valid path, or disbale caching."                    

                log.info("Cortex caching directory set to: " + cache_dir)
                log.info("Processing raw feature " + name + "...")
                
                # local data caching TODO: combine pickle window with API data
                for file in [f for f in os.listdir(cache_dir) if f[-7:] == '.cortex']:  # .lamp
                    path = cache_dir + '/' + file

                    if not re.match('^' + name.split('.')[1], file):
                        continue

                    _, rest = re.split('^'+name.split('.')[1]+'_', file)
                    saved = dict(zip(['id', 'start', 'end'], re.split('.cortex$', rest)[0].split('_')))
                    saved['name'] = name.split('.')[1]
                    try:
                        saved['start'] = int(saved['start'])
                        saved['end'] = int(saved['end'])
                    except:
                        continue

                    if saved['start'] <= kwargs['start'] and saved['end'] >= kwargs['end'] and saved['id'] == kwargs['id']:
                        #if no compression extension, use standard pkl loading
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
                _result = func(**kwargs)
                pickle_path = (cache_dir + '/' +
                               name.split('.')[-1] + '_' +
                               kwargs['id'] + '_' +
                               str(kwargs['start']) + '_' +
                               str(kwargs['end']) + '.cortex')

                if os.getenv('CORTEX_CACHE_COMPRESSION') is not None:
                    assert os.getenv('CORTEX_CACHE_COMPRESSION') in ['gz', 'bz2', 'lzma', 'zip'], f"Compression method for caching does not exist."
                    pickle_path += '.' + os.getenv('CORTEX_CACHE_COMPRESSION')

                pickle.dump(_result,
                            pickle_path,
                            compression=kwargs.get('compression'),
                            set_default_extension=False)

                log.info("Saving raw data as " + pickle_path + "...")
                return _result

            #Get cached data if specified; otherwise get data via API request
            if cache:
                _result = _raw_caching(func=func, *args, **kwargs)
            else:
                _result = func(*args, **kwargs)

            _event = {'timestamp': kwargs['start'],
                      'duration': kwargs['end'] - kwargs['start'],
                      'data': [r for r in _result if r['timestamp'] >= kwargs['start'] and
                               r['timestamp'] <= kwargs['end']]}

            # Add data quality metrics
            def _raw_data_quality(event, *args, **kwargs):
                """
                Add data quality metrics to raw data event
                """
                TEN_MINUTES = 1000 * 60 * 10
                RES = TEN_MINUTES # set the resolution for quality
                HZ_THRESH = 0.5 # set threshold in hz
                idx = 0
                if len(event['data']) > 0:
                    start_time, end_time = kwargs['start'], kwargs["end"]
                    res_counts = np.zeros((len(range(end_time, start_time, -1 * RES))))
                    if res_counts.shape[0] > 0:
                        for i, x in enumerate(range(end_time, start_time, -1 * RES)):
                            while (idx + 1 < len(event['data']) and
                                   event['data'][idx]['timestamp'] > x - RES):
                                res_counts[i] += 1
                                idx += 1
                        fs = res_counts / (RES / 1000)
                        event["fs_mean"] = fs.mean()
                        event["fs_var"] = fs.var()
                        event["percent_good_data"] = np.sum(fs > HZ_THRESH) / fs.shape[0]
                    else:
                        event["fs_mean"] = len(event['data']) / (RES / 1000)
                        event["fs_var"] = 0
                        event["percent_good_data"] = event["fs_mean"] > HZ_THRESH
                else:
                    event["fs_mean"] = 0
                    event["fs_var"] = 0
                    event["percent_good_data"] = 0
                    
                return event
                    
            _event = _raw_data_quality(_event, *args, **kwargs)

            return _event

        # When we register/save the function, make sure we
        # save the decorated and not the RAW function.
        _wrapper2.__name__ = func.__name__
        __features__.append({'name': name, 'type': 'raw', 'dependencies': dependencies, 'callable': _wrapper2})
        return _wrapper2
    return _wrapper1

# Primary features.
def primary_feature(name, dependencies):
    """
    Some explanation of how to use this decorator goes here.
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
            
            def _primary_filter(_res, has_raw_data, *args, **kwargs):
                """
                Filter out primary feature results that do not belong in interval [kwargs['start'], kwargs['end']]
                
                Arguments:
                    
                Returns:
                """
                _body_new_copy = copy.deepcopy(_res)
                _event = { 'timestamp': kwargs['start'], 'duration': kwargs['end'] - kwargs['start'], 'data':
                            [b for b in _body_new_copy if
                                    ((b['start'] >= kwargs['start'] and b['end'] <= kwargs['end'])
                                  or (b['start'] < kwargs['start'] and kwargs['start'] < b['end'] <= kwargs['end'])
                                  or (kwargs['start'] < b['start'] < kwargs['end'] and b['end'] > kwargs['end']))],
                          'has_raw_data': has_raw_data }

                # make sure start and end match kwargs
                if len(_event['data']) > 0:
                    if _event['data'][0]['start'] < kwargs['start']:
                        _event['data'][0]['start'] = kwargs['start']
                        _event['data'][0]['duration'] = _event['data'][0]['end'] - _event['data'][0]['start']
                    if _event['data'][len(_event['data']) - 1]['end'] > kwargs['end']:
                        _event['data'][len(_event['data']) - 1]['end'] = kwargs['end']
                        _event['data'][len(_event['data']) - 1]['duration'] = (_event['data'][len(_event['data']) - 1]['end']
                                                                - _event['data'][len(_event['data']) - 1]['start'])
                        
                return _event
                
                
            def _primary_attach(func, *args, **kwargs):
                """
                Utilize and update LAMP attachments to speed processing of primary feature
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

                start=kwargs.pop('start')
                if _from > kwargs['end']:
                    _result=[]
                else:
                    _result = func(*args, **{**kwargs, 'start':_from})
                    if 'has_raw_data' in _result:
                        has_raw_data = _result['has_raw_data']
                    _result = _result['data']

                # Combine old attachments with new results
                unique_dict = _result + attachments
                unique_dict = [k for j, k in enumerate(unique_dict) if k not in unique_dict[j + 1:]]
                _body_new=sorted((unique_dict),key=lambda x: x['start'])
                # need to use a copy so you don't overwrite the original
                _event = _primary_filter(_body_new, *args, **kwargs)

                # Upload new features as attachment.
                log.info(f"Saving primary feature \"{name}\"...")
                LAMP.Type.set_attachment(kwargs['id'], 'me', attachment_key=name, body=_body_new)

                return _event
            
            attach = kwargs.get('attach')
            if attach:
                _event = _primary_attach(func=func, *args, **kwargs)
                
            else:
                has_raw_data = -1
                _result_init = func(*args, **kwargs)
                _result = _primary_filter(_result_init['data'], _result_init['has_raw_data'], *args, **kwargs)
                
                if 'has_raw_data' in _result:
                    has_raw_data = _result['has_raw_data']
                _event = {'timestamp': kwargs['start'], 'duration': kwargs['end'] - kwargs['start'], 'data': _result['data'], 'has_raw_data': has_raw_data}

            return _event

        # When we register/save the function, make sure we save the
        # decorated and not the RAW function.
        _wrapper2.__name__ = func.__name__
        __features__.append({ 'name': name, 'type': 'primary', 'dependencies': dependencies, 'callable': _wrapper2 })
        return _wrapper2
    return _wrapper1

# Secondary features.
def secondary_feature(name, dependencies):
    """
    Some explanation of how to use this decorator goes here.
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
                raise Exception(f"You must configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY` (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.")
            LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                        os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))

            log.info("Processing secondary feature " + name + "...")

            timestamp_list = list(range(kwargs['start'], kwargs['end'], kwargs['resolution']))
            data = []
            for window in reversed([*zip(timestamp_list[:-1], timestamp_list[1:])]):
                window_start, window_end = window[0], window[1]
                _result = func(**{**kwargs, 'start':window_start, 'end':window_end})
                data.append(_result)

            # TODO: Require primary feature dependencies to be primary features (or raw features?)!
            data = sorted(data,key=lambda x: x['timestamp']) if data else []
            _event = {'timestamp': kwargs['start'], 'duration': kwargs['end'] - kwargs['start'], 'resolution':kwargs['resolution'], 'data': data}

            return _event
        # When we register/save the function, make sure we save the decorated and not the RAW function.
        _wrapper2.__name__ = func.__name__
        __features__.append({ 'name': name, 'type': 'secondary', 'dependencies': dependencies, 'callable': _wrapper2 })
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
        assert os.path.exists(import_dir), "Import cache could not be found. Please provide a existing path to import_dir."
        try:
            cache = tarfile.open(import_dir, 'r:gz') # check if override?
        except tarfile.ReadError:
            raise "Cache file was found but could not be read. Please check that it is of proper type *.tz"

    else:
        cache_dir = cache_finder(cache_dir)
        #find any cache in the folder
        for f in os.listdir(cache_dir):
            if f.endswith('cortex'):
                try:
                    cache = tarfile.open(os.path.join(cache_dir, f), 'r:gz')
                    return cache
                except:
                    log.info("Found a file with extension '.cortex' in cache_dir, but unable to read.")

        raise Exception("No cache found in cache_dir. Please provide a cache to" +
                        " import via 'import_dir' or provide a 'cache_dir' which contains a importable cache.")


def cache_finder(cache_dir):
    """
    Helper function that finds the cache location
    """
    if cache_dir is not None:
        cache_dir = os.path.expanduser(cache_dir)
        assert os.path.exists(cache_dir), f"Caching directory ({cache_dir}) specified as a keyword argument does not exist"
    elif os.getenv('CORTEX_CACHE_DIR') is not None:
        cache_dir = os.path.expanduser(os.getenv('CORTEX_CACHE_DIR'))
        assert os.path.exists(cache_dir), f"Caching directory ({cache_dir}) found in enviornmental variables does not exist"
    elif cache_dir is None: 
        cache_dir = os.path.expanduser('~/.cache/cortex')
        if not os.path.exists(cache_dir):
            log.info(f"Caching directory does not yet exist.")
            log.info(f"Creating default cache dir at ~/.cache/cortex")
            os.makedirs(cache_dir)
        assert os.path.exists(cache_dir), "Error in default caching directory at ~/.cache/cortex. Please specify an alternative locatiton as a keyword argument: 'cache_dir', or as an enviornmental variable: 'CORTEX_CACHE_DIR'"
    return cache_dir

# Allows execution of feature functions from the command line, with argument parsing.
def _main():
    superparser = argparse.ArgumentParser(prog="cortex",
                                          description='Cortex data analysis pipeline for the LAMP Platform')
    superparser.add_argument('--version', action='version', version='Cortex 2021.3.1')
    superparser.add_argument('--format', dest='_format', choices=['json', 'csv', 'yaml'],
                             help='the output format type (can also be set using the environment variable CORTEX_OUTPUT_FORMAT)')
    superparser.add_argument('--access-key', dest='_access_key',
                             help='the access key for the LAMP API Server (can also be set using the environment variable LAMP_ACCESS_KEY)')
    superparser.add_argument('--secret-key', dest='_secret_key',
                             help='the secret key for the LAMP API Server (can also be set using the environment variable LAMP_SECRET_KEY)')
    superparser.add_argument('--server-address', dest='_server_address',
                             help='the server address for the LAMP API Server (can also be set using the environment variable LAMP_SERVER_ADDRESS)')
    subparsers = superparser.add_subparsers(title="features", dest='_feature', required=True,
                                            description="Available features for processing")
    funcs = {f['callable'].__name__: f['callable'] for f in all_features()}
    for name, func in funcs.items():

        # Add a sub-parser for this feature with the required (id, start, end).
        parser = subparsers.add_parser(name)
        parser.add_argument(f"--id", dest='id', type=str, required=True,
                            help='Participant ID')
        parser.add_argument(f"--start", dest='start', type=int, required=True,
                            help='time window start in UTC epoch milliseconds')
        parser.add_argument(f"--resolution", dest='resolution', type=int, required=True,
                             help='time window grouping resolution in milliseconds')
        parser.add_argument(f"--end", dest='end', type=int, required=True,
                            help='time window end in UTC epoch milliseconds')

        # Add feature-specific parameters and mark the parameter as required 
        # if no default value is provided. Use the function docstring to get 
        # the parameter's description.
        opt_idx = len(getfullargspec(func)[0]) - len(getfullargspec(func)[3] or ())
        for idx, param in enumerate(getfullargspec(func)[0]):
            desc = 'missing parameter description'
            parser.add_argument(f"--{param}", dest=param, required=idx < opt_idx,
                                help=desc + (' (required)' if idx < opt_idx else ''))

    # Dynamically execute the specific feature function with the parsed arguments (removing all '_'-prefixed ones).
    kwargs = vars(superparser.parse_args())
    _format = os.getenv('CORTEX_OUTPUT_FORMAT', kwargs.pop('_format') or 'csv')
    if kwargs['_access_key'] is not None:
        os.environ['LAMP_ACCESS_KEY'] = kwargs.pop('_access_key')
    if kwargs['_secret_key'] is not None:
        os.environ['LAMP_SECRET_KEY'] = kwargs.pop('_secret_key')
    if kwargs['_server_address'] is not None:
        os.environ['LAMP_SERVER_ADDRESS'] = kwargs.pop('_server_address')
    _result = funcs[kwargs['_feature']](**{k: v for k, v in kwargs.items() if not k.startswith('_')})
    
    # Format and print the result to console (use bash redirection to output to a file).
    if _format == 'csv':

        # Use Pandas to auto-convert a list of dicts to a CSV string. This may result in unexpected output
        # if the function returns something other than a dataframe-style object!
        print(pd.DataFrame.from_dict(_result).to_csv(index=False))
    elif _format == 'yaml':
        print(yaml.safe_dump(json.loads(json.dumps(_result)), indent=2, sort_keys=False, default_flow_style=False))
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
