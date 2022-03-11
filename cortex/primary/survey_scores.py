""" Module for computing survey scores """
from itertools import groupby
import numpy as np
import LAMP
from ..feature_types import primary_feature, log
from ..raw.survey import survey

@primary_feature(
    name="cortex.survey_scores",
    dependencies=[survey]
)
def survey_scores(scoring_dict,
                  attach=False,
                  **kwargs):
    """
    Get survey scores

    Args:
        scoring_dict (dict): Maps survey questions to categories, for scoring.
            Must have keys: "category_list": [list of category strings]
                            "questions": {
                                "question text": {"category": something from list, "scoring": type of scoring},
                            }
                            "map0": {
                                "none": 0,
                                "some": 1,
                                "all": 2
                            }
            Types of scoring:
                "value": will cast the result to an int
                "boolean": "Yes" --> 1, "No" --> 0
                map to a dictionary: give the name of the dictionary (ex: "map0",
                    and create a corresponding dictionary in the scoring_dict)
                Non-numeric scores are not supported at this time.
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

    # Grab the list of surveys and ALL ActivityEvents which are filtered locally.
    _grp = groupby(survey(replace_ids=True, **kwargs)['data'],
                   lambda x: (x['timestamp'], x['survey']))
    participant_results = [{
        'timestamp': key[0],
        'activity': key[1],
        'temporal_slices': list(group)
    } for key, group in _grp]

    if len(participant_results) > 0:
        has_raw_data = 1
    else:
        has_raw_data = 0

    ret = []

    for s in participant_results:
        ret0 = {}
        survey_end_time = s['timestamp'] + sum([q['duration'] for q in s['temporal_slices']])
        for temp in s["temporal_slices"]:
            if "value" not in temp or "item" not in temp:
                continue
            if (temp["item"] not in scoring_dict["questions"] or
                (temp["item"] in scoring_dict["questions"]
                 and scoring_dict["questions"][temp["item"]]["category"] not in scoring_dict["category_list"])):
                continue
            else:
                ques_info = scoring_dict["questions"][temp["item"]]
                val = score_question(temp["value"], temp["item"], scoring_dict)
                if val is not None:
                    if ques_info["category"] not in ret0:
                        ret0[ques_info["category"]] = {"timestamp": s["timestamp"], "value": 0}
                    ret0[ques_info["category"]]["value"] += val
        for k in ret0.keys():
            if len(ret0[k]) > 0:
                ret.append({
                    "start": ret0[k]["timestamp"],
                    "end": survey_end_time,
                    "category": k,
                    "score": ret0[k]["value"],
                })
    return {'data': ret,
            'has_raw_data': has_raw_data}

def score_question(val, ques, scoring_dict):
    """ Score an individual question.

        Args:
            val - the value from temporal slices
            ques - the question (or the question that the question maps to)
            scoring_dict - the json info with scoring maps
        Returns:
            The score
    """
    if "map_to" in scoring_dict["questions"][ques]:
        return score_question(val,
                              scoring_dict["questions"][scoring_dict["questions"]["map_to"]],
                              scoring_dict)
    ques_info = scoring_dict["questions"][ques]
    if val is None:
        return None
    if ques_info["scoring"] == "value":
        return int(val)
    elif ques_info["scoring"] == "raw":
        return val
    elif ques_info["scoring"] == "boolean":
        return int(val == "Yes")
    elif ques_info["scoring"] in scoring_dict:
        if val in scoring_dict[ques_info["scoring"]]:
            mapped_val = scoring_dict[ques_info["scoring"]][val]
        else:
            log.info("*" + val + "* is not in the scoring key " + ques_info["scoring"] + " for question *" + ques + "* please try again.")
            return None
        return mapped_val
    log.info("Scoring type is not valid. Please try again.")
    return None
