""" Module for getting features from cortex """
import os
import sys
import logging

import time
import inspect
import datetime

import pandas as pd

import cortex.raw as raw
import cortex.primary as primary
import cortex.secondary as secondary
from cortex.feature_types import all_features, log

from cortex.utils.useful_functions import generate_ids, shift_time

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                    format="[%(levelname)s:%(module)s:%(funcName)s] %(message)s")
log = logging.getLogger('cortex')

def now():
    """ So we can do cortex.now() to get the time.
    """
    return int(time.time())*1000

MS_PER_DAY = 86400000 # (1000 ms * 60 sec * 60 min * 24 hr * 1 day)




def run(id_or_set, features=[], feature_params={}, start=None, end=None,
        resolution=MS_PER_DAY, path_to_save="", run_part_and_feats="",
        cache=False, print_logs=False):
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
            cache (boolean, default: False): whether or not to cache raw data
            print_logs (boolean, default: False): whether to set the logging to a higher level
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
    if not print_logs:
        log.setLevel(logging.WARNING)

    if not isinstance(features, list):
        raise Exception("You must pass in features as a list.")
    if start is None or end is None:
        log.warning("If start and / or end are set to None then the start / "
                    + "end time will be set to the earliest or latest raw data point.")
    # Check id to generate list of participants
    participants = generate_ids(id_or_set)

    # if run_part_and_feats is called, generate participant list from here
    if run_part_and_feats != "":
        df = pd.read_csv(run_part_and_feats)
        participants = df.loc["participant"].tolist()
        features_by_participant = df.loc["feature"].tolist()
        features_by_participant = [[x] for x in features_by_participant]
    else:
        features_by_participant = [features] * len(participants)
    func_list = {f['callable'].__name__: f for f in all_features()}

    _results = {}
    curr_val = 0
    for i, participant in enumerate(participants):
        for f in features_by_participant[i]:
            # Make sure we aren't calling non-existant feature functions.
            if f not in func_list.keys():
                continue
            if f not in _results.keys():
                _results[f] = pd.DataFrame()

            params_f = {}
            if f in feature_params:
                params_f = feature_params[f]

            _res = get_feature_for_participant(participant, f, params_f, start,
                                               end, resolution, cache)

            _res2 = pd.DataFrame.from_dict(_res['data'])
            if _res2.shape[0] > 0:
                # If no data exists, don't bother appending the df.
                _res2.insert(0, 'id', participant) # prepend 'id' column
                if hasattr(primary, f):
                    _res2.timestamp = pd.to_datetime(_res2.start, unit='ms')
                else:
                    _res2.timestamp = pd.to_datetime(_res2.timestamp, unit='ms')
                _results[f] = pd.concat([_results[f], _res2])

                # Save if there is a file path specified
                if path_to_save != "":
                    log.info("Saving output locally..")
                    _results[f].to_pickle(os.path.join(path_to_save,
                                            participant + "_" + f + ".pkl"))
            if not print_logs:
                sys.stdout.write('\r')
                j = (curr_val + 1) / (len(participants) * len(features))
                sys.stdout.write("[%-20s] %d%%" % ('='*int(20*j), 100*j))
                sys.stdout.flush()
                curr_val += 1

    return _results


def get_feature_for_participant(participant, feature, feature_params, start, end,
                                resolution, cache):
    """ Helper function to compute the data for a feature for an individual
        participant.

        Args:
            participant: the participant id
            feature: the name of the feature
            feature_params: any additional parameters for that feature
            start: the start in ms
            end: the end in ms
            resolution: the resolution in ms (for secondary features)
            cache: whether or not to cache the data
        Returns:
            The data from the feature for that participant from cortex
    """
    func_list = {f['callable'].__name__: f for f in all_features()}
    start = get_first_last_datapoint(participant, start, resolution, start = 1)
    end = get_first_last_datapoint(participant, end, resolution, start = 0)
    if start is None:
        log.info("Participant %s has no data. Returning 'None' for all features.", participant)
        return None
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

def get_first_last_datapoint(participant, original_time, resolution, start = 1):
    """ Get the first or last raw data timestamp for the participant.

        Args:
            participant: the participant id
            original_time: the start / end time
            resolution: the resolution
            start (boolean, default: 1): whether it is a start or end time
        Returns:
            original_time if it is not None
            None if there is no raw data
            The earliest / latest raw data timestamps if original_time is None
                and there is data. This will be shifted to 9am EST if
                resolution % MS_PER_DAY == 0
    """
    if original_time is not None:
        return original_time
    limit_value = 1
    if start:
        limit_value = -1
    times = [getattr(mod, mod_name)(id=participant,
                                        start=0,
                                        end=int(time.time())*1000,
                                        cache=False,
                                        recursive=False,
                                        attach=False,
                                        _limit=limit_value)['data'][0]['timestamp']
                 for mod_name, mod in inspect.getmembers(raw, inspect.ismodule)
                 if len(getattr(mod, mod_name)(id=participant,
                                               start=0,
                                               end=int(time.time())*1000,
                                               cache=False,
                                               recursive=False,
                                               attach=False,
                                               _limit=limit_value)['data']) > 0]
    if len(times) == 0: # no data: return none
        return None
    if start:
        original_time = min(times)
    else:
        original_time = min(times)
    if resolution % MS_PER_DAY == 0:
        original_time = set_date_9am(original_time, start)
    return original_time

def set_date_9am(original_time, start = 1):
    """ Function to convert the start / end times to the
        previous / next 9am.

        Args:
            original_time: the time in ms
            start: whether it is a start or end time (1 for start, 0 for end)
        Returns:
            the new time in ms shifted to 9am
    """
    time_9am = datetime.time(9,0,0)
    if start:
        start_datetime = datetime.datetime.fromtimestamp(original_time / 1000)
        if start_datetime.time() < time_9am:
            original_time = original_time - MS_PER_DAY
        return shift_time(original_time, shift=9)
    end_datetime = datetime.datetime.fromtimestamp(original_time / 1000)
    if end_datetime.time() > time_9am:
        original_time = original_time + MS_PER_DAY
    return shift_time(original_time, shift=9)
