""" Module for code to create correlation plots """
import os
import time
import logging
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
import LAMP
from ..primary.survey_scores import survey_scores
from statsmodels.stats.multitest import multipletests
logging.getLogger('seaborn').setLevel(level=logging.WARNING)
logging.getLogger('matplotlib').setLevel(level=logging.WARNING)
import seaborn as sns
import matplotlib.pyplot as plt


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
        for i in times:
            ret["timestamp"].append(i)
            for val in np.unique([val["question"] for val in values]):
                curr = [j["score"] for j in surveys if (j["question"] == val) & (j["start"] == i)]
                if len(curr) == 0:
                    curr = None
                else:
                    curr = sum(curr) / len(curr)
                ret[val].append(curr)
        if len(pd.DataFrame(ret)) > 0:
            pd.DataFrame(ret).to_csv(survey_path + part_id + "_" + cat + ".csv")

def get_avg_var_data(parts, scoring_guide, other_global_feats, other_local_feats,
                     other_local_subfeats, passive_feats, survey_dir, passive_dir,
                     avg = 1, time_to_include=[-1, -1]):
    """ Get variance and averages for each feature.

        Args:
            parts: the list of participant ids
            scoring_guide: the scoring dicctionary
            other_global_feats: the list of other global features
            other_local_feats: the list of other local features
            other_local_subfeats: the list of subfeatures
            passive_feats: the list of passive features
            survey_dir: The survey directory (also holds other local / global features)
            passive_dir: The passive data directory
            avg: whether to do average (1) or variance (0)
            time_to_inlude (units: ms): Whether to include the entire time or
                restrict to certain days from the start of the
                study (ie first SensorEvent)
                (ex: time_to_include=[86400000,691200000] would be from day 2 to day 8)
        Notes: See example in correlation_plots.ipynb
    """
    # Make sure that the feature order stays consistent
    all_survey_keys = []
    for val in scoring_guide["category_list"]:
        all_survey_keys += [val]
        all_survey_keys += [k for k in scoring_guide["questions"].keys()
            if ("map_to" not in scoring_guide["questions"][k]) and
               (scoring_guide["questions"][k]["category"] == val)]
    all_other_local_keys = []
    for val in other_local_feats:
        all_other_local_keys += [y for y in other_local_subfeats[val]]
    if avg:
        feat_order = all_survey_keys + other_global_feats + all_other_local_keys + passive_feats
    else:
        feat_order = all_survey_keys + all_other_local_keys + passive_feats
    avg_df0 = []
    for part in parts:
        end_time = time.time() * 1000
        start_time = 0
        if time_to_include[0] != -1:
            start_time = LAMP.SensorEvent.all_by_participant(part,
                                                             _limit=-1)["data"]
            if len(start_time) > 0 and "timestamp" in start_time[0]:
                start_time = start_time[0]["timestamp"] + time_to_include[0]
            else:
                continue
        if time_to_include[1] != -1:
            end_time = start_time + time_to_include[1]
        dict0 = {}
        dict0["part_id"] = part
        for feat in feat_order:
            dict0[feat] = None
        # surveys
        for survey_name in scoring_guide["category_list"]:
            survey_path = survey_dir + part + "_" + survey_name + ".csv"
            if os.path.exists(survey_path):
                df0 = pd.read_csv(survey_path)
                df0 = df0[(df0["timestamp"] >= start_time) & (df0["timestamp"] <= end_time)]
                df0 = df0[[k for k in df0.keys() if (k != "timestamp") & (k != "Unnamed: 0")]]
                for k in df0:
                    if avg:
                        dict0[k] = list(df0[[k]].mean())[0]
                    else:
                        dict0[k] = list(df0[[k]].var())[0]
        # global features
        if avg:
            other_global_path = survey_path = survey_dir + part + "_other_global_feats.csv"
            if os.path.exists(other_global_path):
                df0 = pd.read_csv(other_global_path)
                df0 = df0[[k for k in df0.keys() if (k != "Unnamed: 0") &
                                                    (k in other_global_feats)]]
                for k in df0:
                    dict0[k] = list(df0[k])[0]
        # local features
        for other_feat in other_local_feats:
            feat_path = survey_dir + part + "_" + other_feat + ".csv"
            if os.path.exists(feat_path):
                df0 = pd.read_csv(feat_path)
                df0 = df0[(df0["timestamp"] >= start_time) & (df0["timestamp"] <= end_time)]
                df0 = df0[other_local_subfeats[other_feat]]
                for k in df0:
                    if avg:
                        dict0[k] = list(df0[[k]].mean())[0]
                    else:
                        dict0[k] = list(df0[[k]].var())[0]
        # passive features
        for feat in passive_feats:
            feat_path = passive_dir + part + "_" + feat + ".pkl"
            if os.path.exists(feat_path):
                df0 = pd.read_pickle(feat_path)
                df0["timestamp"] = df0["timestamp"].astype(np.int64) // 10**6
                df0 = df0[(df0["timestamp"] >= start_time) & (df0["timestamp"] <= end_time)]
                if "value" in df0:
                    df0 = df0.rename(columns={"value": feat})
                df0 = df0[[feat]]
                df0 = df0[df0[feat] > 0]
                for k in df0:
                    if avg:
                        dict0[k] = list(df0[[k]].mean())[0]
                    else:
                        dict0[k] = list(df0[[k]].var())[0]
        avg_df0.append(dict0)
    avg_df0 = pd.DataFrame(avg_df0)
    return avg_df0

