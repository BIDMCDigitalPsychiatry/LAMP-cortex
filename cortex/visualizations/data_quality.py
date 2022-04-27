""" Module to create data graphs and attach them to the data portal """
import time
import datetime
import json
import logging
import altair as alt
import LAMP
import pandas as pd
import cortex
from ..utils.useful_functions import get_activity_names, generate_ids, set_graph

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
MS_IN_DAY = 24 * 3600 * 1000


#### -------- Global variables -------- ####
b = datetime.datetime.fromtimestamp((time.time() * 1000) / 1000)
formatted_date = datetime.date.strftime(b, "%m/%d/%Y")

#### -------- General functions -------- ####
def get_parts(researcher_id):
    """ Function to get a list of participant ids for a researcher

        Args:
            researcher_id: the researcher id
        Returns:
            A list of participant ids and study names
    """
    participants = []
    for study in LAMP.Study.all_by_researcher(researcher_id)['data']:
        curr = []
        curr += (p['id'] for p in LAMP.Participant.all_by_study(study['id'])['data'])
        if len(curr) >= 1:
            for part in curr:
                participants.append({
                    "participant_id": part,
                    "study_name": study["name"]
                })
    return participants

def get_data_tags_df(participants):
    """ Produce the data quality tags.

        Args:
            participants: the participants to get data quality
    """
    start_time = int(time.time()) * 1000 - 7 * MS_IN_DAY
    end_time = int(time.time()) * 1000
    dict0 = []
    for part in participants:
        ## get screen state ##
        screen_state = 0
        for time_val in range(start_time, end_time, MS_IN_DAY):
            ss_data = LAMP.SensorEvent.all_by_participant(participant_id=part["participant_id"],
                                                     origin="lamp.device_state",
                                                     _from=time_val,
                                                     to=time_val+MS_IN_DAY,
                                                     _limit=1)["data"]
            if len(ss_data) > 0:
                screen_state += 1
        prev_screen_state = LAMP.SensorEvent.all_by_participant(
                                        participant_id=part["participant_id"],
                                        origin="lamp.device_state",
                                        _limit=1)["data"]
        if len(prev_screen_state) == 0:
            prev_screen_state = None
        else:
            prev_screen_state = prev_screen_state[0]["timestamp"]

        ## get gps ##
        gps_df = pd.DataFrame.from_dict(
            cortex.secondary.data_quality.data_quality(id=part["participant_id"],
                                                   start=start_time,
                                                   end=end_time + 1,
                                                   resolution=MS_IN_DAY,
                                                   feature="gps",
                                                   bin_size=60 * 60 * 1000)['data'])
        gps_df['timestamp'] = pd.to_datetime(gps_df['timestamp'], unit='ms')
        if len(gps_df[gps_df["value"] == 0]) > 0:
            gps_missing_days = list(gps_df[gps_df["value"] == 0]["timestamp"].dt.date)
        else:
            gps_missing_days = None
        gps = gps_df[gps_df["value"] != 0]["value"].mean()

        ## get acc ##
        acc_df = pd.DataFrame.from_dict(
            cortex.secondary.data_quality.data_quality(id=part["participant_id"],
                                                   start=start_time,
                                                   end=end_time + 1,
                                                   resolution=MS_IN_DAY,
                                                   feature="gps",
                                                   bin_size=60 * 60 * 1000)['data'])
        acc_df['timestamp'] = pd.to_datetime(acc_df['timestamp'], unit='ms')
        if len(acc_df[acc_df["value"] == 0]) > 0:
            acc_missing_days = list(acc_df[acc_df["value"] == 0]["timestamp"].dt.date)
        else:
            acc_missing_days = None
        acc = acc_df[acc_df["value"] != 0]["value"].mean()

        if screen_state == 7:
            screen_state_quality = "good"
        elif prev_screen_state is not None:
            screen_state_quality = "bad"
        else:
            screen_state_quality = "missing"
        if gps > 0.8:
            gps_quality = "good"
        elif gps > 0.5:
            gps_quality = "okay"
        else:
            gps_quality = "bad"
        if gps_missing_days is not None and gps > 0:
            gps_quality = gps_quality + "_missing"
        elif gps_missing_days is not None:
            gps_quality = "missing"
        if acc > 0.8:
            acc_quality = "good"
        elif acc > 0.5:
            acc_quality = "okay"
        else:
            acc_quality = "bad"
        if acc_missing_days is not None and acc > 0:
            acc_quality = acc_quality + "_missing"
        elif acc_missing_days is not None:
            acc_quality = "missing"
        dict0.append({"part_id": part["participant_id"],
              "screen_state": screen_state,
              "last_screen_date": prev_screen_state,
              "acc": acc,
              "acc_missing_days": acc_missing_days,
              "gps": gps,
              "gps_missing_days": gps_missing_days,
              "screen_state_quality": screen_state_quality,
              "gps_quality": gps_quality,
              "acc_quality": acc_quality,})

    df_orig = pd.DataFrame(dict0)

    # Prepare df in form for altair
    df2 = []
    for i in range(len(df_orig)):
        for qual_type in ["screen_state_quality", "acc_quality", "gps_quality"]:
            if qual_type in ["gps_quality", "acc_quality"]:
                qual_prefix = qual_type.split("_")[0]
                dates = json.dumps(df_orig.loc[i, qual_prefix + "_missing_days"], indent=4,
                                   sort_keys=True, default=str)
                qual = df_orig.loc[i, qual_prefix]
            else:
                dates = None
                qual = df_orig.loc[i, "screen_state"]
            part = df_orig.loc[i, "part_id"]
            study_name = [x["study_name"] for x in participants if x["participant_id"] == part][0]
            df2.append({
                "Study ID (Participant ID)": study_name + " ("  + part + ")",
                "Participant ID": part,
                "Quality": df_orig.loc[i, qual_type],
                "Type": qual_type,
                "Missing days": dates,
                "Average frequency": qual,
            })
    df2 = pd.DataFrame(df2)
    return df_orig, df2


