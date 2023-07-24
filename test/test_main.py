import requests
from coclico import main
from pathlib import Path
import pandas as pd
from typing import List, Callable
import numpy as np
import shutil
from collections import Counter
import pytest


remote_url = "https://raw.githubusercontent.com/IGNF/coclico-data/main/"
local_path = Path("./data/")

files = [
    "test1/niv1/tile_splitted_2818_32247.laz",
    "test1/niv1/tile_splitted_2818_32248.laz",
    "test1/niv1/tile_splitted_2819_32247.laz",
    "test1/niv1/tile_splitted_2819_32248.laz",
    "test1/niv2/tile_splitted_2818_32247.laz",
    "test1/niv2/tile_splitted_2818_32248.laz",
    "test1/niv2/tile_splitted_2819_32247.laz",
    "test1/niv2/tile_splitted_2819_32248.laz",
    "test1/niv3/tile_splitted_2818_32247.laz",
    "test1/niv3/tile_splitted_2818_32248.laz",
    "test1/niv3/tile_splitted_2819_32247.laz",
    "test1/niv3/tile_splitted_2819_32248.laz",
    "test1/niv4/tile_splitted_2818_32247.laz",
    "test1/niv4/tile_splitted_2818_32248.laz",
    "test1/niv4/tile_splitted_2819_32247.laz",
    "test1/niv4/tile_splitted_2819_32248.laz",
    "test1/ref/tile_splitted_2818_32247.laz",
    "test1/ref/tile_splitted_2818_32248.laz",
    "test1/ref/tile_splitted_2819_32247.laz",
    "test1/ref/tile_splitted_2819_32248.laz",
]


def download_file(remote_file: Path, local_file: Path):
    response = requests.get(str(remote_file), verify=True, allow_redirects=True)
    with open(local_file, "wb") as fout:
        fout.write(response.content)


def download_data():
    test1 = Path("./data/test1")  
    [(test1 / sub_dir).mkdir(parents=True, exist_ok=True) for sub_dir in ["ref", "niv1", "niv2", "niv3", "niv4"] ]

    for file in files:
        local_file = local_path / file
        if not local_file.exists():
            download_file(remote_url + file, local_file)


def setup_module():
    tmp_path = Path("./tmp")
    if tmp_path.is_dir():
        shutil.rmtree(tmp_path)
    
    if not (Path("./data").is_dir()):
        download_data()


def check_df_exists_with_no_empty_data(f: Path) -> pd.DataFrame:
    """Check if a file exists, open it as a pandas dataframe to check that it has no empty data
    Returns the dataframe for potential further investigation

    Args:
        f (Path): path to input csv file

    Returns:
        pd.DataFrame: read dataframe
    """
    assert (f).is_file()
    df = pd.read_csv(f)
    assert not df.isnull().values.any()
    return df


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


def test_compute_metric_intrisic_mpap0_test1():
    las_file = Path("./data/test1/niv1/tile_splitted_2818_32247.laz")
    counter = main.compute_metric_intrisic_mpap0(las_file, class_weights={0: 1, 1: 1, 2: 0, 6: 2})
    print(counter)
    assert counter == Counter({1: 543, 6: 4743})


@pytest.mark.skip(reason="Not implemented yet")
def test_compute_metric_relative_mpap0_toy():
    count_c1 = Counter({1: 12, 2: 20})
    count_ref = Counter({1: 10, 2: 20})
    score = main.compute_metric_relative_mpap0(count_c1, count_ref)
    assert score == Counter({1: 0.2, 2: 0})
    # Inconnue : et si on a pas de points ref: division par 0 !


def test_compare_one_tile_mpap0_test1():
    ci = Path("./data/test1/niv1/")
    ref = Path("./data/test1/ref/")
    out = Path("./tmp/test1/compare_one_tile/niv1/mpap0")
    out.mkdir(parents=True)
    tile_stem = "tile_splitted_2818_32247"
    tile_fn = f"{tile_stem}.laz"
    out_fn = f"{tile_stem}.csv"
    class_weights = {0: 1, 1: 2}
    main.compare_one_tile_mpap0(ci, ref, out, tile_fn, metric_name="mpap0_test", class_weights=class_weights)
    df = check_df_exists_with_no_empty_data(out / out_fn)
    assert set(df.columns) == set(["tile", "class", "mpap0_test"])
    assert set(df["tile"]) == set([tile_stem])


def test_compare_to_ref_test1():
    c1 = Path("./data/test1/niv1/")
    ref = Path("./data/test1/ref/")
    out = Path("./tmp/test1/niv1/compare_to_ref.csv")
    metrics_weights = {"metric1": {0: 1, 1: 2}, "metric2": {0: 1, 1: 2}}
    out.parent.mkdir(parents=True, exist_ok=True)
    nb_classes = 2
    tiles = [f.stem for f in ref.iterdir() if f.name.lower().endswith(("las", "laz"))]

    main.compare_to_ref(c1, ref, out, metrics_weights)
    df = check_df_exists_with_no_empty_data(out)
    assert set(df.columns) == set(["tile", "class"] + [k for k in metrics_weights.keys()])
    assert set(df["tile"]) == set(tiles)
    assert len(df.index) == nb_classes * len(tiles)


def test_merge_stats_toy():
    metrics = ["m1", "m2", "m3"]
    stats = ["mean", "std", "median", "min", "max"]
    classes = [0, 1]
    stats_c1_df = compute_toy_stats_result(stats, metrics, classes, (lambda ii: 2 * ii))
    stats_c2_df = compute_toy_stats_result(stats, metrics, classes, (lambda ii: 3 * ii))
    out = Path("./tmp/toy_results/merge_stats.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    main.merge_stats([stats_c1_df, stats_c2_df], out)
    df = check_df_exists_with_no_empty_data(out)
    assert set(df.columns) == set(["statistic", "metric", "class", "result_0", "result_1"])
    assert len(df.index) == len(metrics) * len(stats) * len(classes)
    assert not np.all(df["result_0"] == 0)
    assert not np.all(df["result_1"] == 0)
    assert set(df["metric"]) == set(metrics)
    assert set(df["statistic"]) == set(stats)
    assert set(df["class"]) == set(classes)


def test_compute_weighted_result_toy():
    weights = {"m1": {0: 1, 1: 0}, "m2": {0: 2}, "m3": {0: 3, 1: 3}}
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
    df = check_df_exists_with_no_empty_data(out)
    assert set(df.columns) == set(["statistic", "result_0", "result_1"])
    assert set(df["statistic"]) == set(stats)
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


def test_compare_test1():
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = Path("./tmp/test1/compare")

    main.compare(c1, c2, ref, out)

    result_by_tile_c1_file = out / "c1" / "result_by_tile.csv"
    check_df_exists_with_no_empty_data(result_by_tile_c1_file)
    result_by_tile_c2_file = out / "c2" / "result_by_tile.csv"
    check_df_exists_with_no_empty_data(result_by_tile_c2_file)
    result_by_metric_file = out / "result_by_metric.csv"
    check_df_exists_with_no_empty_data(result_by_metric_file)
    result_file = out / "result.csv"
    check_df_exists_with_no_empty_data(result_file)
