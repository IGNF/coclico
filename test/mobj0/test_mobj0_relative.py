import logging
import shutil
import subprocess as sp
from pathlib import Path
from test import utils

import geopandas as gpd
import pandas as pd
import pytest

from coclico.config import csv_separator
from coclico.io import read_config_file
from coclico.mobj0 import mobj0_relative

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/mobj0_relative")
CONFIG_FILE_METRICS = Path("./test/configs/config_test_metrics.yaml")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


paired_objects_params = [
    # One test with niv2 data (same objects but with different geometries)
    (
        Path("./data/mobj0/niv2/intrinsic/tile_splitted_2818_32248.geojson"),  # c1_path
        {"1": 51, "6": 13, "9": 0},  # expected_nb_paired
        {"1": 16, "6": 0, "9": 0},  # expected_nb_not_paired
    ),
    # One test with niv4 data (missing buildings)
    (
        Path("./data/mobj0/niv4/intrinsic/tile_splitted_2818_32248.geojson"),  # c1_path
        {"1": 45, "6": 7, "9": 0},  # expected_nb_paired
        {"1": 7, "6": 6, "9": 0},  # expected_nb_not_paired
    ),
]


@pytest.mark.parametrize("c1_file,expected_nb_paired,expected_nb_not_paired", paired_objects_params)
def test_check_paired_objects(c1_file, expected_nb_paired, expected_nb_not_paired):
    ref_file = Path("./data/mobj0/ref/intrinsic/tile_splitted_2818_32248.geojson")
    config_dict = read_config_file(CONFIG_FILE_METRICS)
    classes = sorted(config_dict["mobj0"]["weights"].keys())
    c1_geometries = gpd.read_file(c1_file)
    ref_geometries = gpd.read_file(ref_file)
    nb_paired, nb_not_paired = mobj0_relative.check_paired_objects(c1_geometries, ref_geometries, classes)

    assert nb_paired == expected_nb_paired
    assert nb_not_paired == expected_nb_not_paired


def test_compute_metric_relative():
    c1_dir = Path("./data/mobj0/niv4/intrinsic/")
    ref_dir = Path("./data/mobj0/ref/intrinsic/")
    output_csv = TMP_PATH / "relative" / "result.csv"
    output_csv_tile = TMP_PATH / "relative" / "result_tile.csv"
    expected_cols = {"class", "nb_paired", "nb_not_paired"}

    mobj0_relative.compute_metric_relative(c1_dir, ref_dir, CONFIG_FILE_METRICS, output_csv, output_csv_tile)

    expected_rows = 4 * 3  # 4 files * 3 classes
    assert utils.csv_num_rows(output_csv_tile) == expected_rows
    df = pd.read_csv(output_csv_tile, sep=csv_separator)
    assert set(df.columns) == expected_cols | {"tile"}

    expected_rows = 3  # 3 classes
    assert utils.csv_num_rows(output_csv) == expected_rows

    df = pd.read_csv(output_csv, sep=csv_separator)
    assert set(df.columns) == expected_cols

    # Check result for class 9 (0 points in c1 and ref)
    nb_paired_9 = df["nb_paired"][df.index[df["class"] == 9][0]]
    nb_not_paired_9 = df["nb_not_paired"][df.index[df["class"] == 9][0]]
    assert nb_paired_9 == 0
    assert nb_not_paired_9 == 0

    # Check result for class 6 (several objects in c1 and ref that are not detected the same)
    nb_paired_6 = df["nb_paired"][df.index[df["class"] == 6][0]]
    nb_not_paired_6 = df["nb_not_paired"][df.index[df["class"] == 6][0]]
    assert nb_paired_6 > 0
    assert nb_not_paired_6 > 0


def test_run_main():
    c1_dir = Path("./data/mobj0/niv2/intrinsic")
    ref_dir = Path("./data/mobj0/ref/intrinsic")
    output_csv = TMP_PATH / "unit_test_run_main_mobj0_relative.csv"
    output_csv_tile = TMP_PATH / "unit_test_run_main_mobj0_relative_tile.csv"
    cmd = f"""python -m coclico.mobj0.mobj0_relative \
        --input-dir {c1_dir} \
        --ref-dir {ref_dir} \
        --config-file {CONFIG_FILE_METRICS} \
        --output-csv {output_csv} \
        --output-csv-tile {output_csv_tile} \
    """

    sp.run(cmd, shell=True, check=True)
    logging.info(cmd)

    expected_rows = 4 * 3  # 4 files * 3 classes
    assert utils.csv_num_rows(output_csv_tile) == expected_rows

    expected_rows = 3  # 3 classes
    assert utils.csv_num_rows(output_csv) == expected_rows