#### -------- Make graphs -------- #####
def make_activity_count_graph(participants, researcher_id):
    """ Make activity count graph.

        Args:
            participants: the participant ids and study ids
            researcher_id: the researcher id
    """
    game_names = ["pop_the_bubbles", "balloon_risk", "jewels_b",
                  "spatial_span", "jewels_a", "cats_and_dogs"]

    act_counts = {"Study ID (Participant ID)": [], "Count": [], "Activity Type": []}
    for part in participants:
        act_df = get_activity_names(part["participant_id"], sample_length=7)
        for _ in range(6):
            act_counts["Study ID (Participant ID)"].append(part["study_name"] +
                                                    " (" + part["participant_id"] + ")")
        # Survey
        act_counts["Activity Type"].append("Survey")
        act_counts["Count"].append(len(act_df[act_df["type"] == "survey"]))
        # Tips
        act_counts["Activity Type"].append("Tips")
        act_counts["Count"].append(len(act_df[act_df["type"] == "tips"]))
        # Breathe
        act_counts["Activity Type"].append("Breathe")
        act_counts["Count"].append(len(act_df[act_df["type"] == "breathe"]))
        # Group
        act_counts["Activity Type"].append("Group")
        act_counts["Count"].append(len(act_df[act_df["type"] == "group"]))
        # Games
        act_counts["Activity Type"].append("Games")
        act_counts["Count"].append(len(act_df[act_df["type"].isin(game_names)]))
        # Other
        act_counts["Activity Type"].append("Other")
        act_counts["Count"].append(len(act_df[(act_df["type"] != "survey") &
                                          (act_df["type"] != "tips") &
                                          (act_df["type"] != "breathe") &
                                          (act_df["type"] != "group") &
                                          (~act_df["type"].isin(game_names))]))
    act_counts = pd.DataFrame(act_counts)

    val = ["Other", "Tips", "Survey", "Group", "Games", "Breathe"]
    col = ["crimson", "limegreen", "royalblue", "gray", "gold", "magenta"]
    chart = alt.Chart(act_counts,
                title="Activities in the last 7 days (updated:"
                      + f" {formatted_date})").mark_bar().encode(
        x=alt.X("Study ID (Participant ID)"),
        y=alt.Y("Count"),
        color=alt.Color("Activity Type", scale=alt.Scale(domain=val, range=col)),
        order=alt.Order(
          'Activity Type',
          sort='ascending'
        ),
        tooltip=['Count']
    )
    set_graph(researcher_id,
              "graphs.data_quality.activity_counts",
              (chart).to_dict())

