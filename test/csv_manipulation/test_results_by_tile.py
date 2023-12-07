import json
import shutil
import subprocess as sp
from pathlib import Path
from test.utils import check_df_exists_with_no_empty_data

# import pandas as pd
import pytest
from gpao_utils.store import Store

import coclico.csv_manipulation.results_by_tile

# from typing import Callable, List


# from coclico.config import csv_separator

pytestmark = pytest.mark.docker


TMP_PATH = Path("./tmp/csv_merging/results_by_tile")
DATA_PATH = Path("./data/csv/c1")


def setup_module():
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


# def generate_csv_result(
#     out: Path,
#     tiles: List[str] = ["tile1", "tile2"],
#     metrics: List[str] = ["metric1", "metric2"],
#     classes: List[str] = [0, 1],
#     results_fn: Callable = (lambda ii: ii),
# ):
#     """Generate a toy csv file containing fake tile by tile results for provided tiles, metrics, classes
#     using results_fn to generate the result for each [tile, metric, class] from its creation index
#     This method aims to mimick coclico.main.compare_to_ref results

#     Args:
#         out (Path): path to the output csv file
#         tiles (List[str], optional): tiles names for which to generate results. Defaults to ["tile1", "tile2"].
#         metrics (List[str], optional): metrics for which to generate results. Defaults to ["metric1", "metric2"].
#         classes (List[str], optional): classes for which to generate results. Defaults to ["0", "1"].
#         results_fn (_type_, optional): function to use to generate values from the creation index.
#         Defaults to (lambda ii: ii).
#     """
#     out.mkdir(parents=True, exist_ok=True)
#     for metric in metrics:
#         out_metric = out / metric / "to_ref"
#         out_metric.mkdir(parents=True)
#         ii = 0
#         results_list = []
#         for tile in tiles:
#             for cl in classes:
#                 result_dict = {"tile": tile, "class": cl}
#                 result_dict[metric] = results_fn(ii)
#                 ii += 1
#                 results_list.append(result_dict)

#         df = pd.DataFrame(results_list)
#         df.to_csv(out_metric / "result_tile.csv", index=False, sep=csv_separator)

#         results_list = []
#         for cl in classes:
#             result_dict = {"class": cl}
#             result_dict[metric] = results_fn(ii)
#             ii += 1
#             results_list.append(result_dict)

#         df = pd.DataFrame(results_list)
#         df.to_csv(out_metric / "result.csv", index=False, sep=csv_separator)


def test_merge_results_for_one_classif():
    metrics_weights = {"mpap0": {"1": 0.5, "2": 0, "3_4_5": 4, "9": 1}}
    metrics = list(metrics_weights.keys())
    classes = list(metrics_weights["mpap0"].keys())
    tiles = [
        "tile_splitted_2818_32247",
        "tile_splitted_2818_32248",
        "tile_splitted_2819_32247",
        "tile_splitted_2819_32248",
    ]

    base_path = DATA_PATH
    out = TMP_PATH / "result.csv"
    out_tile = TMP_PATH / "result_tile.csv"

    coclico.csv_manipulation.results_by_tile.merge_results_for_one_classif(base_path, out, metrics_weights)

    df = check_df_exists_with_no_empty_data(out)
    assert set(df.columns) == set(["class"] + metrics)
    assert len(df.index) == len(classes)

    df = check_df_exists_with_no_empty_data(out_tile)
    assert set(df.columns) == set(["tile", "class"] + metrics)
    assert len(df.index) == len(tiles) * len(classes)
    assert set(df["tile"]) == set(tiles)

    mpap0_score_class_9 = df["mpap0"][df.index[df["class"] == "9"][0]]
    assert mpap0_score_class_9 == 1  # score for class 9 is 1. Case: 0 point for classe 9 in c1 and ref.


# TODO comment out when we have more than one metric working again

# def test_merge_results_for_one_classif_on_different_classes():
#     """Check that the result file is created correctly when classes are not the same for all metrics"""
#     metrics = ["m1", "m2", "m3"]
#     classes = [0, 1, 2, 3]
#     tiles = ["tile1", "tile2"]
#     base_path = TMP_PATH / Path("toy_results/results_by_tile_on_different_classes")
#     out = base_path / "result.csv"
#     out_tile = base_path / "result_tile.csv"
#     generate_csv_result(base_path, tiles, ["m1", "m2"], [0, 1, 2], (lambda ii: 2 * ii))
#     generate_csv_result(base_path, tiles, ["m3"], [1, 2, 3], (lambda ii: 3 * ii))

#     coclico.csv_manipulation.results_by_tile.merge_results_for_one_classif(base_path, out)

#     assert out.is_file()
#     df = pd.read_csv(out, dtype={"class": str}, sep=csv_separator)
#     assert set(df.columns) == set(["class"] + metrics)
#     assert len(df.index) == len(classes)
#     assert all([not df[m].isnull().values.all() for m in metrics])  # check that no metric is completely empty

#     assert out_tile.is_file()
#     df = pd.read_csv(out_tile, dtype={"class": str}, sep=csv_separator)
#     assert set(df.columns) == set(["tile", "class"] + metrics)
#     assert len(df.index) == len(tiles) * len(classes)
#     assert set(df["tile"]) == set(tiles)
#     assert all([not df[m].isnull().values.all() for m in metrics])  # check that no metric is completely empty


def test_run_main():
    out = TMP_PATH / "result_by_tile.csv"
    metrics_weights = {"mpap0": {"0": 1, "2": 2, "3_4": 3}}  # , "mpla0": {"0": 1, "2": 2, "5": 3}}

    cmd = f"""python -m coclico.csv_manipulation.results_by_tile \
    --metrics-root-folder {DATA_PATH} \
    --output-path {out} \
    --metrics-weights '{json.dumps(metrics_weights)}'
    """

    sp.run(cmd, shell=True, check=True)


def test_create_job_merge_tile_results():
    out = Path("local_store/out")
    metrics_root_folder = Path("local_store/input")
    store = Store("local_store", "win_store", "unix_store")
    metrics_weights = {"mpap0": {"1": 0.5, "2": 0, "3_4_5": 4, "9": 1}}

    job = coclico.csv_manipulation.results_by_tile.create_job_merge_results(
        metrics_root_folder, out, store, metrics_weights
    )
    job_json = json.loads(job.to_json())  # return a string
    assert job_json["name"].startswith("merge_tiles")  # check that it is running the right method
