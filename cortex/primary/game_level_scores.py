""" Module for computing game level scores """
import numpy as np
import pandas as pd
from ..feature_types import primary_feature, log
from ..raw.balloon_risk import balloon_risk
from ..raw.cats_and_dogs import cats_and_dogs
from ..raw.jewels_a import jewels_a
from ..raw.jewels_b import jewels_b
from ..raw.pop_the_bubbles import pop_the_bubbles
from ..raw.spatial_span import spatial_span
from .. import raw

# List of valid games
GAMES = ['jewels_a', 'jewels_b', 'balloon_risk',
         'cats_and_dogs', 'pop_the_bubbles', 'spatial_span']

@primary_feature(
    name="cortex.game_level_scores",
    dependencies=[balloon_risk, cats_and_dogs, jewels_a,
                  jewels_b, pop_the_bubbles, spatial_span]
)
def game_level_scores(name_of_game,
                  attach=False,
                  **kwargs):
    """ Get cognitive game scores.

    Args:
        name_of_game (str): The name of the game to score.
        attach (boolean): Indicates whether to use LAMP.Type.attachments in calculating the feature.
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.

    Returns:
        A dictionary with fields:
            data (dict): Survey categories mapped to individual scores.
            has_raw_data (int): Indicates whether there is raw data.
    """
    if name_of_game == 'pop_the_bubbles':
        return score_pop_the_bubbles(**kwargs)
    if name_of_game == 'balloon_risk':
        return score_balloon_risk(**kwargs)
    if name_of_game not in GAMES:
        log.warning('The name of the game is not valid.')
        return {'data': [], 'has_raw_data': 0}
    raw_feature = getattr(getattr(raw, name_of_game), name_of_game)
    data_df = pd.DataFrame(raw_feature(**kwargs)['data'])
    has_raw_data = 1
    if len(data_df) == 0:
        has_raw_data = 0
    data_df = pd.DataFrame(data_df)

    ret = []
    for i in range(len(data_df)):
        game_df = pd.DataFrame(data_df.loc[i, "temporal_slices"])
        if "status" not in game_df and "type" in game_df:
            game_df = game_df.rename(columns={"type": "status"})
        if len(game_df) == 0:
            continue
        for level in np.unique(game_df["level"]):
            level_df = game_df[game_df["level"] == level]
            level_avg = level_df.mean()
            ret.append({
                "start": data_df.loc[i, "timestamp"],
                "end": data_df.loc[i, "timestamp"] + level_df["duration"].sum(),
                "level": level,
                "avg_tap_time": level_df[level_df["duration"] > 0]["duration"].mean(),
                "perc_correct": level_avg["status"],
            })
            if name_of_game in ['jewels_a', 'jewels_b']:
                ret[len(ret) - 1]["jewels_collected"] = len(level_df[level_df["status"]])
    return {'data': ret,
            'has_raw_data': has_raw_data}

def score_pop_the_bubbles(**kwargs):
    """ Helper function to score pop_the_bubbles.
    """
    data_df = pd.DataFrame(pop_the_bubbles(**kwargs)['data'])
    has_raw_data = 1
    if len(data_df) == 0:
        has_raw_data = 0
    ret = []
    for i in range(len(data_df)):
        game_df = pd.DataFrame(data_df.loc[i, "temporal_slices"]).dropna()
        if len(game_df) == 0:
            continue
        for level in np.unique(game_df["level"]):
            level_df = game_df[game_df["level"] == level]
            ret.append({
                "start": data_df.loc[i, "timestamp"],
                "end": data_df.loc[i, "timestamp"] + data_df.loc[i, "duration"],
                "level": level,
                "avg_go_perc_correct":
                    level_df[~level_df['value'].str.contains('no-go')]["type"].mean(),
                "avg_NO_go_perc_correct":
                    level_df[level_df['value'].str.contains('no-go')]["type"].mean()
            })
    return {'data': ret,
            'has_raw_data': has_raw_data}


def score_balloon_risk(**kwargs):
    """ Helper function to score balloon_risk.
    """
    data_df = pd.DataFrame(balloon_risk(**kwargs)['data'])
    has_raw_data = 1
    if len(data_df) == 0:
        has_raw_data = 0
    ret = []
    for i in range(len(data_df)):
        game_df = pd.DataFrame(data_df.loc[i, "temporal_slices"]).dropna()
        for level in np.unique(game_df["level"]):
            level_df = game_df[game_df["level"] == level]
            if "type" in level_df and len(level_df[~level_df["type"]]) > 0:
                avg_pumps = 0
            elif "status" in level_df and len(level_df[~level_df["status"]]) > 0:
                avg_pumps = 0
            else:
                avg_pumps = len(level_df)
            ret.append({
                "start": data_df.loc[i, "timestamp"],
                "end": data_df.loc[i, "timestamp"] + level_df["duration"].sum(),
                "level": level,
                "avg_pumps": avg_pumps,
            })
    return {'data': ret,
            'has_raw_data': has_raw_data}
