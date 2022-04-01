import os
import json
import time
import datetime
import LAMP
import numpy as np
import pandas as pd
LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
            os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))

from ..utils.useful_functions import generate_ids, shift_time
from ..primary.survey_scores import survey_scores

import seaborn as sns
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
from statsmodels.stats.multitest import multipletests


def save_surveys_to_file(part_id, survey_path, scoring_dict):
    """ Save all surveys in seperatate files.

        Args:
            part_id - the participant id
            survey_path - path to the survey directory
            survey_dict - the survey scoring dict
    """
    surveys = survey_scores(id=part_id, start=0, end=int(time.time() * 1000),
                                          scoring_dict=scoring_dict, return_ind_ques=True)["data"]
    for cat in scoring_dict["category_list"]:
        times = np.unique([x["start"] for x in surveys if x["category"] == cat])
        values = [x for x in surveys if x["category"] == cat]
        ret = {x: [] for x in np.unique([x["question"] for x in values])}
        ret["timestamp"] = []
        for t in times:
            ret["timestamp"].append(t)
            for x in np.unique([x["question"] for x in values]):
                curr = [j["score"] for j in surveys if (j["question"] == x) & (j["start"] == t)]
                if len(curr) == 0:
                    curr = None
                else:
                    curr = sum(curr) / len(curr)
                ret[x].append(curr)
        if len(pd.DataFrame(ret)) > 0:
            pd.DataFrame(ret).to_csv(survey_path + part_id + "_" + cat + ".csv")

def get_avg_var_data(parts, scoring_guide, OTHER_GLOBAL_FEATS, OTHER_LOCAL_FEATS, OTHER_LOCAL_SUBFEATS,
                     PASSIVE_FEATS, SURVEY_DIR, PASSIVE_DIR, avg = 1, time_to_include=[-1, -1]):
    """ Get variance and averages for each feature.

        Args:
            parts: the list of participant ids
            scoring_guide: the scoring dicctionary
            OTHER_GLOBAL_FEATS: the list of other global features
            OTHER_LOCAL_FEATS: the list of other local features
            OTHER_LOCAL_SUBFEATS: the list of subfeatures
            PASSIVE_FEATS: the list of passive features
            SURVEY_DIR: The survey directory (also holds other local / global features)
            PASSIVE_DIR: The passive data directory
            avg: whether to do average (1) or variance (0)
            time_to_inlude (units: ms): Whether to include the entire time or restrict to certain days
                from the start of the study (ie first SensorEvent)
                (ex: time_to_include=[86400000,691200000] would be from day 2 to day 8)
        Notes: See example in correlation_plots.ipynb
    """
    # Make sure that the feature order stays consistent
    all_survey_keys = []
    for x in scoring_guide["category_list"]:
        all_survey_keys += [x]
        all_survey_keys += [k for k in scoring_guide["questions"].keys()
            if ("map_to" not in scoring_guide["questions"][k]) and
               (scoring_guide["questions"][k]["category"] == x)]
    all_other_local_keys = []
    for x in OTHER_LOCAL_FEATS:
        all_other_local_keys += [y for y in OTHER_LOCAL_SUBFEATS[x]]
    if avg:
        feat_order = all_survey_keys + OTHER_GLOBAL_FEATS + all_other_local_keys + PASSIVE_FEATS
    else:
        feat_order = all_survey_keys + all_other_local_keys + PASSIVE_FEATS
    avg_df = []
    for p in parts:
        end_time = time.time() * 1000
        start_time = 0
        if time_to_include[0] != -1:
            start_time = LAMP.SensorEvent.all_by_participant(p,
                                                             _limit=-1)["data"]
            if len(start_time) > 0 and "timestamp" in start_time[0]:
                start_time = start_time[0]["timestamp"] + time_to_include[0]
            else:
                continue
        if time_to_include[1] != -1:
            end_time = start_time + time_to_include[1]
        dict0 = {}
        dict0["part_id"] = p
        for f in feat_order:
            dict0[f] = None
        # surveys
        for s in scoring_guide["category_list"]:
            survey_path = SURVEY_DIR + p + "_" + s + ".csv"
            if os.path.exists(survey_path):
                df = pd.read_csv(survey_path)
                df = df[(df["timestamp"] >= start_time) & (df["timestamp"] <= end_time)]
                df = df[[k for k in df.keys() if (k != "timestamp") & (k != "Unnamed: 0")]]
                for k in df:
                    if avg:
                        dict0[k] = list(df[[k]].mean())[0]
                    else:
                        dict0[k] = list(df[[k]].var())[0]
        # global features
        if avg:
            other_global_path = survey_path = SURVEY_DIR + p + "_other_global_feats.csv"
            if os.path.exists(other_global_path):
                df = pd.read_csv(other_global_path)
                df = df[[k for k in df.keys() if (k != "Unnamed: 0") & (k in OTHER_GLOBAL_FEATS)]]
                for k in df:
                    dict0[k] = list(df[k])[0]
        # local features
        for o in OTHER_LOCAL_FEATS:
            feat_path = SURVEY_DIR + p + "_" + o + ".csv"
            if os.path.exists(feat_path):
                df = pd.read_csv(feat_path)
                df = df[(df["timestamp"] >= start_time) & (df["timestamp"] <= end_time)]
                df = df[OTHER_LOCAL_SUBFEATS[o]]
                for k in df:
                    if avg:
                        dict0[k] = list(df[[k]].mean())[0]
                    else:
                        dict0[k] = list(df[[k]].var())[0]
        # passive features
        for s in PASSIVE_FEATS:
            feat_path = PASSIVE_DIR + p + "_" + s + ".pkl"
            if os.path.exists(feat_path):
                df = pd.read_pickle(feat_path)
                df["timestamp"] = df["timestamp"].astype(np.int64) // 10**6
                df = df[(df["timestamp"] >= start_time) & (df["timestamp"] <= end_time)]
                if "value" in df:
                    df = df.rename(columns={"value": s})
                df = df[[s]]
                df = df[df[s] > 0]
                for k in df:
                    if avg:
                        dict0[k] = list(df[[k]].mean())[0]
                    else:
                        dict0[k] = list(df[[k]].var())[0]
        avg_df.append(dict0)
    avg_df = pd.DataFrame(avg_df)
    return avg_df

