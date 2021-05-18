import cortex.raw as raw
import cortex.primary as primary
import cortex.secondary as secondary

from functools import reduce
import LAMP
import time
from inspect import getmembers, ismodule
import pandas as pd
import altair as alt
import os

# Convenience to avoid extra imports/time-mangling nonsense...
def now():
    return int(time.time())*1000

MS_IN_A_DAY = 86400000
def run(id, features, start=None, end=None, resolution=MS_IN_A_DAY):
    # Connect to the LAMP API server.
    if not 'LAMP_ACCESS_KEY' in os.environ or not 'LAMP_SECRET_KEY' in os.environ:
        raise Exception(f"You configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY` (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.")
    LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                 os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))
    
    #1. Check id to generate list of participants (put into "generate_id_list"?)
    participants = generate_ids(id)
    feature_group = "survey_results"
    fns = [getattr(mod, mod_name) for mod_name, mod in getmembers(raw, ismodule) if mod_name in features]
    
    #TODO allow for raw, primary, and secondary to be used at once
#     fns = map(lambda feature_group: [getattr(mod, mod_name) 
#                                      for mod_name, mod in getmembers(feature_group, ismodule) 
#                                      if mod_name in features],
#               [raw, primary, secondary])
    
    _results = {}
    for f in fns:
        _results[str(f.__name__)] = pd.DataFrame()
        for participant in participants:
            
            #Find start, end 
            # FIXME: Seems to not work correctly in every case?
            if start is None:
                start = min([getattr(mod, mod_name)(id=participant, start=0, end=int(time.time())*1000, cache=False, recursive=False, limit=-1)['data'][0]['timestamp']
                                  for mod_name, mod in getmembers(raw, ismodule)
                                  if len(getattr(mod, mod_name)(id=participant, start=0, end=int(time.time())*1000, cache=False, recursive=False, limit=-1)['data']) > 0])
            if end is None:
                end = max([getattr(mod, mod_name)(id=participant, start=0, end=int(time.time())*1000, cache=False, recursive=False, limit=1)['data'][0]['timestamp']
                            for mod_name, mod in getmembers(raw, ismodule)
                            if len(getattr(mod, mod_name)(id=participant, start=0, end=int(time.time())*1000, cache=False, recursive=False, limit=1)['data']) > 0])
            
            #TODO only for raw function; allow resolution/other params to be passed if secondary, etc
            _res =  f(id=participant,
                      start=start,
                      end=end)#,
                      #resolution=MS_IN_A_DAY)
            _res2 = pd.DataFrame.from_dict(_res['data'])
            _res2.insert(0, 'id', participant) # prepend 'id' column
            _res2.timestamp = pd.to_datetime(_res2.timestamp, unit='ms') # convert to datetime
            _results[str(f.__name__)] = pd.concat([_results[str(f.__name__)], _res2])
            
    #TODO: convert and concat all dicts in each _results[str(f)] to pd.DataFrame
            
    return _results

# Helper function to generate a plot directly from a Cortex DF.
def plot(*args, **kwargs):
    return alt.Chart(run(*args, **kwargs)['survey']) # FIXME! hard-coded for now!
    
#Helper function to get list of all participant ids from "id" of type {LAMP.Researcher, LAMP.Study, LAMP.Participant}
def generate_ids(id_set):
    
    """
    This function takes either a single id of type Researcher, Study, or
    Participant,or a list of participant ids, and returns a list of all
    associated participant ids.
    
    Args:
        id_set(str/list) - A Researcher, Study, or Participant id, or a list of Participant ids
    
    Returns:
        list - A list of all associated participant ids
    """
    if isinstance(id_set, str):
        # Use LAMP.Type.parent to determine if this id is associated with
        # a Researcher, Study, or Participant
        parents = LAMP.Type.parent(id_set)["data"]

        # If we find a "Study" parent, this must be a Participant
        if "Study" in parents:
            # We return a list of exactly the one Participant ID.
            return [id_set]

        # If we do NOT find a Study parent, it cannot be a participant,
        # but the presence of a "Researcher" parent means it is a Study.
        elif "Researcher" in parents:
            # We return a list of Participant ids.
            return [val['id'] for val in LAMP.Participant.all_by_study(id_set)['data']]

        # Researchers have no parents.
        # Therefore, an empty parent dictionary means this id is associated
        # with a Researcher.
        elif not bool(parents):
            # First, we get all study ids associated with this researcher
            study_ids = [val['id'] for val in LAMP.Study.all_by_researcher(id_set)["data"]]
            # Then, we loop through the list of study ids and concatenate all associated
            # participant ids into a single list, which we then return.
            participant_ids = []
            for study_id in study_ids:
                participant_ids += [val['id'] for val in LAMP.Participant.all_by_study(study_id)['data']]
            return participant_ids
        # If we reached this condition, the parent array is not empty, but it does not
        # contain Study OR Researcher parents. This is unlikely but we log the unknown
        # parents and return an empty list.
        else:
            #log.info("Unknown parent"+str(parents))
            return []

    # If a list was passed in, we assume it was a list of participant ids.
    # We then return it unchanged.
    elif isinstance(id_set, list):
        return id_set

#Check type of id
def id_check(id):
    pass



