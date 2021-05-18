import os
import sys
import json
import yaml
import LAMP
import logging
import argparse
import pandas as pd
from pprint import pprint
from inspect import getargspec
import compress_pickle as pickle
import tarfile
#from .raw import sensors_results, cognitive_games_results, surveys_results # FIXME REMOVE LATER

# Get a universal logger to share with all feature functions.
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format="[%(levelname)s:%(module)s:%(funcName)s] %(message)s")
log = logging.getLogger('cortex')

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
                if kwargs.get(param, None) is None:
                    raise Exception(f"parameter `{param}` is required but missing")

            # Connect to the LAMP API server.
            if not 'LAMP_ACCESS_KEY' in os.environ or not 'LAMP_SECRET_KEY' in os.environ:
                raise Exception(f"You configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY` (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.")
            LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                         os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))
            
            # Find a valid local cache directory
            cache = kwargs.get('cache')

            if cache is None or cache:
                if kwargs.get('cache_dir') is not None:
                    cache_dir = os.path.expanduser(kwargs['cache_dir'])
                    assert os.path.exists(cache_dir), f"Caching directory ({cache_dir}) specified as a keyword argument does not exist"
                elif os.getenv('CORTEX_CACHE_DIR') is not None:
                    cache_dir = os.path.expanduser(os.getenv('CORTEX_CACHE_DIR'))
                    assert os.path.exists(cache_dir), f"Caching directory ({cache_dir}) found in enviornmental variables does not exist"
                if cache_dir is None: 
                    cache_dir = os.path.expanduser('~/.cache/cortex')
                    if not os.path.exists(cache_dir):
                        log.info(f"Caching directory does not yet exist, creating...")
                        os.makedirs(cache_dir)
                    assert os.path.exists(cache_dir), "Default caching directory could not be used, specify an alternative locatiton as a keyword argument: 'cache', or as an enviornmental variable: 'CORTEX_CACHE_DIR'"
                log.info(f"Cortex caching directory set to: {cache_dir}")   

                log.info(f"Processing raw feature \"{name}\"...")

                # local data caching TODO: combine pickle window with API data
                found = False
                for file in [f for f in os.listdir(cache_dir) if f[-7:] == '.cortex']:  # .lamp
                    path = cache_dir + '/' + file
                    saved = dict(zip(['name', 'id', 'start', 'end'], file.split('.')[0].split('_')))
                    saved['start'] = int(saved['start'])
                    saved['end'] = int(saved['end'])
                    if name.split('.')[-1] == saved['name']:
                        if saved['start'] <= kwargs['start'] and saved['end'] >= kwargs['end']:
                            if file.split('.')[-1] == 'cortex': #if no compression extension, use standard pkl loading
                                _result = pickle.load(path, 
                                                      set_default_extension=False,
                                                      compression=None)
                            else: 
                                _result = pickle.load(path)
                            found = True
                            log.info('Using saved raw data...')
                            break
                            
                if not found:
                    log.info('No saved raw data found, getting new...')
                    _result = func(*args, **kwargs)
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
                    
                    log.info(f"Saving raw data as \"{pickle_path}\"...")
            else:
                _result = func(*args, **kwargs)

            _event = {'timestamp': kwargs['start'],
                      'duration': kwargs['end'] - kwargs['start'],
                      'data': [r for r in _result if r['timestamp'] >= kwargs['start'] and
                               r['timestamp'] <= kwargs['end']]}
            return _event

        # When we register/save the function, make sure we save the decorated and not the RAW function.
        _wrapper2.__name__ = func.__name__
        __features__.append({ 'name': name, 'type': 'raw', 'dependencies': dependencies, 'callable': _wrapper2 })
        return _wrapper2
    return _wrapper1

