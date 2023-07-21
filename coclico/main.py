from pathlib import Path
import logging
import pandas as pd
from typing import List, Dict
from collections import Counter
import pdal


def compute_metric_intrisic_mpap0(las_file: Path, class_weights: Dict) -> Counter:
    """Count points on las file ()

    Args:
        las_file (Path): _description_

    Returns:
        Counter: _description_
    """
    # TODO: replace with function imported from pdaltools
    # (pdaltools.count_occurences.count_occurences_for_attribute import compute_count_one_file)
    # not done yet as this module is not accessible from outside the library
    pipeline = pdal.Reader.las(str(las_file))
    pipeline |= pdal.Filter.stats(dimensions="Classification", count="Classification")
    pipeline.execute()
    raw_counts = pipeline.metadata["metadata"]["filters.stats"]["statistic"][0]["counts"]
    split_counts = [c.split("/") for c in raw_counts]

    points_counts = Counter({str(int(float(value))): int(count) for value, count in split_counts})
    # get results only for classes that are in weights dictionary
    out_counts = Counter({int(k): v for k, v in points_counts.items() if class_weights.get(int(k), 0) > 0})

    return out_counts


def compute_metric_relative_mpap0(pts_counts_ci, pts_counts_ref):
    logging.warning("Not implemented yet")
    diff_points_counts = Counter({0: 0.2, 1: 0.1})

    return diff_points_counts


def compute_note_mpap0(score):
    logging.warning("Not implemented yet")
    note = Counter({0: 0, 1: 1})
    return note


def compare_one_tile_mpap0(
    ci: Path, ref: Path, out: Path, tile_fn: str, class_weights: Dict, metric_name: str = "mpap0"
):
    logging.debug(f"Compare Ci: {ci} to Ref: {ref} in out {out} for metric MPAP0")
    tile_stem = Path(tile_fn).stem
    out_file = out / (tile_stem + ".csv")
    points_counts_ci = compute_metric_intrisic_mpap0(ci / tile_fn, class_weights)
    points_counts_ref = compute_metric_intrisic_mpap0(ref / tile_fn, class_weights)

    score = compute_metric_relative_mpap0(points_counts_ci, points_counts_ref)
    note = compute_note_mpap0(score)
    data = [{"tile": tile_stem, "class": cl, metric_name: note[cl]} for cl in class_weights.keys()]
    df = pd.DataFrame(data)
    df.to_csv(out_file, index=False)


def compare_to_ref(ci: Path, ref: Path, out: Path, metric_weights: Dict):
    logging.debug(f"Compare Ci: {ci} to Ref: {ref} in out {out}")
    out_dir = out.parent
    metrics = {"metric1": compare_one_tile_mpap0, "metric2": compare_one_tile_mpap0}
    tiles_filenames = [f.name for f in ref.iterdir() if f.name.lower().endswith(("las", "laz"))]
    merged_df = pd.DataFrame(columns=["tile", "class"])
    for metric_name, metric_fn in metrics.items():
        if metric_name in metric_weights.keys():
            metric_out = out_dir / metric_name
            # exist_ok = false in order to force working from clean directory
            # to make sure that the concatenation is done only on the expected csv files
            metric_out.mkdir(parents=True, exist_ok=False)

            for tile_fn in tiles_filenames:
                metric_fn(
                    ci, ref, metric_out, tile_fn, class_weights=metric_weights[metric_name], metric_name=metric_name
                )

            metric_df = pd.concat([pd.read_csv(f) for f in metric_out.iterdir() if f.name.endswith("csv")])
            merged_df = merged_df.merge(metric_df, on=["tile", "class"], how="right")

    merged_df.to_csv(out, index=False)


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
                    raise ValueError(
                        f"No or several values found for statistic={group['statistic'].iloc[0]}, "
                        + "class={cl}, metric={metric}. ({val.values})"
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
    result_by_tile_c1_file = out / "c1" / "result_by_tile.csv"
    result_by_tile_c2_file = out / "c2" / "result_by_tile.csv"
    result_by_metric_file = out / "result_by_metric.csv"
    result_file = out / "result.csv"
    metrics_weights = {"metric1": {0: 1, 1: 2}, "metric2": {0: 1, 1: 0}}
    out.mkdir(parents=True, exist_ok=True)

    compare_to_ref(c1, ref, result_by_tile_c1_file, metrics_weights)
    stats_c1 = compute_stats(result_by_tile_c1_file)
    result_c1 = compute_weighted_result(stats_c1, metrics_weights)

    compare_to_ref(c2, ref, result_by_tile_c2_file, metrics_weights)
    stats_c2 = compute_stats(result_by_tile_c2_file)
    result_c2 = compute_weighted_result(stats_c2, metrics_weights)

    merge_stats([stats_c1, stats_c2], result_by_metric_file)
    merge_weighted_results([result_c1, result_c2], result_file)
