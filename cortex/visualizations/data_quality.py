""" Module to create data graphs and attach them to the data portal """
import os
import time
import datetime
import json
import logging
import altair as alt
import LAMP
import pandas as pd
import cortex

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
        curr+=(p['id'] for p in LAMP.Participant.all_by_study(study['id'])['data'])
        if len(curr) >= 1:
            for p in curr:
                participants.append({
                    "participant_id": p,
                    "study_name": study["name"]
                })
    return participants

def get_act_names(part_id, days_ago):
    """ Get an activity df with names of activities and types.

        Args:
            part_id: the participant id
            days_ago: number of prior days to include
                (ie days_ago=7 for the previous week)
        Returns:
            the df with names and types
    """
    df_names = []
    df_type = []
    df = LAMP.ActivityEvent.all_by_participant(part_id)["data"]
    df = pd.DataFrame([x for x in df if
                       (x["timestamp"] > int(time.time() * 1000) - days_ago * MS_IN_DAY)])
    act_names = pd.DataFrame(LAMP.Activity.all_by_participant(part_id)["data"])
    df_names = []
    for j in range(len(df)):
        if len(list(act_names[act_names["id"] == df.loc[j, "activity"]]["name"])) > 0:
            df_names.append(list(act_names[act_names["id"] == df.loc[j, "activity"]]
                                 ["name"])[0])
            df_type.append(list(act_names[act_names["id"] == df.loc[j, "activity"]]
                                ["spec"])[0].split(".")[1])
        else:
            df_names.append(None)
            df_type.append(None)
    df["name"] = df_names
    df["type"] = df_type
    return df

