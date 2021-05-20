import os
import time
from functools import reduce

import pandas as pd
import altair as alt

import LAMP
import cortex.raw as raw
import cortex.primary as primary
import cortex.secondary as secondary
from cortex.feature_types import all_features

# Convenience to avoid extra imports/time-mangling nonsense...
def now():
    return int(time.time())*1000

# Convenience to avoid mental math...
MS_PER_DAY = 86400000 # (1000 ms * 60 sec * 60 min * 24 hr * 1 day)

def run(id_or_set, features, start=None, end=None, resolution=MS_PER_DAY):
    # Connect to the LAMP API server.
    if not 'LAMP_ACCESS_KEY' in os.environ or not 'LAMP_SECRET_KEY' in os.environ:
        raise Exception(f"You configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY` (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.")
    LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                 os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))
    
    #1. Check id to generate list of participants (put into "generate_id_list"?)
    participants = generate_ids(id_or_set)
    func_list = {f['callable'].__name__: f for f in all_features()}
    
    #TODO allow for raw, primary, and secondary to be used at once
#     fns = map(lambda feature_group: [getattr(mod, mod_name) 
#                                      for mod_name, mod in getmembers(feature_group, ismodule) 
#                                      if mod_name in features],
#               [raw, primary, secondary])
    
    _results = {}
    for f in features:
        
        # Make sure we aren't calling non-existant feature functions.
        if f not in func_list.keys():
            continue
        _results[f] = pd.DataFrame()
        
        # Iterate all participants in the list
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
            _res = func_list[f]['callable'](
                     id=participant,
                     start=start,
                     end=end,
                     #resolution=MS_PER_DAY
                   )
            _res2 = pd.DataFrame.from_dict(_res['data'])
            if _res2.shape[0] > 0:
                # If no data exists, don't bother appending the df.
                _res2.insert(0, 'id', participant) # prepend 'id' column
                _res2.timestamp = pd.to_datetime(_res2.timestamp, unit='ms') # convert to datetime
                _results[f] = pd.concat([_results[f], _res2])
            
    #TODO: convert and concat all dicts in each _results[str(f)] to pd.DataFrame
            
    return _results

# Helper function to generate a plot directly from a Cortex DF.
# FIXME: currently only allows plotting first one; should be alt.layer()'ed charts.
def plot(*args, **kwargs):
    df_dict = run(*args, **kwargs)
    return alt.Chart(list(df_dict.values())[0])
    
# Helper function to get list of all participant ids from "id" of type {LAMP.Researcher, LAMP.Study, LAMP.Participant}
def generate_ids(id_set):
    """
    This function takes either a single id of type Researcher, Study, or
    Participant,or a list of participant ids, and returns a list of all
    associated participant ids.

    Args:
        id_set(str/list) - A Researcher, Study, or Participant id, or a list of any combination of ids

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
            #log.info("Unpacked and returned a single participant id.")
            return [id_set]

        # If we do NOT find a Study parent, it cannot be a participant,
        # but the presence of a "Researcher" parent means it is a Study.
        elif "Researcher" in parents:
            # We return a list of Participant ids.
            final_list = [val['id'] for val in LAMP.Participant.all_by_study(id_set)['data']];
            #log.info("Unpacked ids for Study "+id_set +" and returned " + str(len(final_list)) + " ids.")
            return final_list

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
            #log.info("Unpacked " + str(len(study_ids))+" studies for Researcher " + id_set + " and returned " + 
            #         str(len(participant_ids)) + " ids total.")
            return participant_ids
        # If we reached this condition, the parent array is not empty, but it does not
        # contain Study OR Researcher parents. This is unlikely but we log the unknown
        # parents and return an empty list.
        else:
            #log.info("Unknown parents found: " + str(parents) + ". Returning empty array.")
            return []

    # If a list was passed in, we call this function
    # on each element, combine the resulting arrays with reduce,
    # and elminate repeat ids by converting our list to and from
    # a set.
    elif isinstance(id_set, list):
        combined_ids = list(set(reduce(lambda acc, _id: acc + generate_ids(_id), id_set, []))) 
        #log.info("After combining all id lists, returned " + str(len(combined_ids)) + " total ids.")
        return combined_ids
