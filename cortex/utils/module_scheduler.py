""" Module for scheduling activities """
import os
import datetime
import random
import time
import json
import pandas as pd
import LAMP
from ..utils.useful_functions import shift_time

path_prefix = os.path.split(os.path.realpath(__file__))[0]
MODULE_JSON_FILE = path_prefix+"/example_modules.json"
MODULE_SPEC_FILE = path_prefix+"/example_module_specs.json"

MS_IN_A_DAY = 86400000

with open(MODULE_JSON_FILE, "r") as file_handle:
    MODULE_JSON = json.load(file_handle)

with open(MODULE_SPEC_FILE, "r") as file_handle:
    MODULE_SPECS = json.load(file_handle)

def schedule_module(part_id, module_name, start_time, module_json):
    """ Schedule a module.

        Args:
            study_id: the study id
            module_name: the name of the module
            start_time: the start time for the module
    """
    if module_name not in module_json:
        print(module_name + " is not in the list of modules. "
              + part_id + " has not been scheduled.")
        return
    sucess = _schedule_module_helper(part_id,
                                     module_json[module_name]["activities"],
                                     module_json[module_name]["daily"],
                                     [start_time + x for x in module_json[module_name]["times"]],
                                     )
    if sucess == 0 and module_json[module_name]["message"] != "":
        dt_val = datetime.datetime.fromtimestamp(start_time / 1000)
        dt_iso = dt_val.isoformat() + 'Z'
        message_data = {"data": []}
        try:
            message_data = LAMP.Type.get_attachment(part_id, "lamp.messaging")
        except LAMP.ApiException:
            pass
        message_data["data"].append({'from': 'researcher',
                                     'type': 'message',
                                     'date': dt_iso,
                                     'text': module_json[module_name]["message"]})
        LAMP.Type.set_attachment(part_id,
                                 "me",
                                 attachment_key = "lamp.messaging",
                                 body=message_data["data"])
    elif sucess != 0:
        print("At least one module was missing for " + part_id)


def _schedule_module_helper(part_id, act_names, daily_schedule, start_times):
    """ Function to schedule all modules

        Args:
            part_id: the participant id
            act_names: the names of the activities to schedule
            daily_schedule: "daily" or "none"
            start_times: the time in ms to start the activity
        Returns:
            0 for sucess, 1 for some activities are missing
    """
    act_dict = LAMP.Activity.all_by_participant(part_id)["data"]
    all_act = pd.DataFrame(act_dict)
    if _check_modules(act_dict, act_names) == 0:
        for k, _ in enumerate(act_names):
            ind = list(all_act.index[all_act["name"] == act_names[k]])[0]
            curr_dict = act_dict[ind]
            dt_val = datetime.datetime.fromtimestamp(start_times[k] / 1000)
            dt_iso = dt_val.isoformat() + 'Z'
            curr_dict["schedule"].append({
                'start_date': dt_iso,
                'time': dt_iso,
                'custom_time': None,
                'repeat_interval': daily_schedule[k],
                'notification_ids': [random.randint(1,100000)]})
            try:
                LAMP.Activity.update(activity_id=curr_dict['id'], activity_activity=curr_dict)
            except LAMP.ApiException:
                pass
        return 0
    return -1

def _check_modules(act_dict, act_names):
    """ Check whether the modules are there or not.

        Args:
            act_dict: the dict of activities
            act_names: the names to check
        Returns:
            0 for sucess, -1 for failure
    """
    act_list = pd.DataFrame(act_dict)['name'].to_list()
    ret = 0
    for name in act_names:
        if name not in act_list:
            ret = -1
    return ret

def unschedule_other_surveys(part_id, keep_these):
    """ Delete schedules for all surveys except for keep_these.
    """
    act_dict = LAMP.Activity.all_by_participant(part_id)["data"]
    for act in act_dict:
        if len(act["schedule"]) > 0:
            if act["name"] not in keep_these:
                act["schedule"] = []
                LAMP.Activity.update(activity_id=act['id'], activity_activity=act)

def unschedule_specific_survey(part_id, survey_name):
    """ Delete schedule for a specific activity.
    """
    act_dict = LAMP.Activity.all_by_participant(part_id)["data"]
    for act in act_dict:
        if len(act["schedule"]) > 0 and act["name"] == survey_name:
            act["schedule"] = []
            LAMP.Activity.update(activity_id=act['id'], activity_activity=act)

def correct_modules(part_id, phase_tag, module_tag, module_json=MODULE_JSON):
    """ Check what module someone is scheduled for, verify that the schedule
        is correct.

        Participants will have a module list attached (modules) in the form:
            [{
                "module": "trial_period",
                "phase": "trial",
                "start_end": [0, 345600000],
                "shift": 18
             },
             {
                 "module": "daily_and_weekly",
                 "phase": "enrolled",
                 "start_end": [0, 2764800000],
                 "shift": 18
             }]

        Args:
            part_id: the participant id
            phase_tag: the tag for participant, should have status and phases fields
            module_tag: the tag for participant, should be in the form shown above
            module_json: json with module specs
        Note: The phase and module tags could be hard coded as environment variables
            or as global variables here as instead.
        Returns:
            A dictionary in the form:
            {
                 "correct module": correct module,
                 "current module": [current module/s],
                 "wrong module": 1 or 0,
                 "wrong repeat intervals": ["activity0", "activity1"],
                 "wrong times": [{"activity0": time_diff0}, {"activity1": time_diff1},],
            }
    """
    try:
        phase = LAMP.Type.get_attachment(part_id, phase_tag)["data"]
        part_mods = LAMP.Type.get_attachment(part_id, module_tag)["data"]
    except LAMP.ApiException:
        print(f"Participant {part_id} is missing a phase or module attachment."
              + " Please correct this!")
        return
    if phase["status"] != 'enrolled' and phase["status"] != 'trial':
        return

    phase_timestamp = phase['phases'][phase["status"]]
    curr_df = int(time.time() * 1000) - phase_timestamp

    # Find current module/s
    part_mods = [x for x in part_mods if x["phase"] == phase["status"]]
    part_mods = [x for x in part_mods if (x["start_end"][0] < curr_df) &
                                         (x["start_end"][1] >= curr_df)]

    # Figure out what module they are scheduled for
    acts = LAMP.Activity.all_by_participant(part_id)["data"]
    acts = [x for x in acts if x["schedule"] != []]
    act_df = pd.DataFrame(acts)

    # Unschedule unwanted activities
    for i in range(len(act_df)):
        found = False
        for mod in part_mods:
            # Check if the module is scheduled
            for mod_name in module_json[mod["module"]]["activities"]:
                if act_df.loc[i, "name"] == mod_name:
                    found = True
        if not found:
            unschedule_specific_survey(part_id, act_df.loc[i, "name"])

    need_to_schedule = False
    for mod in part_mods:
        # Check if the module is scheduled
        for mod_name in module_json[mod["module"]]["activities"]:
            if len(act_df) == 0 or len(act_df[act_df["name"] == mod_name]) != 1:
                need_to_schedule = True
        if need_to_schedule:
            # If something is missing, unschedule all activities in the module before proceeding
            for mod_name in module_json[mod["module"]]["activities"]:
                unschedule_specific_survey(part_id, mod_name)
            schedule_module(part_id, mod["module"], shift_time(time.time() * 1000), module_json)
