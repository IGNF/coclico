import json
import shutil
import subprocess as sp
from pathlib import Path
from test.utils import check_df_exists_with_no_empty_data

import pandas as pd
import pytest
from gpao_utils.store import Store

import coclico.csv_manipulation.results_by_tile
from coclico.config import csv_separator

pytestmark = pytest.mark.docker


TMP_PATH = Path("./tmp/csv_merging/results_by_tile")
DATA_PATH = Path("./data/csv/c1")

TILES = [
    "tile_splitted_2818_32247",
    "tile_splitted_2818_32248",
    "tile_splitted_2819_32247",
    "tile_splitted_2819_32248",
]


def setup_module():
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_merge_results_for_one_classif():
    metrics_weights = {"mpap0": {"1": 0.5, "2": 0, "3_4_5": 4, "9": 1}}
    metrics = list(metrics_weights.keys())
    classes = list(metrics_weights["mpap0"].keys())

    base_path = TMP_PATH / "merge_results_for_one_classif"
    out = base_path / "result.csv"
    out_tile = base_path / "result_tile.csv"

    coclico.csv_manipulation.results_by_tile.merge_results_for_one_classif(DATA_PATH, out, metrics_weights)

    df = check_df_exists_with_no_empty_data(out)
    assert set(df.columns) == set(["class"] + metrics)
    assert len(df.index) == len(classes)

    df = check_df_exists_with_no_empty_data(out_tile)
    assert set(df.columns) == set(["tile", "class"] + metrics)
    assert len(df.index) == len(TILES) * len(classes)
    assert set(df["tile"]) == set(TILES)

    mpap0_score_class_9 = df["mpap0"][df.index[df["class"] == "9"][0]]
    assert mpap0_score_class_9 == 1  # score for class 9 is 1. Case: 0 point for classe 9 in c1 and ref.


def test_merge_results_for_one_classif_on_different_classes():
    """Check that the result file is created correctly when classes are not the same for all metrics"""
    metrics_weights = {
        "mpap0": {"1": 0.5, "2": 0, "3_4_5": 4, "9": 1},
        "mpla0": {"0": 1, "1": 1, "2": 0, "3_4_5": 1, "3 _ 4": 2},
    }
    metrics = list(metrics_weights.keys())
    classes = set([cl for metric_dict in metrics_weights.values() for cl in metric_dict.keys()])
    base_path = TMP_PATH / Path("results_by_tile_on_different_classes")
    out = base_path / "result.csv"
    out_tile = base_path / "result_tile.csv"

    coclico.csv_manipulation.results_by_tile.merge_results_for_one_classif(DATA_PATH, out, metrics_weights)

    assert out.is_file()
    df = pd.read_csv(out, dtype={"class": str}, sep=csv_separator)
    assert set(df.columns) == set(["class"] + metrics)
    assert len(df.index) == len(classes)
    assert all([not df[m].isnull().values.all() for m in metrics])  # check that no metric is completely empty

    assert out_tile.is_file()
    df = pd.read_csv(out_tile, dtype={"class": str}, sep=csv_separator)
    assert set(df.columns) == set(["tile", "class"] + metrics)
    assert len(df.index) == len(TILES) * len(classes)
    assert set(df["tile"]) == set(TILES)
    assert all([not df[m].isnull().values.all() for m in metrics])  # check that no metric is completely empty


def test_run_main():
    out = TMP_PATH / "run_main" / "result.csv"
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
