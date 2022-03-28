""" Module for averaging results for each game """
from ..feature_types import secondary_feature
from ..primary.game_level_scores import game_level_scores

@secondary_feature(
    name="cortex.game_results",
    dependencies=[game_level_scores]
)
def game_results(name_of_game, **kwargs):
    """ Returns the average game results.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for
                which the feature is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for
                which the feature is being generated. Required.
        name_of_game (str): The name of the game to return average scores.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The average score for this game.
                For cats_and_dogs, spatial_span, jewels_a, jewels_b: average tap time (ms)
                For balloon_risk: average number of pumps
                For pop_the_bubbles: average percent correct of no-go trials
    """
    all_scores = game_level_scores(name_of_game=name_of_game, **kwargs)['data']
    game_avg = None
    if len(all_scores) > 0:
        if "avg_tap_time" in all_scores[0]:
            game_avg = sum([x["avg_tap_time"] for x in all_scores]) / len(all_scores)
        elif "avg_NO_go_perc_correct" in all_scores[0]:
            game_avg = sum([x["avg_NO_go_perc_correct"] for x in all_scores]) / len(all_scores)
        elif "avg_pumps" in all_scores[0]:
            game_avg = sum([x["avg_pumps"] for x in all_scores]) / len(all_scores)
    return {'timestamp': kwargs['start'], 'value': game_avg}
