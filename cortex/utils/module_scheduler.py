""" Module for scheduling activities """
import os
import LAMP
import pandas as pd
import datetime
import random
import time
import json
LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
        os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))
from useful_functions import shift_time


# Need to change these for your own study
MODULE_JSON_FILE = "example_modules.json"
MODULE_SPEC_FILE = "example_module_specs.json"

MS_IN_A_DAY = 86400000

f = open(MODULE_JSON_FILE)
MODULE_JSON = json.load(f)
f.close()

f = open(MODULE_SPEC_FILE)
MODULE_SPECS = json.load(f)
f.close()

def schedule_module(part_id, module_name, start_time, module_json):
    """ Schedule a module.

        Args:
            study_id: the study id
            module_name: the name of the module
            start_time: the start time for the module
    """
    if module_name not in module_json:
        print(module_name + " is not in the list of modules. " + part_id + " has not been scheduled.")
        return
    sucess = _schedule_module_helper(part_id,
                                     module_json[module_name]["activities"],
                                     module_json[module_name]["daily"],
                                     [start_time + x for x in module_json[module_name]["times"]],
                                     )
    if sucess == 0 and module_json[module_name]["message"] != "":
        dt = datetime.datetime.fromtimestamp(start_time / 1000)
        dt_iso = dt.isoformat() + 'Z'
        message_data = {"data": []}
        try:
            message_data = LAMP.Type.get_attachment(part_id, "lamp.messaging")
        except:
            pass
        message_data["data"].append({'from': 'researcher',
                                     'type': 'message',
                                     'date': dt_iso,
                                     'text': module_json[module_name]["message"]})
        LAMP.Type.set_attachment(part_id, "me", attachment_key = "lamp.messaging",body=message_data["data"])
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
        for k, act in enumerate(act_names):
            ind = list(all_act.index[all_act["name"] == act_names[k]])[0]
            curr_dict = act_dict[ind]
            dt = datetime.datetime.fromtimestamp(start_times[k] / 1000)
            dt_iso = dt.isoformat() + 'Z'
            curr_dict["schedule"].append({
                'start_date': dt_iso,
                'time': dt_iso,
                'custom_time': None,
                'repeat_interval': daily_schedule[k],
                'notification_ids': [random.randint(1,100000)]})
            try:
                LAMP.Activity.update(activity_id=curr_dict['id'], activity_activity=curr_dict)
            except:
                pass
        return 0
    else:
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
    for x in act_names:
        if x not in act_list:
            ret = -1
    return ret

def unschedule_other_surveys(part_id, keep_these=["Morning Daily Survey", "Weekly Survey"]):
    """ Delete schedules for all surveys except for keep_these.
    """
    act_dict = LAMP.Activity.all_by_participant(part_id)["data"]
    all_act = pd.DataFrame(act_dict)
    for i in range(len(act_dict)):
        if len(act_dict[i]["schedule"]) > 0:
            if act_dict[i]["name"] not in keep_these:
                act_dict[i]["schedule"] = []
                LAMP.Activity.update(activity_id=act_dict[i]['id'], activity_activity=act_dict[i])

def unschedule_specific_survey(part_id, survey_name):
    """ Delete schedule for a specific activity.
    """
    act_dict = LAMP.Activity.all_by_participant(part_id)["data"]
    all_act = pd.DataFrame(act_dict)
    for i in range(len(act_dict)):
        if len(act_dict[i]["schedule"]) > 0 and act_dict[i]["name"] == survey_name:
            act_dict[i]["schedule"] = []
            LAMP.Activity.update(activity_id=act_dict[i]['id'], activity_activity=act_dict[i])

def correct_modules(part_id, PHASE_TAG, MODULE_TAG, module_json=MODULE_JSON):
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
    ret = {"correct module": "",
           "current module": "",
           "wrong module": 0,
           "wrong repeat intervals": [],
           "wrong times": [],
        }

    try:
        phase = LAMP.Type.get_attachment(part_id, PHASE_TAG)["data"]
    except:
        print(f"Participant {part_id} has no phase attachment. Please correct this!")
        return
    if phase["status"] != 'enrolled' and phase["status"] != 'trial':
        return
    try:
        part_mods = LAMP.Type.get_attachment(part_id, MODULE_TAG)["data"]
    except:
        print(f"Participant {part_id} has no module attachment. Please correct this!")
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
            for x in module_json[mod["module"]]["activities"]:
                if act_df.loc[i, "name"] == x:
                    found = True
        if not found:
            unschedule_specific_survey(part_id, act_df.loc[i, "name"])

    need_to_schedule = False
    for mod in part_mods:
        # Check if the module is scheduled
        for x in module_json[mod["module"]]["activities"]:
            if len(act_df) == 0 or len(act_df[act_df["name"] == x]) != 1:
                need_to_schedule = True
        if need_to_schedule:
            # If something is missing, unschedule all activities in the module before proceeding
            for x in module_json[mod["module"]]["activities"]:
                 unschedule_specific_survey(part_id, x)
            schedule_module(part_id, mod["module"], shift_time(time.time() * 1000), module_json)
