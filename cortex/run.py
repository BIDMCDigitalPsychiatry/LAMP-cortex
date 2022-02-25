""" Module for getting features from cortex """
import os
import sys
import logging

import time
from functools import reduce
import inspect
import datetime

import pandas as pd

import LAMP
import cortex.raw as raw
import cortex.primary as primary
import cortex.secondary as secondary
from cortex.feature_types import all_features, log

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                    format="[%(levelname)s:%(module)s:%(funcName)s] %(message)s")
log = logging.getLogger('cortex')


# Convenience to avoid extra imports/time-mangling nonsense...
def now():
    return int(time.time())*1000

# Convenience to avoid mental math...
MS_PER_DAY = 86400000 # (1000 ms * 60 sec * 60 min * 24 hr * 1 day)




def run(id_or_set, features=[], feature_params={}, start=None, end=None,
        resolution=MS_PER_DAY, path_to_save="", run_part_and_feats="", cache=False):
    """ Function to get features from cortex.

        Args:
            id_or_set: a single string or list of strings containing
                    participant, researcher, or study ids.
            features: a list of raw, primary, and secondary features
            feature_params: a dictionary of optional parameters for each
                    feature, see example below
            start: the start time
            end: the end time
            resolution: the bin size in miliseconds, default is 1 day
            path_to_save: where to save the result, if no path it will
                not be saved, just returned
            run_part_and_features: to run on only certain participants
                and certain matching features, create a csv file with
                columns containing ids and features and column headings
                "participant" (participant id) and "feature"
        Returns:
            A dictionary with the features.

        Example:
            run(['U111111','abcdefg'],
                ['entropy','gps','hometime'],
                {'entropy': {method: 'k_means'}, 'hometime': {}})
            # the participant U111111 and all participants by studies of
            # researcher abcdefg
            # get entropy and hometime (secondary), and gps (primary)
            # for entropy, set method to 'k_means', don't set any parameters
            # for gps or hometime
            ** ids are fake. Please insert your desired ids.
        Notes:
            If the start and / or end time are not specified, the earliest and
            latest raw data timepoints will be used. These will then be shifted
            so all days start and end at 9am (if resolution is modulo days)
            If both features and run_part_and_features are specified then
            run_part_and_features will take precendence and features will be
            set to [].
    """
    # Connect to the LAMP API server.
    if not 'LAMP_ACCESS_KEY' in os.environ or not 'LAMP_SECRET_KEY' in os.environ:
        raise Exception(f"You configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY`"
                        + " (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.")
    LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                 os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))

    # Check id to generate list of participants
    participants = generate_ids(id_or_set)
    
    # if run_part_and_feats is called, generate participant list from here
    if run_part_and_feats != "":
        df = pd.read_csv(run_part_and_feats)
        participants = df.loc["participant"].tolist()
        features_by_participant = df.loc["feature"].tolist()
        features = []
    func_list = {f['callable'].__name__: f for f in all_features()}

    # TODO allow for raw, primary, and secondary to be used at once
    # fns = map(lambda feature_group: [getattr(mod, mod_name)
    #                                  for mod_name, mod in
    #                     getmembers(feature_group, ismodule)
    #                                  if mod_name in features],
    #                                  [raw, primary, secondary])

    _results = {}
    # Loop through all participants
    for i, participant in enumerate(participants):
        # loop through all features
        for f in features:
            # Make sure we aren't calling non-existant feature functions.
            if f not in func_list.keys():
                continue
            if f not in _results.keys():
                _results[f] = pd.DataFrame()

            if f in feature_params:
                params_f = feature_params[f]
            else:
                params_f = {}
            #try:
            _res = get_feature_for_participant(participant, f, params_f, start,
                                               end, resolution, cache)
            if _res is None:
                _results[f] = pd.DataFrame()
                continue
            # Make this into a df
            _res2 = pd.DataFrame.from_dict(_res['data'])
            if _res2.shape[0] > 0:
                # If no data exists, don't bother appending the df.
                _res2.insert(0, 'id', participant) # prepend 'id' column
                 # convert to datetime
                if hasattr(primary, f):
                    _res2.timestamp = pd.to_datetime(_res2.start, unit='ms')
                else:
                    _res2.timestamp = pd.to_datetime(_res2.timestamp, unit='ms')
                _results[f] = pd.concat([_results[f], _res2])
                if path_to_save != "":
                    log.info("Saving output locally..")

                    # create subdir if doesn't exist
                    if not os.path.exists(os.path.join(path_to_save, f)):
                        os.makedirs(os.path.join(path_to_save, f))

                    _results[f].to_pickle(os.path.join(path_to_save, f, participant + ".pkl"))

        if run_part_and_feats != "":
            f = features_by_participant[i]
            # Make sure we aren't calling non-existant feature functions.
            if f not in func_list.keys():
                continue
            if f not in _results.keys():
                _results[f] = pd.DataFrame()

            try:
                _res = get_feature_for_participant(participant, f, {}, start,
                                                   end, resolution, cache)

                # Make this into a df
                _res2 = pd.DataFrame.from_dict(_res['data'])
                if _res2.shape[0] > 0:
                    # If no data exists, don't bother appending the df.
                    _res2.insert(0, 'id', participant) # prepend 'id' column
                    # convert to datetime
                    if hasattr(primary, f):
                        _res2.timestamp = pd.to_datetime(_res2.start, unit='ms')
                    else:
                        _res2.timestamp = pd.to_datetime(_res2.timestamp, unit='ms')
                    _results[f] = pd.concat([_results[f], _res2])

                    # Save if there is a file path specified
                    if path_to_save != "":
                        if path_to_save[len(path_to_save) - 1] != "/":
                            path_to_save += "/"
                        _results[f].to_pickle(path_to_save + '_'.join([participant, f]) + ".pkl")
            except:
                log.info("Participant: " + participant + ", Feature: " + f + " crashed.")

    return _results


