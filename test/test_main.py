import os
import requests
from coclico import main
from pathlib import Path
import pandas as pd
from typing import List, Callable
import numpy as np
import shutil


remote_url = "https://github.com/IGNF/coclico-data/blob/main/"
local_path = "./data/"

files = [
    "test0/ref/Semis_2021_0919_6424_LA93_IGN69.laz",
    "test0/niv1/Semis_2021_0919_6424_LA93_IGN69.laz",
    "test0/niv2/Semis_2021_0919_6424_LA93_IGN69.laz",
    "test0/niv3/Semis_2021_0919_6424_LA93_IGN69.laz",
    "test0/niv4/Semis_2021_0919_6424_LA93_IGN69.laz",
]


def download(remote_file, local_file):
    response = requests.get(remote_file, verify=True, allow_redirects=True)
    with open(local_file, "wb") as fout:
        fout.write(response.content)


def setup_module():
    tmp_path = Path("./tmp")
    if tmp_path.is_dir():
        shutil.rmtree(tmp_path)
    os.makedirs("./data/test0/ref/", exist_ok=True)
    os.makedirs("./data/test0/niv1/", exist_ok=True)
    os.makedirs("./data/test0/niv2/", exist_ok=True)
    os.makedirs("./data/test0/niv3/", exist_ok=True)
    os.makedirs("./data/test0/niv4/", exist_ok=True)

    for file in files:
        local_file = os.path.join(local_path, file)
        if not os.path.exists(local_file):
            download(os.path.join(remote_url, file), local_file)


def compute_toy_by_tile_result(
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


def test_compare_to_ref_test0():
    c1 = Path("./data/test0/niv1/")
    ref = Path("./data/test0/ref/")
    out = Path("./tmp/test0/compare_to_ref.csv")
    out.parent.mkdir(parents=True, exist_ok=True)

    main.compare_to_ref(c1, ref, out)

    assert out.is_file()
    df = pd.read_csv(out)
    assert set(df.columns) == set(["tile", "class", "metric1", "metric2"])
    assert len(df.index) > 0
    assert not df.isnull().values.any()


def test_merge_stats_toy():
    metrics = ["m1", "m2", "m3"]
    stats = ["mean", "std", "median", "min", "max"]
    classes = [0, 1]
    stats_c1_df = compute_toy_stats_result(stats, metrics, classes, (lambda ii: 2 * ii))
    stats_c2_df = compute_toy_stats_result(stats, metrics, classes, (lambda ii: 3 * ii))
    out = Path("./tmp/toy_results/merge_stats.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    main.merge_stats([stats_c1_df, stats_c2_df], out)
    assert out.is_file()
    df = pd.read_csv(out)
    assert set(df.columns) == set(["statistic", "metric", "class", "result_0", "result_1"])
    assert len(df.index) == len(metrics) * len(stats) * len(classes)
    assert not df.isnull().values.any()
    assert not np.all(df["result_0"] == 0)
    assert not np.all(df["result_1"] == 0)
    assert set(df["metric"]) == set(metrics)
    assert set(df["statistic"]) == set(stats)
    assert set(df["class"]) == set(classes)


def test_compute_weighted_result_toy():
    weights = {0: {"m1": 1, "m2": 2, "m3": 3}, 1: {"m1": 0, "m3": 3}}
    metrics = ["m1", "m2", "m3"]
    stats = ["mean", "std", "median", "min", "max"]
    classes = [0, 1]
    stats_df = compute_toy_stats_result(stats, metrics, classes, (lambda ii: 2 * ii))
    result_df = main.compute_weighted_result(stats_df, weights)
    assert set(result_df.columns) == set(["statistic", "result"])
    assert set(result_df["statistic"]) == set(stats)
    assert not result_df.isnull().values.any()


def test_merge_weighted_results_toy():
    out = Path("./tmp/toy_results/merge_weighted_results.csv")
    out.parent.mkdir(parents=True, exist_ok=True)

    stats = ["median", "mean", "std"]
    res_0 = compute_toy_weighted_result(stats, lambda ii: 2 * ii)
    res_1 = compute_toy_weighted_result(stats, lambda ii: 3 * ii)

    main.merge_weighted_results([res_0, res_1], out)
    assert out.is_file()
    df = pd.read_csv(out)
    assert set(df.columns) == set(["statistic", "result_0", "result_1"])
    assert set(df["statistic"]) == set(stats)
    assert not df.isnull().values.any()
    assert not np.all(df["result_0"] == 0)
    assert not np.all(df["result_1"] == 0)


def test_compute_stats_toy():
    metrics = ["m1", "m2", "m3"]
    stats = ["mean", "std", "median", "min", "max"]
    classes = [0, 1]
    base_path = Path("./tmp/toy_results/")
    base_path.mkdir(parents=True, exist_ok=True)
    result_c1 = base_path / "results_by_tile_c1.csv"
    compute_toy_by_tile_result(result_c1, ["tile1", "tile2", "tile3", "tile4"], metrics, classes, (lambda ii: 2 * ii))
    df = main.compute_stats(result_c1)

    assert set(df.columns) == set(["statistic", "metric", "class", "result"])
    assert set(df.statistic) == set(stats)
    assert set(df.metric) == set(metrics)
    assert len(df.index) == len(metrics) * len(classes) * len(stats)
    assert not df.isnull().values.any()

    for s in stats:
        assert not (np.all(df.result[df.statistic == s] == 0))


def test_compare_test0():
    c1 = Path("./data/test0/niv1/")
    c2 = Path("./data/test0/niv4/")
    ref = Path("./data/test0/ref/")
    out = Path("./tmp/test0/compare")

    main.compare(c1, c2, ref, out)

    result_by_tile_c1_file = out / "result_by_tile_c1.csv"
    assert (result_by_tile_c1_file).is_file()
    result_by_tile_c2_file = out / "result_by_tile_c2.csv"
    assert (result_by_tile_c2_file).is_file()
    result_by_metric_file = out / "result_by_metric.csv"
    assert (result_by_metric_file).is_file()
    result_file = out / "result.csv"
    assert (result_file).is_file()