def make_data_qual_tags(researcher_id, qual_df2):
    """ Make the data quality tags graph. Attach the data portal.

        Args:
            researcher_id: the researcher id
            qual_df2: the quality df in the format needed for plotting
    """
    val = ["missing", "bad", "okay", "good", "bad_missing", "okay_missing", "good_missing"]
    col = ["gray", "red", "gold", "limegreen", "crimson", "orange", "green"]

    chart = alt.Chart(qual_df2, title=f"Data quality (updated {formatted_date})").mark_bar().encode(
        x="Study ID (Participant ID)",
        y='Type',
        color=alt.Color('Quality', scale=alt.Scale(domain=val, range=col)),
        tooltip=['Missing days', "Average frequency"]
    )

    set_graph(researcher_id,
              "graphs.data_quality.quality_tags",
              (chart).to_dict())

def make_passive_data_graphs(participants, researcher_id, qual_df1):
    """ Make the passive data feature (screen duration, steps, hometime) graphs.

        Args:
            participants: the list of participant ids and study names
            researcher_id: the researcher id
            qual_df1: the quality of each feature. Features below the quality
                threshold will not be plotted.
    """
    step_counts = []
    for part in participants:
        steps = pd.DataFrame(
            cortex.secondary.step_count.step_count(id=part["participant_id"],
                                                   start=int(time.time() * 1000) - 7 * MS_IN_DAY,
                                                   end=int(time.time() * 1000) + 1,
                                                   resolution=MS_IN_DAY)["data"]).dropna()
        if len(steps) > 0:
            steps = steps["value"].mean()
        else:
            steps = 0
        step_counts.append({
            "Study ID (Participant ID)": part["study_name"] + " (" + part["participant_id"] + ")",
            "Average steps": steps,
        })
    step_counts = pd.DataFrame(step_counts)

    screen_dur = []
    for part in participants:
        screen = 0
        if (list(qual_df1[qual_df1["part_id"] == part["participant_id"]]
                ["screen_state_quality"])[0] == "good"):
            screen = pd.DataFrame(
                cortex.secondary.screen_duration.screen_duration(id=part["participant_id"],
                                             start=int(time.time() * 1000) - 7 * MS_IN_DAY,
                                             end=int(time.time() * 1000) + 1,
                                             resolution=MS_IN_DAY)["data"]).dropna()
            if len(screen) > 0:
                screen = screen["value"].mean() / (3600 * 1000)
        screen_dur.append({
            "Study ID (Participant ID)": part["study_name"] + " (" + part["participant_id"] + ")",
            "Average screen time (hrs)": screen,
        })
    screen_dur = pd.DataFrame(screen_dur)

    hometime = []
    for part in participants:
        home = 0
        gps_qual = list(qual_df1[qual_df1["part_id"] == part["participant_id"]]["gps_quality"])[0]
        if gps_qual in ["good", "okay"]:
            home = pd.DataFrame(
                cortex.secondary.hometime.hometime(id=part["participant_id"],
                                                   start=int(time.time() * 1000) - 7 * MS_IN_DAY,
                                                   end=int(time.time() * 1000) + 1,
                                                   resolution=MS_IN_DAY)["data"]).dropna()
            if len(home) > 0:
                home = home["value"].mean() / (3600 * 1000)
        hometime.append({
            "Study ID (Participant ID)": part["study_name"] + " (" + part["participant_id"] + ")",
            "Average hometime (hrs)": home,
        })
    hometime = pd.DataFrame(hometime)

    chart1 = alt.Chart(screen_dur, title="Average screen duration (updated: "
                       + f"{formatted_date})").mark_bar(color="orange").encode(
        x=alt.X("Study ID (Participant ID)"),
        y="Average screen time (hrs)",
    )

    chart2 = alt.Chart(step_counts, title="Average steps (updated: "
                       + f"{formatted_date})").mark_bar(color="turquoise").encode(
        x=alt.X("Study ID (Participant ID)"),
        y="Average steps",
    )

    chart3 = alt.Chart(hometime, title="Average hometime (updated: "
                       + f"{formatted_date})").mark_bar(color="crimson").encode(
        x=alt.X("Study ID (Participant ID)"),
        y="Average hometime (hrs)",
    )
    if len(participants) < 15:
        chart12 = alt.hconcat(chart1, chart2)
    else:
        chart12 = alt.vconcat(chart1, chart2)

    set_graph(researcher_id,
              "graphs.data_quality.passive_features",
              (alt.vconcat(chart12, chart3)).to_dict())