def get_feature_for_participant(participant, feature, feature_params, start, end,
                                resolution, cache):
    """ Helper function to compute the data for a feature for an individual
        participant.
    """
    func_list = {f['callable'].__name__: f for f in all_features()}
    # 5 Find start, end
    # FIXME: Seems to not work correctly in every case?
    if start is None:
        starts = [getattr(mod, mod_name)(id=participant,
                                            start=0,
                                            end=int(time.time())*1000,
                                            cache=False,
                                            recursive=False,
                                            attach=False,
                                            _limit=-1)['data'][0]['timestamp']
                     for mod_name, mod in inspect.getmembers(raw, inspect.ismodule)
                     if len(getattr(mod, mod_name)(id=participant,
                                                   start=0,
                                                   end=int(time.time())*1000,
                                                   cache=False,
                                                   recursive=False,
                                                   attach=False,
                                                   _limit=-1)['data']) > 0]
        if len(starts) == 0: # no data: return none
            log.info("Participant " + participant +
                     " has no data. Returning 'None' for all features.")
            return None
        start = min(starts)
        if resolution % MS_PER_DAY == 0:
            start = set_date_9am(start, 1)
    if end is None:
        end = max([getattr(mod, mod_name)(id=participant,
                                          start=0,
                                          end=int(time.time())*1000,
                                          cache=False,
                                          recursive=False,
                                          _limit=1)['data'][0]['timestamp']
                    for mod_name, mod in inspect.getmembers(raw, inspect.ismodule)
                    if len(getattr(mod, mod_name)(id=participant,
                                                  start=0,
                                                  end=int(time.time())*1000,
                                                  cache=False,
                                                  recursive=False,
                                                  _limit=1)['data']) > 0])
        if resolution % MS_PER_DAY == 0:
            end = set_date_9am(end, 0)
    if hasattr(secondary, feature):
        _res = func_list[feature]['callable'](
                 id=participant,
                 start=start,
                 end=end,
                 resolution=MS_PER_DAY,
                 cache=cache,
                 **feature_params)
    else:
        _res = func_list[feature]['callable'](
                id=participant,
                start=start,
                end=end,
                cache=cache,
                **feature_params)
    return _res

