import coclico.csv_manipulation.merge_results
from gpao_utils.utils_store import Store
import json
import numpy as np
import operator as op
import pandas as pd
from pathlib import Path
import shutil
import subprocess as sp
from test.utils import check_df_exists_with_no_empty_data
from typing import Callable, List


TMP_PATH = Path("./tmp/csv_merging/merge_results")


def setup_module():
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def compute_toy_stats_result(
    stats: List[str] = ["mean", "median"],
    metrics: List[str] = ["metric1", "metric2"],
    classes: List[str] = [0, 1],
    results_fn: Callable = (lambda ii: ii),
) -> pd.DataFrame:
    """Generate a pandas dataframe containing fake statistics results for provided stats,
    metrics, classes using results_fn to generate the result for each [stat, metric, class]
    This method aims to mimick coclico.main.compute_stats results

    Args:
        stats (List[str], optional): stats names for which to generate results. Defaults to ["mean", "median"].
        metrics (List[str], optional): metric names for which to generate results. Defaults to ["metric1", "metric2"].
        classes (List[str], optional): classes names for which to generate results. Defaults to ["0", "1"].
        results_fn (_type_, optional): function to use to generate values from the creation index.
        Defaults to (lambda ii: ii).

    Returns:
        pd.DataFrame: output dataframe
    """
    results_list = []
    ii = 0
    for stat in stats:
        for cl in classes:
            for m in metrics:
                result_dict = {"statistic": stat, "class": cl, "metric": m, "result": results_fn(ii)}
                ii += 1
                results_list.append(result_dict)

    df = pd.DataFrame(results_list)

    return df