def make_survey_count_graph_by_name(participants, researcher_id, name):
    """ Function to make survey count graphs for an individual survey.

        Args:
            participants: the list of participant ids and study names
            researcher_id: the researcher id
            name: the name of the survey. Must be exact.
        The graph tag will be graphs.data_quality.name
    """
    act_counts = {"Study ID (Participant ID)": [], "Count": []}
    for part in participants:
        act_df = get_activity_names(part["participant_id"], sample_length=7)
        act_counts["Study ID (Participant ID)"].append(
            part["study_name"] + " (" + part["participant_id"] + ")")
        act_counts["Count"].append(len(act_df[act_df["name"] == name]))
    act_counts = pd.DataFrame(act_counts)

    chart = alt.Chart(act_counts, title="Activities in the last 7 days (updated: "
                      + f"{formatted_date})").mark_bar(color="blueviolet").encode(
        x=alt.X("Study ID (Participant ID)"),
        y=alt.Y("Count"),
        tooltip=['Count']
    )
    key_name = name.replace(" ", "_").lower()
    key_name = f"graphs.data_quality.{key_name}"
    set_graph(researcher_id,
              key_name,
              (chart).to_dict())

def make_percent_completion_graph(spec, researcher_id, name):
    """ Function to make a graph of the percent of activites
        (from the spec) that have been completed.

        Args:
            spec (dict): the specification dict
                {participant / study / researcher id:
                   [
                       {
                           "activity_name": "some_activity",
                           "count": 2,
                           "time_interval": MS_IN_DAY * 7
                       }
                   ]
                }
                example spec:
                {"U12345678":
                   [
                       {
                           "activity_name": "Daily Survey",
                           "count": 7,
                           "time_interval": MS_IN_DAY * 7
                       }
                   ]
                 "shdjei293jfj":
                     [
                       {
                           "activity_name": "Mood",
                           "count": 3,
                           "time_interval": MS_IN_DAY * 7
                       },
                       {
                           "activity_name": "Anxiety",
                           "count": 2,
                           "time_interval": MS_IN_DAY * 5
                       }
                   ]
                }
            Note: behavior is not defined if participants are in
                multiple keys.
            researcher_id: the researcher id
            name: the name of the survey. Must be exact.
        The graph tag will be graphs.data_quality.name
    """
    perc_compl = {"Study ID (Participant ID)": [], "Completion": []}
    for k in spec:
        part_list = generate_ids(k)
        for part in part_list:
            part_count = 0
            total_count = 0
            for act in spec[k]:
                act_df = get_activity_names(part,
                                    sample_length=act["time_interval"] / MS_IN_DAY)
                part_count += min(len(act_df[act_df["name"] == act["activity_name"]]),
                                  act["count"])
                total_count += act["count"]
            try:
                study_name = LAMP.Type.get_attachment(part, "lamp.name")["data"]
            except LAMP.ApiException:
                study_name = ""
            perc_compl["Study ID (Participant ID)"].append(
                                study_name + " (" + part + ")")
            perc_compl["Completion"].append(part_count / total_count)
    perc_compl = pd.DataFrame(perc_compl)

    chart = alt.Chart(perc_compl, title="Activity completion (updated: "
                      + f"{formatted_date})").mark_bar(color="deepskyblue").encode(
        x=alt.X("Study ID (Participant ID)"),
        y=alt.Y("Completion", scale=alt.Scale(domain=[0, 1])),
        tooltip=['Completion']
    )
    key_name = name.replace(" ", "_").lower()
    key_name = f"graphs.data_quality.{key_name}"
    set_graph(researcher_id,
              key_name,
              (chart).to_dict())

def clear_chart(researcher_id, name):
    """ Function to clear a chart from the data portal.

        Args:
            researcher_id: the researcher_id
            name: the name of the plot
    """
    key_name = "graphs.data_quality." + name
    set_graph(researcher_id,
              key_name,
              None)

def data_quality(researcher_id):
    """ Function to create quality graphs for data monitoring.
    """
    if len(researcher_id) == 0 or len(LAMP.Researcher.view(researcher_id)["data"]) == 0:
        log.warning('Invalid researcher id. Aborting.')
        return

    start_time = time.time()
    participants = get_parts(researcher_id)

    if len(participants) == 0:
        log.warning("This researcher has no participants. Please check researcher id.")
        return

    qual_df1, qual_df2 = get_data_tags_df(participants)

    # Make graphs
    make_activity_count_graph(participants, researcher_id)
    make_data_qual_tags(researcher_id, qual_df2)
    make_passive_data_graphs(participants, researcher_id, qual_df1)
    time_elapsed = "{:.2f}".format((time.time() - start_time) / 60)
    log.info("Run time: %s minutes", time_elapsed)