def get_corr(combined_df, survey_list, feat_list, feat_nonzero=1, survey_nonzero=1, req_list=[], alpha=0.05, show_num=1):
    """ Function to get correlations.

        Args:
            combined_df: df with all of your features
            survey_list: list of survey names
            feat_list: list of features
            feat_nonzero: only include nonzero features
            survey_nonzero: only include nonzero surveys
            req_list: list of dicts in the form {"col_name", "val", "greater_than"}
                where col_name is the name of the column
                val is the value to be greater or less than
                and greater than is 1 for greater, 0 for less
                all given parameters will be applied
            alpha: significance level
        Returns:
            mat: matrix with correlations
            pvals: the p-value strings for printing
            dict_corr: the dictionary of corr, key, p-val and N
    """
    dict_corr = {"key": [], "corr": [], "p-val": [], 'N': []}
    corrected_p_vals = {"pval": [], "row_col": []}
    pvals = []
    mat = np.zeros((len(survey_list), len(feat_list)))
    for i, k in enumerate(survey_list):
        p0 = []
        for j, feat in enumerate(feat_list):
            dict_corr["key"].append(k + " / " + feat)
            a2 = combined_df
            for d in range(len(req_list)):
                req = req_list[d]
                if req["greater_than"]:
                    a2 = a2[a2[req["col_name"]] > req["val"]]
                elif req["greater_than"] == 0:
                    a2 = a2[a2[req["col_name"]] < req["val"]]
            if feat_nonzero:
                a2 = a2[a2[feat] > 0]
            a3 = a2
            if survey_nonzero:
                a3 = a2[a2[k] > 0]
            if len(a3.dropna()) < 3:
                c = [0, 1]
            else:
                a3 = a3.dropna()
                c = pearsonr(a3[k], a3[feat])
            dict_corr["corr"].append(c[0])
            dict_corr["p-val"].append(c[1])
            if len(survey_list) >= len(feat_list) and i > j:
                corrected_p_vals["row_col"].append((i, j))
                corrected_p_vals["pval"].append(c[1])
            if len(survey_list) < len(feat_list) and j > i:
                corrected_p_vals["row_col"].append((i, j))
                corrected_p_vals["pval"].append(c[1])
            dict_corr['N'].append(len(a3))
            mat[i,j] = c[0]
            str0 = ""
            if show_num:
                str0 = f"{c[0]:.3f}"
            p0.append(str0)
        pvals.append(np.array(p0))

    corrected_p_vals["pval"] = multipletests(list(corrected_p_vals["pval"]), alpha=alpha, method='fdr_bh')[1]
    pvals2 = []
    for i in range(len(pvals)):
        p0 = []
        for j in range(len(pvals[0])):
            str0 = pvals[i][j]
            if i == j:
                str0 += "*"
            else:
                if len(survey_list) >= len(feat_list) and i > j:
                    idx = corrected_p_vals["row_col"].index((i, j))
                elif len(survey_list) < len(feat_list) and j > i:
                    idx = corrected_p_vals["row_col"].index((i, j))
                else:
                    idx = corrected_p_vals["row_col"].index((j, i))
                if list(corrected_p_vals["pval"])[idx] < alpha:
                    str0 += "*"
            p0.append(str0)
        pvals2.append(p0)
    return mat, pvals2, pd.DataFrame(dict_corr)

def make_corr_plot(mat, pvals, survey_list, feat_list, title="",):
    """ Create a correlation plot.

        Args:
            mat: the matrix of correlations
            pvals: the significance strings
            survey_list: the list of survey names
            feat_list: the list of feature names
            title: what to title the plot
    """
    fig, axes = plt.subplots(figsize=(20,20))
    axes = sns.heatmap(axes=axes, data=mat, vmax=0.5, vmin=-0.5, annot=pvals, fmt='', square=False)
    if len(feat_list) < 10:
        axes.set_xticklabels(feat_list)
    plt.xticks(rotation=90)
    if len(survey_list) < 10:
        axes.set_yticklabels(survey_list)
    plt.yticks(rotation=45)
    plt.title(title)
    return fig
