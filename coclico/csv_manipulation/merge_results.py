import argparse
from coclico._version import __version__
from gpao.job import Job
from gpao.project import Project
from gpao_utils.utils_store import Store
import json
import logging
import pandas as pd
from pathlib import Path, PurePosixPath
from typing import Dict, List


def compute_stats(results_file: Path) -> pd.DataFrame:
    """Compute statistics over tiles from raw result file

    Args:
        results_file (Path): path of the file containing individual tiles results
    Returns:
        pd.DataFrame: statistics
    """
    df = pd.read_csv(results_file, dtype={"class": str})
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
    df = stats_dfs[0]
    df.rename(columns={"result": "result_0"}, inplace=True)
    for ii, df_to_join in enumerate(stats_dfs[1:]):
        df = df.merge(df_to_join, on=["statistic", "class", "metric"], validate="1:1", how="left")
        # rename result column with index to know which is which
        df.rename(columns={"result": f"result_{ii+1}"}, inplace=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)


def compute_weighted_result(stats_df: pd.DataFrame, weights: Dict) -> pd.DataFrame:
    """Compute weighted sum of notes for all metrics using the weights stored in a dictionary like:
        weights = {
            "metric1": {
                "class0": 1,
                "class1": 2
            },
            "metric2": {
                "class0": 0,
                "class1": 3
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
        for metric in weights.keys():
            for cl in weights[metric].keys():
                val = group[(group["metric"] == metric) & (group["class"] == cl)]["result"]
                if len(val.index) != 1:
                    logging.warning(f"Raise exception for group: {group}")
                    logging.warning(type(cl))
                    raise ValueError(
                        f"No or several values found for statistic={group['statistic'].iloc[0]}, "
                        + f"class={cl}, metric={metric}. ({val.values})"
                    )
                res += weights[metric][cl] * val.values[0]

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
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)


def create_merge_all_results_project(
    result_by_tile_c1_in: Path,
    result_by_tile_c2_in: Path,
    result_by_metric_out: Path,
    result_out: Path,
    store: Store,
    metrics_weights: Dict,
    project_name: str,
) -> Project:
    command = f"""
    docker run -t --rm --userns=host --shm-size=2gb
    -v {store.to_unix(result_by_tile_c1_in.parent)}:/input_c1
    -v {store.to_unix(result_by_tile_c2_in.parent)}:/input_c2
    -v {store.to_unix(result_by_metric_out.parent)}:/out_metric
    -v {store.to_unix(result_out.parent)}:/out
    ignimagelidar/coclico:{__version__}
    python -m coclico.csv_manipulation.merge_results
    --result_by_tile_c1_in {PurePosixPath("/input_c1") / result_by_tile_c1_in.name}
    --result_by_tile_c2_in {PurePosixPath("/input_c2") / result_by_tile_c2_in.name}
    --result_by_metric_out {PurePosixPath("/out_metric") / result_by_metric_out.name}
    --result_out {PurePosixPath("/out") / result_out.name}
    --metric_weights '{json.dumps(metrics_weights)}'
    """
    job = Job("merge_all_results", command, tags=["docker"])
    project = Project(project_name, [job])

    return project


def merge_all_results(
    result_by_tile_c1_in: Path,
    result_by_tile_c2_in: Path,
    result_by_metric_out: Path,
    result_out: Path,
    metrics_weights: Dict,
):
    result_by_metric_out.parent.mkdir(parents=True, exist_ok=True)
    result_out.parent.mkdir(parents=True, exist_ok=True)
    stats_c1 = compute_stats(result_by_tile_c1_in)
    result_c1 = compute_weighted_result(stats_c1, metrics_weights)

    stats_c2 = compute_stats(result_by_tile_c2_in)
    result_c2 = compute_weighted_result(stats_c2, metrics_weights)

    merge_stats([stats_c1, stats_c2], result_by_metric_out)
    merge_weighted_results([result_c1, result_c2], result_out)


def parse_args():
    parser = argparse.ArgumentParser("Run mpap0 metric on one tile")
    parser.add_argument(
        "--result_by_tile_c1_in",
        type=Path,
        help="Path to the folder containing the tile-by-tile result csv for one classification",
    )
    parser.add_argument(
        "--result_by_tile_c2_in",
        type=Path,
        help="Path to the folder containing the tile-by-tile result csv for another classification",
    )
    parser.add_argument("--result_by_metric_out", type=Path, help="Path to the file to save the metric-by-metric csv")
    parser.add_argument("--result_out", type=Path, help="Path to the file to save the global weighted result")
    parser.add_argument("--metric_weights", type=json.loads, help="Dictionary of the metrics weights")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    merge_all_results(
        args.result_by_tile_c1_in,
        args.result_by_tile_c2_in,
        args.result_by_metric_out,
        args.result_out,
        args.metric_weights,
    )
