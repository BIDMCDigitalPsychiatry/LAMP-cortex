import os
import LAMP
from functools import reduce
import pandas as pd
LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'), os.getenv('LAMP_SERVER_ADDRESS'))
import datetime


def generate_ids(id_set):
    """ This function takes either a single id of type Researcher, Study, or
        Participant,or a list of participant ids, and returns a list of all
        associated participant ids.

        Args:
            id_set(str/list) - A Researcher, Study, or Participant id,
                or a list of any combination of ids

        Returns:
            list - A list of all associated participant ids
    """
    if isinstance(id_set, str):
        parents = LAMP.Type.parent(id_set)["data"]

        if "Study" in parents:
            return [id_set]
        elif "Researcher" in parents:
            final_list = [val['id'] for val in LAMP.Participant.all_by_study(id_set)['data']];
            return final_list
        elif not bool(parents):
            study_ids = [val['id'] for val in LAMP.Study.all_by_researcher(id_set)["data"]]
            participant_ids = []
            for study_id in study_ids:
                participant_ids += [val['id'] for val in LAMP.Participant.all_by_study(study_id)['data']]
            return participant_ids
        else:
            return []
    elif isinstance(id_set, list):
        combined_ids = list(set(reduce(lambda acc, _id: acc + generate_ids(_id), id_set, [])))
        return combined_ids

def shift_time(curr_time, shift=18):
    """ Function to convert the start / end times to the same
        day at a certain time.

        Args:
            curr_time: the time in ms (for the date)
            shift: the time to shift start time to
        Returns:
            the new timestamp (current date and shifted time)
    """
    time_shift = datetime.time(shift,0,0)
    end_date = datetime.datetime.fromtimestamp(curr_time / 1000).date()
    end_datetime = datetime.datetime.combine(end_date, time_shift)
    return int(end_datetime.timestamp() * 1000)

def delete_sensors(part_id):
    """ Function to remove all sensors.
        This will stop passive data collection.

        Args:
            part_id: the participant id
    """
    sensors = LAMP.Sensor.all_by_participant(part_id)["data"]
    for s in sensors:
        LAMP.Sensor.delete(s["id"])

def add_sensor(study_id, spec, name):
    """ Function to add a sensor.

        Args:
            study_id: the study id
            spec: a sensor spec (such as 'lamp.gps' or 'lamp.device_state')
            name: what to call the sensor
    """
    LAMP.Sensor.create(study_id, {'spec': spec, 'name': name, 'settings':{}})

def propagate_activity(base_user, activity_name, parts, excluded_tags=[]):
    """ Copy the activity from one user into all other.
        Only copy the content of the activity, do not create new activities.

        Args:
            base_user: the user to copy the activity from
            activity_name: the name of the activity to copy
            parts: list of participants to propogate the change to
            excluded_tags: list of tags not to copy to all participants
    """
    # get the activity from base user
    activity = [x for x in LAMP.Activity.all_by_participant(base_user)["data"]
                 if x["name"] == activity_name][0]
    copy_act = {}
    for x in activity:
        if x != "id":
            copy_act[x] = activity[x]

    # Copy activity into all users
    for p in parts:
        all_acts = LAMP.Activity.all_by_participant(participant_id=p)['data']
        for x in all_acts:
            if x["name"] == activity_name:
                LAMP.Activity.update(activity_id=x['id'], activity_activity=copy_act)
                for attach_name in LAMP.Type.list_attachments(activity["id"])["data"]:
                    if attach_name not in excluded_tags:
                        LAMP.Type.set_attachment(x["id"], "me", attach_name,
                            body=LAMP.Type.get_attachment(activity["id"], attach_name)["data"])

def get_part_id_from_name(name, parts):
    """ Find the id which has the lamp.name == name
    """
    # Get the tecc participants
    for p in parts:
        if LAMP.Type.get_attachment(p, "lamp.name")["data"] == name:
            return p
    return -1

def get_activity_names(part_id):
    """ Get activity names and specs for a participant.

        Args:
            part_id: the participant_id
        Returns:
            The DataFrame of ActivityEvents with two additional columns:
            "name" and "spec" from the Activity data
        Note: this will not account for deleted activities.
    """
    df_names = []
    df_type = []
    df = LAMP.ActivityEvent.all_by_participant(part_id)["data"]
    df = pd.DataFrame(df)
    act_names = pd.DataFrame(LAMP.Activity.all_by_participant(part_id)["data"])
    df_names = []
    for j in range(len(df)):
        if len(list(act_names[act_names["id"] == df.loc[j, "activity"]]["name"])) > 0:
            df_names.append(list(act_names[act_names["id"] == df.loc[j, "activity"]]["name"])[0])
            df_type.append(list(act_names[act_names["id"] == df.loc[j, "activity"]]["spec"])[0].split(".")[1])
        else:
            df_names.append(None)
            df_type.append(None)
    df["name"] = df_names
    df["spec"] = df_type
    return df