def get_corr(combined_df0, survey_list, feat_list, req_list=[],
             alpha=0.05, show_num=1):
    """ Function to get correlations.

        Args:
            combined_df0: df0 with all of your features
            survey_list: list of survey names
            feat_list: list of features
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
        temp_p_vals = []
        for j, feat in enumerate(feat_list):
            dict_corr["key"].append(k + " / " + feat)
            df_feats = combined_df0
            for req in req_list:
                if req["greater_than"]:
                    df_feats = df_feats[df_feats[req["col_name"]] > req["val"]]
                elif req["greater_than"] == 0:
                    df_feats = df_feats[df_feats[req["col_name"]] < req["val"]]
            if (len(df_feats.dropna()) < 3 or
                df_feats.dropna()[k].var() == 0 or
                df_feats.dropna()[feat].var() == 0):
                corr = [0, 1]
            else:
                corr = pearsonr(df_feats.dropna()[k], df_feats.dropna()[feat])
            dict_corr["corr"].append(corr[0])
            dict_corr["p-val"].append(corr[1])
            if ((k, feat) not in corrected_p_vals["row_col"] and
                (feat, k) not in corrected_p_vals["row_col"]):
                corrected_p_vals["row_col"].append((k, feat))
                corrected_p_vals["pval"].append(corr[1])
            dict_corr['N'].append(len(df_feats.dropna()))
            mat[i, j] = corr[0]
            str0 = ""
            if show_num:
                str0 = f"{corr[0]:.3f}"
            temp_p_vals.append(str0)
        pvals.append(np.array(temp_p_vals))

    corrected_p_vals["pval"] = multipletests(list(corrected_p_vals["pval"]),
                                             alpha=alpha,
                                             method='fdr_bh')[1]
    pvals2 = []
    for i, k in enumerate(survey_list):
        temp_p_vals = []
        for j, feat in enumerate(feat_list):
            str0 = pvals[i][j]
            if i == j:
                str0 += "*"
            else:
                if (k, feat) in corrected_p_vals["row_col"]:
                    idx = corrected_p_vals["row_col"].index((k, feat))
                elif (feat, k) in corrected_p_vals["row_col"]:
                    idx = corrected_p_vals["row_col"].index((feat, k))
                if list(corrected_p_vals["pval"])[idx] < alpha:
                    str0 += "*"
            temp_p_vals.append(str0)
        pvals2.append(temp_p_vals)
    return mat, pvals2, pd.DataFrame(dict_corr)

def make_corr_plot(mat, pvals, survey_list, feat_list, title=""):
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

# Model specific functions
def produce_improvement_df0(parts,
                            feature_name,
                            amount_change,
                            feat_dir_0,
                            fn_0,
                            min_num_records=2,
                            min_starting_score=0,
                            min_time_diff=0):
    """ Function to produce improvement dataframes.

        Args:
            parts: the list of participnat ids
            feature_name: name of the feature to use for comparison. Cannot be a global feature.
            amount_change: min amount that the feature must change by (start - end)
            min_num_records: minimum number of records to include. Must have at least 2 to compare
            min_starting_score: only consider people with at least this starting score
            min_time_diff: only consider if the start / end features are this far apart

            feat_dir_0: the path to the features
            fn_0: the name of the feature file (feature_name.csv or feature_name.pkl)
                the full feature file is participantID_featurename.csv, and "participantID_"
                will be appended to the fn_0
        Returns:
            Dataframe with part_id, improved, change columns. Participants
                that do not meet criteria will have improved = None
    """
    # Get the improvement for each person
    improvement_df0_0 = {"part_id": [], "improved": [], "change": []}
    for part in parts:
        feat_path = feat_dir_0 + part + "_" + fn_0
        improvement_df0_0["part_id"].append(part)
        improved = None
        change = None
        if os.path.exists(feat_path):
            if feat_path[-1] == "l":
                df0 = pd.read_pickle(feat_path)
            else:
                df0 = pd.read_csv(feat_path)
            if (len(df0) >= min_num_records and
                df0.loc[len(df0) - 1, feature_name] >= min_starting_score):
                if df0.loc[0, "timestamp"] - df0.loc[len(df0) - 1, "timestamp"] >= min_time_diff:
                    diff = df0.loc[len(df0) - 1, feature_name] - df0.loc[0, feature_name]
                    improved = (df0.loc[len(df0) - 1, feature_name] - df0.loc[0, feature_name]
                                > amount_change)
                    if 0 < amount_change < 1 and improved == 1:
                        improved = diff / df0.loc[len(df0) - 1, feature_name] > amount_change
                    change = df0.loc[len(df0) - 1, feature_name] - df0.loc[0, feature_name]
        improvement_df0_0["improved"].append(improved)
        improvement_df0_0["change"].append(change)

    return pd.DataFrame(improvement_df0_0)