def test_merge_stats_toy():
    metrics = ["m1", "m2", "m3"]
    stats = ["mean", "std", "median", "min", "max"]
    classes = ["0", "1"]
    stats_c1_df = compute_toy_stats_result(stats, metrics, classes, (lambda ii: 2 * ii))
    stats_c2_df = compute_toy_stats_result(stats, metrics, classes, (lambda ii: 3 * ii))
    out = TMP_PATH / Path("toy_results/merge_stats.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    coclico.csv_manipulation.merge_results.merge_stats([stats_c1_df, stats_c2_df], out)
    df = check_df_exists_with_no_empty_data(out)
    assert set(df.columns) == set(["statistic", "metric", "class", "result_0", "result_1"])
    assert len(df.index) == len(metrics) * len(stats) * len(classes)
    assert not np.all(df["result_0"] == 0)
    assert not np.all(df["result_1"] == 0)
    assert set(df["metric"]) == set(metrics)
    assert set(df["statistic"]) == set(stats)
    assert set(df["class"]) == set(classes)


def test_compute_weighted_result_toy():
    weights = {"m1": {"0": 1, "1": 0}, "m2": {"0": 2}, "m3": {"0": 3, "1": 3}}
    metrics = ["m1", "m2", "m3"]
    stats = ["mean", "std", "median", "min", "max"]
    classes = ["0", "1"]
    stats_df = compute_toy_stats_result(stats, metrics, classes, (lambda ii: 2 * ii))
    result_df = coclico.csv_manipulation.merge_results.compute_weighted_result(stats_df, weights)
    assert set(result_df.columns) == set(["statistic", "result"])
    assert set(result_df["statistic"]) == set(stats)
    assert not result_df.isnull().values.any()


def compute_toy_weighted_result(
    stats: List[str] = ["mean", "median"],
    results_fn: Callable = (lambda ii: ii),
) -> pd.DataFrame:
    """Generate a pandas series containing fake weigthed results for provided stats using results_fn
    to generate the result for each stat
    This method aims to mimick coclico.main.compute_weighted_result results

    Args:
        stats (List[str], optional): stats names for which to generate results. Defaults to ["mean", "median"].
        results_fn (_type_, optional): function to use to generate values from the creation index.
        Defaults to (lambda ii: ii).

    Returns:
        pd.DataFrame: output dataframe
    """
    result_list = [{"statistic": s, "result": results_fn(ii)} for ii, s in enumerate(stats)]
    df = pd.DataFrame(result_list)

    return df


def test_merge_weighted_results_toy():
    out = TMP_PATH / Path("toy_results/merge_weighted_results.csv")
    out.parent.mkdir(parents=True, exist_ok=True)

    stats = ["median", "mean", "std"]
    res_0 = compute_toy_weighted_result(stats, lambda ii: 2 * ii)
    res_1 = compute_toy_weighted_result(stats, lambda ii: 3 * ii)

    coclico.csv_manipulation.merge_results.merge_weighted_results([res_0, res_1], out)
    df = check_df_exists_with_no_empty_data(out)
    assert set(df.columns) == set(["statistic", "result_0", "result_1"])
    assert set(df["statistic"]) == set(stats)
    assert not np.all(df["result_0"] == 0)
    assert not np.all(df["result_1"] == 0)


def compute_toy_by_tile_merged_result(
    out: Path,
    tiles: List[str] = ["tile1", "tile2"],
    metrics: List[str] = ["metric1", "metric2"],
    classes: List[str] = [0, 1],
    results_fn: Callable = (lambda ii: ii),
):
    """Generate a toy csv file containing fake tile by tile results for provided tiles, metrics, classes
    using results_fn to generate the result for each [tile, metric, class] from its creation index
    This method aims to mimick coclico.main.compare_to_ref results

    Args:
        out (Path): path to the output csv file
        tiles (List[str], optional): tiles names for which to generate results. Defaults to ["tile1", "tile2"].
        metrics (List[str], optional): metrics for which to generate results. Defaults to ["metric1", "metric2"].
        classes (List[str], optional): classes for which to generate results. Defaults to ["0", "1"].
        results_fn (_type_, optional): function to use to generate values from the creation index.
        Defaults to (lambda ii: ii).
    """
    results_list = []
    ii = 0
    for tile in tiles:
        for cl in classes:
            result_dict = {"tile": tile, "class": cl}
            for m in metrics:
                result_dict[m] = results_fn(ii)
                ii += 1
            results_list.append(result_dict)

    df = pd.DataFrame(results_list)
    df.to_csv(out, index=False)


def test_compute_stats_toy():
    metrics = ["m1", "m2", "m3"]
    stats = ["mean", "std", "median", "min", "max"]
    classes = [0, 1]
    base_path = TMP_PATH / Path("toy_results/")
    base_path.mkdir(parents=True, exist_ok=True)
    result_c1 = base_path / "results_by_tile_c1.csv"
    compute_toy_by_tile_merged_result(
        result_c1, ["tile1", "tile2", "tile3", "tile4"], metrics, classes, (lambda ii: 2 * ii)
    )
    df = coclico.csv_manipulation.merge_results.compute_stats(result_c1)

    assert set(df.columns) == set(["statistic", "metric", "class", "result"])
    assert set(df.statistic) == set(stats)
    assert set(df.metric) == set(metrics)
    assert len(df.index) == len(metrics) * len(classes) * len(stats)
    assert not df.isnull().values.any()

    for s in stats:
        assert not (np.all(df.result[df.statistic == s] == 0))


def test_merge_all_results_toy():
    metrics = ["m1", "m2", "m3"]
    classes = [0, 1]
    weights = {"m1": {"0": 1, "1": 0}, "m2": {"0": 2}, "m3": {"0": 3, "1": 3}}
    base_path = TMP_PATH / Path("merge_toy_results/")
    base_path.mkdir(parents=True)
    result_c1 = base_path / "results_by_tile_c1.csv"
    compute_toy_by_tile_merged_result(
        result_c1, ["tile1", "tile2", "tile3", "tile4"], metrics, classes, (lambda ii: 2 * ii)
    )
    result_c2 = base_path / "results_by_tile_c2.csv"
    compute_toy_by_tile_merged_result(
        result_c2, ["tile1", "tile2", "tile3", "tile4"], metrics, classes, (lambda ii: 3 * ii)
    )
    result_by_metric = base_path / "results_by_metric.csv"
    result = base_path / "results.csv"

    coclico.csv_manipulation.merge_results.merge_all_results(result_c1, result_c2, result_by_metric, result, weights)
    check_df_exists_with_no_empty_data(result_by_metric)
    check_df_exists_with_no_empty_data(result)


def test_merge_all_results_cli_toy():
    metrics = ["m1", "m2", "m3"]
    classes = [0, 1]
    weights = {"m1": {"0": 1, "1": 0}, "m2": {"0": 2}, "m3": {"0": 3, "1": 3}}
    base_path = TMP_PATH / Path("merge_cli_toy_results/")
    base_path.mkdir(parents=True)
    result_c1 = base_path / "results_by_tile_c1.csv"
    compute_toy_by_tile_merged_result(
        result_c1, ["tile1", "tile2", "tile3", "tile4"], metrics, classes, (lambda ii: 2 * ii)
    )
    result_c2 = base_path / "results_by_tile_c2.csv"
    compute_toy_by_tile_merged_result(
        result_c2, ["tile1", "tile2", "tile3", "tile4"], metrics, classes, (lambda ii: 3 * ii)
    )
    result_by_metric = base_path / "results_by_metric.csv"
    result = base_path / "results.csv"

    cmd = f"""python -m coclico.csv_manipulation.merge_results \
    --result_by_tile_c1_in {result_c1} \
    --result_by_tile_c2_in {result_c2} \
    --result_by_metric_out {result_by_metric} \
    --result_out {result} \
    --metric_weights '{json.dumps(weights)}'
    """

    sp.run(cmd, shell=True, check=True)
    check_df_exists_with_no_empty_data(result_by_metric)
    check_df_exists_with_no_empty_data(result)


def test_create_merge_all_results_project():
    weights = {"m1": {"0": 1, "1": 0}, "m2": {"0": 2}, "m3": {"0": 3, "1": 3}}
    result_c1 = Path("local_store/results_c1.csv")
    result_c2 = Path("local_store/results_c2.csv")
    result_by_metric = Path("local_store/results_by_metric.csv")
    result = Path("local_store/results.csv")
    store = Store("local_store", "win_store", "unix_store")
    project_name = "coclico_test_create_merge_all_results_project"

    project = coclico.csv_manipulation.merge_results.create_merge_all_results_project(
        result_c1, result_c2, result_by_metric, result, store, weights, project_name
    )
    project_json = json.loads(project.to_json())  # return a string
    assert project_json["name"] == project_name  # check that it is running the right method
    assert len(project_json["jobs"]) == 1
    # check that the right paths are provided to the unix store
    assert not op.contains(project_json["jobs"][0]["command"], "local_store")
    assert op.contains(project_json["jobs"][0]["command"], "unix_store")
