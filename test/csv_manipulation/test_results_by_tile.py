import json
import shutil
import subprocess as sp
from pathlib import Path
from test.utils import basic_check_on_df

import pandas as pd
import pytest
from gpao_utils.store import Store

import coclico.csv_manipulation.results_by_tile
import coclico.io as io
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
    config_file = Path("./test/configs/config_test_results_by_tile_1_metric.yaml")
    config_dict = io.read_config_file(config_file)
    metrics = list(config_dict.keys())
    classes = list(config_dict["mpap0"]["weights"].keys())

    base_path = TMP_PATH / "merge_results_for_one_classif"
    out = base_path / "result.csv"
    out_tile = base_path / "result_tile.csv"

    coclico.csv_manipulation.results_by_tile.merge_results_for_one_classif(DATA_PATH, out, config_file)

    df = basic_check_on_df(out)
    assert set(df.columns) == set(["class"] + metrics)
    assert len(df.index) == len(classes)

    df = basic_check_on_df(out_tile)
    assert set(df.columns) == set(["tile", "class"] + metrics)
    assert len(df.index) == len(TILES) * len(classes)
    assert set(df["tile"]) == set(TILES)

    mpap0_score_class_9 = df["mpap0"][df.index[df["class"] == "9"][0]]
    assert mpap0_score_class_9 == 1  # score for class 9 is 1. Case: 0 point for classe 9 in c1 and ref.


def test_merge_results_for_one_classif_on_different_classes():
    """Check that the result file is created correctly when classes are not the same for all metrics"""
    config_file = Path("./test/configs/config_test_results_by_tile_several_metrics.yaml")
    config_dict = io.read_config_file(config_file)
    metrics = list(config_dict.keys())
    classes = set([cl for metric_dict in config_dict.values() for cl in metric_dict["weights"].keys()])
    base_path = TMP_PATH / Path("results_by_tile_on_different_classes")
    out = base_path / "result.csv"
    out_tile = base_path / "result_tile.csv"

    coclico.csv_manipulation.results_by_tile.merge_results_for_one_classif(DATA_PATH, out, config_file)

    assert out.is_file()
    df = pd.read_csv(out, dtype={"class": str}, sep=csv_separator)
    print(df.to_markdown())
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
    CONFIG_FILE = Path("./test/configs/config_test_results_by_tile_1_metric.yaml")

    cmd = f"""python -m coclico.csv_manipulation.results_by_tile \
    --metrics-root-folder {DATA_PATH} \
    --output-path {out} \
    --config-file {CONFIG_FILE}
    """

    sp.run(cmd, shell=True, check=True)


def test_create_job_merge_results():
    config_file = Path("./test/configs/config_test_compute_weighted_result.yaml")

    out = Path("local_store/out")
    metrics_root_folder = Path("local_store/input")
    store = Store("local_store", "win_store", "unix_store")

    job = coclico.csv_manipulation.results_by_tile.create_job_merge_results(
        metrics_root_folder, out, store, config_file
    )
    job_json = json.loads(job.to_json())  # return a string
    assert job_json["name"].startswith("merge_notes")  # check that it is running the right method
