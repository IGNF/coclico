import logging
import shutil
import subprocess as sp
from pathlib import Path
from test import utils

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
        {"1": 51, "6": 13, "9": 0},  # expected_ref_count
        {"1": 51, "6": 13, "9": 0},  # expected_paired_count
        {"1": 16, "6": 0, "9": 0},  # expected_not_paired_count
    ),
    # One test with niv4 data (missing buildings)
    (
        Path("./data/mobj0/niv4/intrinsic/tile_splitted_2818_32248.geojson"),  # c1_path
        {"1": 51, "6": 13, "9": 0},  # expected_ref_count
        {"1": 45, "6": 7, "9": 0},  # expected_paired_count
        {"1": 7, "6": 6, "9": 0},  # expected_not_paired_count
    ),
    # One test with empty data file
    (
        Path("./data/mobj0/empty.geojson"),  # c1_path
        {"1": 51, "6": 13, "9": 0},  # expected_ref_count
        {"1": 0, "6": 0, "9": 0},  # expected_paired_count
        {"1": 51, "6": 13, "9": 0},  # expected_not_paired_count
    ),
]


@pytest.mark.parametrize(
    "c1_file,expected_ref_count,expected_paired_count,expected_not_paired_count", paired_objects_params
)
def test_check_paired_objects(c1_file, expected_ref_count, expected_paired_count, expected_not_paired_count):
    ref_file = Path("./data/mobj0/ref/intrinsic/tile_splitted_2818_32248.geojson")
    config_dict = read_config_file(CONFIG_FILE_METRICS)
    classes = sorted(config_dict["mobj0"]["weights"].keys())
    ref_count, paired_count, not_paired_count = mobj0_relative.check_paired_objects(c1_file, ref_file, classes)
    assert ref_count == expected_ref_count
    assert paired_count == expected_paired_count
    assert not_paired_count == expected_not_paired_count


def test_check_paired_objects_empty_ref():
    ref_file = Path("./data/mobj0/empty.geojson")
    c1_file = Path("./data/mobj0/niv2/intrinsic/tile_splitted_2818_32248.geojson")
    config_dict = read_config_file(CONFIG_FILE_METRICS)
    classes = sorted(config_dict["mobj0"]["weights"].keys())
    ref_count, paired_count, not_paired_count = mobj0_relative.check_paired_objects(c1_file, ref_file, classes)
    assert ref_count == {"1": 0, "6": 0, "9": 0}
    assert paired_count == {"1": 0, "6": 0, "9": 0}
    assert not_paired_count == {"1": 67, "6": 13, "9": 0}


def test_compute_metric_relative():
    c1_dir = Path("./data/mobj0/niv4/intrinsic/")
    ref_dir = Path("./data/mobj0/ref/intrinsic/")
    output_csv = TMP_PATH / "relative" / "result.csv"
    output_csv_tile = TMP_PATH / "relative" / "result_tile.csv"
    expected_cols = {"class", "ref_object_count", "paired_count", "not_paired_count"}

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
    ref_count_9 = df["ref_object_count"][df.index[df["class"] == 9][0]]
    paired_count_9 = df["paired_count"][df.index[df["class"] == 9][0]]
    not_paired_count_9 = df["not_paired_count"][df.index[df["class"] == 9][0]]
    assert ref_count_9 == 0
    assert paired_count_9 == 0
    assert not_paired_count_9 == 0

    # Check result for class 6 (several objects in c1 and ref that are not detected the same)
    ref_count_6 = df["paired_count"][df.index[df["class"] == 6][0]]
    paired_count_6 = df["paired_count"][df.index[df["class"] == 6][0]]
    not_paired_count_6 = df["not_paired_count"][df.index[df["class"] == 6][0]]
    assert ref_count_6 > 0
    assert paired_count_6 > 0
    assert not_paired_count_6 > 0


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