def get_data_tags_df(participants):
    """ Produce the data quality tags.

        Args:
            participants: the participants to get data quality
    """
    start_time = int(time.time()) * 1000 - 7 * MS_IN_DAY
    end_time = int(time.time()) * 1000
    dict0 = []
    for p in participants:
        ## get screen state ##
        screen_state = 0
        for d in range(start_time, end_time, MS_IN_DAY):
            ss = LAMP.SensorEvent.all_by_participant(participant_id=p["participant_id"],
                                                     origin="lamp.screen_state",
                                                     _from=d,
                                                     to=d+MS_IN_DAY,
                                                     _limit=1)["data"]
            if len(ss) == 0:
                ss = LAMP.SensorEvent.all_by_participant(participant_id=p["participant_id"],
                                                     origin="lamp.device_state",
                                                     _from=d,
                                                     to=d+MS_IN_DAY,
                                                     _limit=1)["data"]
            if len(ss) > 0:
                screen_state += 1
        prev_screen_state = LAMP.SensorEvent.all_by_participant(participant_id=p["participant_id"],
                                                     origin="lamp.screen_state",
                                                     _limit=1)["data"]

        if len(prev_screen_state) == 0:
            prev_screen_state = LAMP.SensorEvent.all_by_participant(
                                                     participant_id=p["participant_id"],
                                                     origin="lamp.device_state",
                                                     _limit=1)["data"]
        if len(prev_screen_state) == 0:
            prev_screen_state = None
        else:
            prev_screen_state = prev_screen_state[0]["timestamp"]

        ## get gps ##
        df = pd.DataFrame.from_dict(
            cortex.secondary.data_quality.data_quality(id=p["participant_id"],
                                                   start=start_time,
                                                   end=end_time + 1,
                                                   resolution=MS_IN_DAY,
                                                   feature="gps",
                                                   bin_size=60 * 60 * 1000)['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        if len(df[df["value"] == 0]) > 0:
            gps_missing_days = list(df[df["value"] == 0]["timestamp"].dt.date)
        else:
            gps_missing_days = None
        gps = df[df["value"] != 0]["value"].mean()

        ## get acc ##
        df = pd.DataFrame.from_dict(
            cortex.secondary.data_quality.data_quality(id=p["participant_id"],
                                                   start=start_time,
                                                   end=end_time + 1,
                                                   resolution=MS_IN_DAY,
                                                   feature="gps",
                                                   bin_size=60 * 60 * 1000)['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        if len(df[df["value"] == 0]) > 0:
            acc_missing_days = list(df[df["value"] == 0]["timestamp"].dt.date)
        else:
            acc_missing_days = None
        acc = df[df["value"] != 0]["value"].mean()

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
        d0 = {"part_id": p["participant_id"],
              "screen_state": screen_state,
              "last_screen_date": prev_screen_state,
              "acc": acc,
              "acc_missing_days": acc_missing_days,
              "gps": gps,
              "gps_missing_days": gps_missing_days,
              "screen_state_quality": screen_state_quality,
              "gps_quality": gps_quality,
              "acc_quality": acc_quality,}
        dict0.append(d0)

    df = pd.DataFrame(dict0)

    # Prepare df in form for altair
    df2 = []
    for x in range(len(df)):
        for y in ["screen_state_quality", "acc_quality", "gps_quality"]:
            if y == "acc_quality":
                dates = json.dumps(df.loc[x, "acc_missing_days"], indent=4,
                                   sort_keys=True, default=str)
                qual = df.loc[x, "acc"]
            elif y == "gps_quality":
                dates = json.dumps(df.loc[x, "gps_missing_days"], indent=4,
                                   sort_keys=True, default=str)
                qual = df.loc[x, "gps"]
            else:
                dates = None
                qual = df.loc[x, "screen_state"]
            p = df.loc[x, "part_id"]
            study_name = [x["study_name"] for x in participants if x["participant_id"] == p][0]
            df2.append({
                "Study ID (Participant ID)": study_name + " ("  + p + ")",
                "Participant ID": p,
                "Quality": df.loc[x, y],
                "Type": y,
                "Missing days": dates,
                "Average frequency": qual,
            })
    df2 = pd.DataFrame(df2)
    return df, df2


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
    for p in participants:
        df = get_act_names(p["participant_id"], 7)
        for _ in range(6):
            act_counts["Study ID (Participant ID)"].append(p["study_name"] +
                                                    " (" + p["participant_id"] + ")")
        # Survey
        act_counts["Activity Type"].append("Survey")
        act_counts["Count"].append(len(df[df["type"] == "survey"]))
        # Tips
        act_counts["Activity Type"].append("Tips")
        act_counts["Count"].append(len(df[df["type"] == "tips"]))
        # Breathe
        act_counts["Activity Type"].append("Breathe")
        act_counts["Count"].append(len(df[df["type"] == "breathe"]))
        # Group
        act_counts["Activity Type"].append("Group")
        act_counts["Count"].append(len(df[df["type"] == "group"]))
        # Games
        act_counts["Activity Type"].append("Games")
        act_counts["Count"].append(len(df[df["type"].isin(game_names)]))
        # Other
        act_counts["Activity Type"].append("Other")
        act_counts["Count"].append(len(df[(df["type"] != "survey") &
                                          (df["type"] != "tips") &
                                          (df["type"] != "breathe") &
                                          (df["type"] != "group") &
                                          (~df["type"].isin(game_names))]))
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
    LAMP.Type.set_attachment(researcher_id, "me",
                         attachment_key = "graphs.data_quality.activity_counts",
                         body=(chart).to_dict())

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

    LAMP.Type.set_attachment(researcher_id, "me",
                         attachment_key = "graphs.data_quality.quality_tags",
                         body=(chart).to_dict())

def make_passive_data_graphs(participants, researcher_id, qual_df1):
    """ Make the passive data feature (screen duration, steps, hometime) graphs.

        Args:
            participants: the list of participant ids and study names
            researcher_id: the researcher id
            qual_df1: the quality of each feature. Features below the quality
                threshold will not be plotted.
    """
    step_counts = []
    for p in participants:
        steps = pd.DataFrame(
            cortex.secondary.step_count.step_count(id=p["participant_id"],
                                                   start=int(time.time() * 1000) - 7 * MS_IN_DAY,
                                                   end=int(time.time() * 1000) + 1,
                                                   resolution=MS_IN_DAY)["data"])
        steps = steps.dropna()
        if len(steps) > 0:
            steps = steps["value"].mean()
        else:
            steps = 0
        step_counts.append({
            "Study ID (Participant ID)": p["study_name"] + " (" + p["participant_id"] + ")",
            "Average steps": steps,
        })
    step_counts = pd.DataFrame(step_counts)

    screen_dur = []
    for p in participants:
        screen = 0
        if (list(qual_df1[qual_df1["part_id"] == p["participant_id"]]
                ["screen_state_quality"])[0] == "good"):
            screen = pd.DataFrame(
                cortex.secondary.screen_duration.screen_duration(id=p["participant_id"],
                                             start=int(time.time() * 1000) - 7 * MS_IN_DAY,
                                             end=int(time.time() * 1000) + 1,
                                             resolution=MS_IN_DAY)["data"])
            screen = screen.dropna()
            if len(screen) > 0:
                screen = screen["value"].mean() / (3600 * 1000)
        screen_dur.append({
            "Study ID (Participant ID)": p["study_name"] + " (" + p["participant_id"] + ")",
            "Average screen time (hrs)": screen,
        })
    screen_dur = pd.DataFrame(screen_dur)

    hometime = []
    for p in participants:
        home = 0
        gps_qual = list(qual_df1[qual_df1["part_id"] == p["participant_id"]]["gps_quality"])[0]
        if gps_qual in ["good", "okay"]:
            home = pd.DataFrame(
                cortex.secondary.hometime.hometime(id=p["participant_id"],
                                                   start=int(time.time() * 1000) - 7 * MS_IN_DAY,
                                                   end=int(time.time() * 1000) + 1,
                                                   resolution=MS_IN_DAY)["data"])
            home = home.dropna()
            if len(home) > 0:
                home = home["value"].mean() / (3600 * 1000)
        hometime.append({
            "Study ID (Participant ID)": p["study_name"] + " (" + p["participant_id"] + ")",
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
    chart = alt.vconcat(chart12, chart3)
    LAMP.Type.set_attachment(researcher_id, "me",
                         attachment_key = "graphs.data_quality.passive_features",
                         body=(chart).to_dict())

def make_survey_count_graph_by_name(participants, researcher_id, name):
    """ Function to make survey count graphs for an individual survey.

        Args:
            participants: the list of participant ids and study names
            researcher_id: the researcher id
            name: the name of the survey. Must be exact.
        The graph tag will be graphs.data_quality.name
    """
    act_counts = {"Study ID (Participant ID)": [], "Count": []}
    for p in participants:
        df = get_act_names(p["participant_id"], 7)
        act_counts["Study ID (Participant ID)"].append(
            p["study_name"] + " (" + p["participant_id"] + ")")
        act_counts["Count"].append(len(df[df["name"] == name]))
    act_counts = pd.DataFrame(act_counts)

    chart = alt.Chart(act_counts, title="Activities in the last 7 days (updated: "
                      + f"{formatted_date})").mark_bar(color="blueviolet").encode(
        x=alt.X("Study ID (Participant ID)"),
        y=alt.Y("Count"),
        tooltip=['Count']
    )
    key_name = name.replace(" ", "_").lower()
    key_name = f"graphs.data_quality.{key_name}"
    LAMP.Type.set_attachment(researcher_id, "me",
                         attachment_key = key_name,
                         body=(chart).to_dict())

def clear_chart(researcher_id, name):
    """ Function to clear a chart from the data portal.

        Args:
            researcher_id: the researcher_id
            name: the name of the plot
    """
    key_name = "graphs.data_quality." + name
    LAMP.Type.set_attachment(researcher_id, "me",
                         attachment_key = key_name,
                         body=None)

def data_quality(researcher_id):
    """ Function to create quality graphs for data monitoring.
    """
    # Connect to LAMP
    if not 'LAMP_ACCESS_KEY' in os.environ or not 'LAMP_SECRET_KEY' in os.environ:
        raise Exception("You configure `LAMP_ACCESS_KEY` and `LAMP_SECRET_KEY`"
                        + " (and optionally `LAMP_SERVER_ADDRESS`) to use Cortex.")
    LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
                 os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))

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
