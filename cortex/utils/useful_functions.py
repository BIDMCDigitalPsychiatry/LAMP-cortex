""" Module for various useful functions for
    working with the LAMP API
"""
from functools import reduce
import datetime
import time
import re
import pandas as pd
import LAMP

MS_IN_DAY = 24 * 3600 * 1000
#Used for set_graphs
EXPERIMENTAL_NAME='lamp.selectedExperimental'

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
        if "Researcher" in parents:
            final_list = [val['id'] for val in LAMP.Participant.all_by_study(id_set)['data']]
            return final_list
        if not bool(parents):
            study_ids = [val['id'] for val in LAMP.Study.all_by_researcher(id_set)["data"]]
            participant_ids = []
            for study_id in study_ids:
                participant_ids += [val['id'] for val in
                                    LAMP.Participant.all_by_study(study_id)['data']]
            return participant_ids
        return []
    if isinstance(id_set, list):
        combined_ids = list(set(reduce(lambda acc, _id: acc + generate_ids(_id), id_set, [])))
        return combined_ids
    return []

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
    for sensor in sensors:
        LAMP.Sensor.delete(sensor["id"])

def add_sensor(study_id, spec, name):
    """ Function to add a sensor.

        Args:
            study_id: the study id
            spec: a sensor spec (such as 'lamp.gps' or 'lamp.device_state')
            name: what to call the sensor
    """
    LAMP.Sensor.create(study_id, {'spec': spec, 'name': name, 'settings':{}})

def propagate_activity(base_user, activity_name, parts, excluded_tags=None):
    """ Copy the activity from one user into all other.
        Only copy the content of the activity, do not create new activities.

        Args:
            base_user: the user to copy the activity from
            activity_name: the name of the activity to copy
            parts: list of participants to propogate the change to
            excluded_tags: list of tags not to copy to all participants
    """
    if excluded_tags is None:
        excluded_tags = []
    # get the activity from base user
    activity = [x for x in LAMP.Activity.all_by_participant(base_user)["data"]
                 if x["name"] == activity_name][0]
    copy_act = {}
    for val in activity:
        if val != "id":
            copy_act[val] = activity[val]

    # Copy activity into all users
    for part in parts:
        all_acts = LAMP.Activity.all_by_participant(participant_id=part)['data']
        act_list = [x for x in all_acts if x["name"] == activity_name]
        for act in act_list:
            LAMP.Activity.update(activity_id=act['id'], activity_activity=copy_act)
            for attach_name in LAMP.Type.list_attachments(activity["id"])["data"]:
                if attach_name not in excluded_tags:
                    LAMP.Type.set_attachment(act["id"], "me", attach_name,
                        body=LAMP.Type.get_attachment(activity["id"], attach_name)["data"])

def get_part_id_from_name(name, parts):
    """ Find the id which has the lamp.name == name
    """
    # Get the tecc participants
    for part in parts:
        if LAMP.Type.get_attachment(part, "lamp.name")["data"] == name:
            return part
    return -1

def get_activity_names(part_id, sample_length = -1, end_of_window = int(time.time() * 1000)):
    """ Get activity names and specs for a participant.

        Args:
            part_id (string): the participant_id
            sample_length (float, default: -1, unit: days): get the activities from
                the previous x days. If -1, all data will be used
            end_of_window (float, default: current time, unit: ms): the end
                of the window to pull data in ms
        Returns:
            The DataFrame of ActivityEvents with two additional columns:
            "name" and "spec" from the Activity data
        Note: this will not account for deleted activities.
            Please refer to db.py for information on deleted activities.
    """
    df_names = []
    df_type = []
    df_act_events = LAMP.ActivityEvent.all_by_participant(part_id)["data"]
    if sample_length > 0:
        df_act_events = [x for x in df_act_events if
                       (x["timestamp"] > end_of_window - sample_length * MS_IN_DAY)]
    df_act_events = pd.DataFrame(df_act_events)
    act_names = pd.DataFrame(LAMP.Activity.all_by_participant(part_id)["data"])
    df_names = []
    for j in range(len(df_act_events)):
        if len(list(act_names[act_names["id"] == df_act_events.loc[j, "activity"]]["name"])) > 0:
            df_names.append(list(act_names[act_names["id"] ==
                                           df_act_events.loc[j, "activity"]]["name"])[0])
            df_type.append(list(act_names[act_names["id"] ==
                            df_act_events.loc[j, "activity"]]["spec"])[0].split(".")[1])
        else:
            df_names.append(None)
            df_type.append(None)
    df_act_events["name"] = df_names
    df_act_events["spec"] = df_type
    return df_act_events

def set_graph(target, key, graph, display_on_patient_portal=False, set_on_parents=False):
    """ Attaches a graph to a target in LAMP. If the target is a participant,
        graphs can also be attached for viewing in the data portal or
        patient portal.

        Args:
            target: LAMP ID to set a graph tag on.
            graph: A JSON representation of a vega spec
            display_on_patient_portal: if True,
                graph displays on patient portal
            set_on_parents: if True, graph is made
                available to parents in the data portal
        Returns:
            None
    """

    if not re.match(r'(^[A-Za-z_.0-9]+$)',key):
        #Attachment names should be alphanumeric with '.' and '_' characters
        #We attempt to fix and warn a common mistake
        key = key.replace(' ','_')
        if not re.match(r'(^[A-Za-z_.0-9]+$)',key):
            raise ValueError("""Please use an alphanumeric key with '.' and '_'
            characters for LAMP attachments""")
        print('''Coerced invalid attachments string to correctness. Next time,
        please use an alphanumeric key with '.' and '_'
        characters for LAMP attachments''')


    LAMP.Type.set_attachment(target, "me",
                             attachment_key=key,
                             body=graph)

    if not 'Study' in LAMP.Type.parent(target)['data']:
        return

    if display_on_patient_portal:
        if not re.match(r'(^lamp.dashboard.experimental.)',key):
            print("""Warning! Names that do not start with 'lamp.dashboard.experimental'
            may not be shown to participants on the participant portal.""")
        #Add the graph to the list of displayed graphs
        if EXPERIMENTAL_NAME in LAMP.Type.list_attachments(target)['data']:
            current_selection = LAMP.Type.get_attachment(target,
                                                         EXPERIMENTAL_NAME)['data']
            current_selection += [key]
            LAMP.Type.set_attachment(target, "me",
                                     attachment_key = EXPERIMENTAL_NAME,
                                     body=list(set(current_selection)))
        else:
            LAMP.Type.set_attachment(target, "me",
                                     attachment_key = EXPERIMENTAL_NAME,
                                     body=[key])
    if set_on_parents:
        #Attach the name to researcher and study wide tags for the data portal
        for lamp_type,_id in LAMP.Type.parent(target)['data'].items():
            try:
                attachment=f'lamp.dashboard.{lamp_type.lower()}_tags'
                current_attachments = LAMP.Type.get_attachment(_id,
                                                               attachment)['data']
            except LAMP.ApiException:
                current_attachments = []
            new_attachments = list(set(current_attachments + [key]))
            LAMP.Type.set_attachment(_id, 'me',
                                     f'lamp.dashboard.{lamp_type.lower()}_tags',
                                     body=new_attachments)