# Primary features.
def primary_feature(name, dependencies, attach):
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
                *getargspec(func)[0][:-len(getargspec(func)[3] or ()) or None]
            ]
            for param in params:
                if kwargs.get(param, None) is None:
                    raise Exception(f"parameter `{param}` is required but missing")
            
            # Connect to the LAMP API server.
            if not 'LAMP_ACCESS_KEY' in os.environ or not 'LAMP_SECRET_KEY' in os.environ:
                raise Exception(f"You must configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY` (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.")
            LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                        os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))
            
            log.info(f"Processing primary feature \"{name}\"...")

            # TODO: Require primary feature dependencies to be raw features! -> Update: Not require but add a param to allow direct 2ndary to be calculated or not

            #Get previously calculated primary feature results from attachments, if you do attach.
            if attach:
                try: 
                   attachments = LAMP.Type.get_attachment(kwargs['id'], name)['data']
                   # remove last in case interval still open 
                   attachments.remove(max(attachments, key=lambda x: x['end']))
                   _from = max(a['end'] for a in attachments)
                   log.info(f"Using saved \"{name}\"...")
                except LAMP.ApiException: 
                   attachments = []
                   _from = 0 
                   log.info(f"No saved \"{name}\" found...")
                except Exception:
                    attachments = []
                    _from = 0 
                    log.info(f"Saved \"{name}\" could not be parsed, discarding...")

                start=kwargs.pop('start')
                if _from > kwargs['end']:
                    _result=[]
                else:
                    _result = func(*args, **{**kwargs, 'start':_from})

                # Combine old attachments with new result
                _body_new=sorted((_result+attachments),key=lambda x: x['start'])
                _event = { 'timestamp': start, 'duration': kwargs['end'] - start, 'data': 
                [b for b in _body_new if b['start']>=start] } 

                # Upload new features as attachment.
                log.info(f"Saving primary feature \"{name}\"...") 
                LAMP.Type.set_attachment(kwargs['id'], 'me', attachment_key=name, body=_body_new)
            else:
                _result = func(*args, **kwargs)
                _event = {'timestamp':kwargs['start'], 'duration': kwargs['end'] - kwargs['start'], 'data':_result}

            return _event

        # When we register/save the function, make sure we save the decorated and not the RAW function.
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
                *getargspec(func)[0][:-len(getargspec(func)[3] or ()) or None]
            ]
            for param in params:
                if kwargs.get(param, None) is None:
                    raise Exception(f"parameter `{param}` is required but missing")

            # Connect to the LAMP API server.
            if not 'LAMP_ACCESS_KEY' in os.environ or not 'LAMP_SECRET_KEY' in os.environ:
                raise Exception(f"You must configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY` (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.")
            LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                        os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))
            
            log.info(f"Processing secondary feature \"{name}\"...")

            timestamp_list = list(range(kwargs['start'], kwargs['end'], kwargs['resolution']))
            data = []
            for window in reversed([*zip(timestamp_list[:-1], timestamp_list[1:])]):
                window_start, window_end = window[0], window[1]
                _result = func(**{**kwargs, 'start':window_start, 'end':window_end})
                data.append(_result)
                
            # TODO: Require primary feature dependencies to be primary features (or raw features?)!
            data=sorted(data,key=lambda x: x['timestamp'])
            _event = {'timestamp': kwargs['start'], 'duration': kwargs['end'] - kwargs['start'], 'resolution':kwargs['resolution'], 'data': data}
            return _event

            return _event
        # When we register/save the function, make sure we save the decorated and not the RAW function.
        _wrapper2.__name__ = func.__name__
        __features__.append({ 'name': name, 'type': 'secondary', 'dependencies': dependencies, 'callable': _wrapper2 })
        return _wrapper2
    return _wrapper1

def delete_attach(id, features=None):
    """
    Deletes all saved primary features for a participant (requires LAMP-core 2021.4.7 or later)
    :param participant (str): LAMP id to reset for
    :param features (list): features to reset, defaults to all features (optional)
    """
    attachments= LAMP.Type.list_attachments(participant)['data']
    if features is None: features=attachments
    for feature in attachments:
        if feature.startswith('cortex'):
            if feature in features:
                LAMP.Type.set_attachment(participant, 'me', attachment_key=feature, body=None)
                log.info(f"Reset \"{feature}\"...")
                
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
    tar = tarfile.open('cache_' + str(int(time.time())*1000) + '.lamp', 'w:gz') #check if override?
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
            cache = tarfile.open(import_dir, 'r:gz') #check if override?
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
                    
        raise Exception("No cache found in cache_dir. Please provide a cache to import via 'import_dir' or provide a 'cache_dir' which contains a importable cache.")
                    

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
        opt_idx = len(getargspec(func)[0]) - len(getargspec(func)[3] or ())
        for idx, param in enumerate(getargspec(func)[0]):
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
