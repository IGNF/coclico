from pathlib import Path
import logging
import pandas as pd
from typing import List, Dict


def compare_to_ref(ci: Path, ref: Path, out: Path):
    logging.debug(f"Compare Ci: {ci} to Ref: {ref} in out {out}")
    df = pd.DataFrame(
        [
            {"tile": "tile0", "class": 0, "metric1": 0, "metric2": 1},
            {"tile": "tile0", "class": 1, "metric1": 2, "metric2": 3},
            {"tile": "tile1", "class": 0, "metric1": 4, "metric2": 5},
            {"tile": "tile1", "class": 1, "metric1": 6, "metric2": 7},
        ]
    )
    df.to_csv(out, index=False)


def compute_stats(results_file: Path) -> pd.DataFrame:
    """Compute statistics over tiles from raw result file

    Args:
        results_file (Path): path of the file containing individual tiles results
    Returns:
        pd.DataFrame: statistics
    """
    df = pd.read_csv(results_file)
    df.drop("tile", axis=1, inplace=True)
    df_means = df.groupby(["class"]).mean()
    df_means.reset_index(inplace=True)  # force "class" to be a 'normal' column
    df_means.insert(0, "statistic", "mean")  # insert statistic as first column
    df_mins = df.groupby(["class"]).min()
    df_mins.reset_index(inplace=True)
    df_mins["statistic"] = "min"
    df_maxs = df.groupby(["class"]).max()
    df_maxs.reset_index(inplace=True)
    df_maxs["statistic"] = "max"
    df_medians = df.groupby(["class"]).median()
    df_medians.reset_index(inplace=True)
    df_medians["statistic"] = "median"
    df_stds = df.groupby(["class"]).std()
    df_stds.reset_index(inplace=True)
    df_stds["statistic"] = "std"

    stats_df = pd.concat([df_means, df_mins, df_maxs, df_medians, df_stds], ignore_index=True)
    # convert dataframe with cols {stats, class, m1, m2, m3}
    # into dataframe with cols {stats, class, metric, result}
    ids = set(["statistic", "class"])
    metrics = set(stats_df.columns) - ids
    stats_df = pd.melt(stats_df, id_vars=ids, value_vars=metrics, var_name="metric", value_name="result")

    return stats_df


def merge_stats(stats_dfs: List[pd.DataFrame], out: Path):
    """Merge statistics from several classifications

    Args:
        stats_dfs (List[pd.DataFrame]): dataframe containing statistics for a single classification
        compared to a reference
        out (Path): output csv file
    """
    # logging.debug("stats_dfs")
    # logging.debug(stats_dfs)
    df = stats_dfs[0]
    df.rename(columns={"result": "result_0"}, inplace=True)
    for ii, df_to_join in enumerate(stats_dfs[1:]):
        df = df.merge(df_to_join, on=["statistic", "class", "metric"], validate="1:1", how="left")
        # rename result column with index to know which is which
        df.rename(columns={"result": f"result_{ii+1}"}, inplace=True)
    df.to_csv(out, index=False)


def compute_weighted_result(stats_df: pd.DataFrame, weights: Dict) -> pd.DataFrame:
    """Compute weighted sum of notes for all metrics using the weights stored in a dictionary like:
        weights = {
            "class_0": {
                "metric1": 1,
                "metric2": 2
            },
            "class_1": {
                "metric1": 0,
                "metric2": 3
            }
        }

    Args:
        stats_df (pd.DataFrame): dataframe containing statistics for a classification
        weights (Dict): weights to apply to the different metrics to generate the aggregated result

    Returns:
        pd.Dataframe: pandas Dataframe containing the weighted value for each statistic
    """

    def compute_weighted_sum(group):
        res = 0
        logging.debug(group)

        for cl in weights.keys():
            for metric in weights[cl].keys():
                val = group[(group["metric"] == metric) & (group["class"] == cl)]["result"]
                if len(val.index) != 1:
                    raise ValueError(
                        f"No or several values found for statistic={group['statistic'].iloc[0]}, "
                        + "class={cl}, metric={metric}. ({val.values})"
                    )

                res += weights[cl][metric] * val.values[0]

        return res

    weighted_results = stats_df.groupby("statistic").apply(compute_weighted_sum)
    weighted_results.name = "result"
    weighted_results = weighted_results.to_frame()
    weighted_results.reset_index(inplace=True)

    return weighted_results


def merge_weighted_results(weighted_results: List[pd.Series], out: Path):
    df = weighted_results[0]
    df.rename(columns={"result": "result_0"}, inplace=True)
    for ii, df_to_join in enumerate(weighted_results[1:]):
        df = df.merge(df_to_join, on=["statistic"], validate="1:1", how="left")
        # rename result column with index to know which is which
        df.rename(columns={"result": f"result_{ii+1}"}, inplace=True)
    df.to_csv(out, index=False)


def compare(c1: Path, c2: Path, ref: Path, out: Path):
    """Main function to compare 2 classification (c1, c2) with respect to a reference
    classification (ref) and save it as json files in out.
    This funcion works on folders containing las files.

    Args:
        c1 (Path): path to the folder containing c1 classified point clouds
        c2 (Path): path to the folder containing c2 classified point clouds
        ref (Path): path to the folder containing the reference classified point clouds
        out (Path): output path for the json outputs
    """
    logging.debug(f"Compare C1: {c1} to Ref: {ref} AND C2:{c2} to {ref} in out {out}")
    result_by_tile_c1_file = out / "result_by_tile_c1.csv"
    result_by_tile_c2_file = out / "result_by_tile_c2.csv"
    result_by_metric_file = out / "result_by_metric.csv"
    result_file = out / "result.csv"
    metrics_weights = {0: {"metric1": 1, "metric2": 2}, 1: {"metric1": 0, "metric2": 3}}
    out.mkdir(parents=True, exist_ok=True)

    compare_to_ref(c1, ref, result_by_tile_c1_file)
    stats_c1 = compute_stats(result_by_tile_c1_file)
    result_c1 = compute_weighted_result(stats_c1, metrics_weights)

    compare_to_ref(c2, ref, result_by_tile_c2_file)
    stats_c2 = compute_stats(result_by_tile_c2_file)
    result_c2 = compute_weighted_result(stats_c2, metrics_weights)

    merge_stats([stats_c1, stats_c2], result_by_metric_file)
    merge_weighted_results([result_c1, result_c2], result_file)