def set_date_9am(original_time, start = 1):
    """ Function to convert the start / end times to the
        previous / next 9am.

        Args:
            original_time: the time in ms
            start: whether it is a start or end time (1 for start, 0 for end)
        Returns:
            the new time in ms
    """
    if start:
        return _get_new_start_time(original_time)
    return _get_new_end_time(original_time)


def _get_new_start_time(earliest_time):
    """ Helper function to move the start time to the previous 9am.

        Args:
            earliest_time: the time in ms
        Returns:
            the new time in ms
    """
    time_9am = datetime.time(9,0,0)
    start_datetime = datetime.datetime.fromtimestamp(earliest_time / 1000)
    start_date = start_datetime.date()
    if start_datetime.time() < time_9am:
        start_date = start_date - datetime.timedelta(days=1)
    start_datetime = datetime.datetime.combine(start_date, time_9am)
    new_earliest_time = int(start_datetime.timestamp() * 1000)
    return new_earliest_time


def _get_new_end_time(latest_time):
    """ Helper function to move the end time to the next 9am.

        Args:
            latest_time: the time in ms
        Returns:
            the new time in ms
    """
    time_9am = datetime.time(9,0,0)
    end_datetime = datetime.datetime.fromtimestamp(latest_time / 1000)
    end_date = end_datetime.date()
    if end_datetime.time() > time_9am:
        end_date = end_date + datetime.timedelta(days=1)
    end_datetime = datetime.datetime.combine(end_date, time_9am)
    new_latest_time = int(end_datetime.timestamp() * 1000)
    return new_latest_time


def generate_ids(id_set):
    """
    Helper function to get list of all participant ids from "id" of type
    {LAMP.Researcher, LAMP.Study, LAMP.Participant}

    This function takes either a single id of type Researcher, Study, or
    Participant,or a list of participant ids, and returns a list of all
    associated participant ids.

    Args:
        id_set(str/list) - A Researcher, Study, or Participant id, or a list of
        any combination of ids

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
            # log.info("Unpacked and returned a single participant id.")
            return [id_set]

        # If we do NOT find a Study parent, it cannot be a participant,
        # but the presence of a "Researcher" parent means it is a Study.
        elif "Researcher" in parents:
            # We return a list of Participant ids.
            final_list = [val['id'] for val in
                          LAMP.Participant.all_by_study(id_set)['data']]
            # log.info("Unpacked ids for Study "+id_set +" and returned " +
            # str(len(final_list)) + " ids.")
            return final_list

        # Researchers have no parents.
        # Therefore, an empty parent dictionary means this id is associated
        # with a Researcher.
        elif not bool(parents):
            # First, we get all study ids associated with this researcher
            study_ids = [val['id'] for val in
                         LAMP.Study.all_by_researcher(id_set)["data"]]
            # Then, we loop through the list of study ids and concatenate all
            # associated participant ids into a single list, which we then
            # return.
            participant_ids = []
            for study_id in study_ids:
                participant_ids += [val['id'] for val in
                                    LAMP.Participant.all_by_study(study_id)
                                    ['data']]
            # log.info("Unpacked " + str(len(study_ids)) + " studies for
            # Researcher " + id_set + " and returned " +
            # str(len(participant_ids)) + " ids total.")
            return participant_ids
        # If we reached this condition, the parent array is not empty, but it does not
        # contain Study OR Researcher parents. This is unlikely but we log the
        # unknown parents and return an empty list.
        else:
            # log.info("Unknown parents found: " + str(parents) + ". Returning
            # empty array.")
            return []

    # If a list was passed in, we call this function
    # on each element, combine the resulting arrays with reduce,
    # and elminate repeat ids by converting our list to and from
    # a set.
    elif isinstance(id_set, list):
        combined_ids = list(set(reduce(lambda acc,
                                       _id: acc + generate_ids(_id),
                                       id_set, [])))
        # log.info("After combining all id lists, returned " +
        # str(len(combined_ids)) + " total ids.")
        return combined_ids
