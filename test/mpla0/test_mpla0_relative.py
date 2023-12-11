import json
import logging
import shutil
import subprocess as sp
from pathlib import Path
from test import utils

import pandas as pd
import pytest
import rasterio

from coclico.config import csv_separator
from coclico.mpla0 import mpla0_relative

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/mpla0_relative")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_generate_sum_by_layer():
    raster_file = Path("./data/mpla0/c1/intrinsic/tile_splitted_2818_32247.tif")
    with rasterio.Env():
        with rasterio.open(raster_file) as f:
            raster = f.read()
    class_weights = dict(
        {
            "0": 1,
            "1": 1,
            "2": 0,  # simple classes
            "3_4_5": 1,  # composed class
            "3 _ 4": 2,  # composed class with spaces
        }
    )
    classes = sorted(class_weights.keys())
    print(classes)
    d = mpla0_relative.generate_sum_by_layer(raster, classes)

    assert d == {
        "0": 0,
        "1": 225,
        "2": 36173,
        "3 _ 4": 2353,
        "3_4_5": 10692,
    }


def test_compute_metric_relative():
    c1_dir = Path("./data/mpla0/c1/intrinsic")
    ref_dir = Path("./data/mpla0/ref/intrinsic")
    class_weights = dict(
        {
            "0": 1,
            "1": 1,
            "2": 0,  # simple classes
            "3_4_5": 1,  # composed class
            "3 _ 4": 2,  # composed class with spaces
        }
    )
    output_csv = TMP_PATH / "relative" / "result.csv"
    output_csv_tile = TMP_PATH / "relative" / "result_tile.csv"
    expected_cols = {"class", "ref_pixel_count", "intersection", "union"}

    mpla0_relative.compute_metric_relative(c1_dir, ref_dir, class_weights, output_csv, output_csv_tile)

    expected_rows = 2 * 5  # 2 files * 5 classes
    assert utils.csv_num_rows(output_csv_tile) == expected_rows

    df = pd.read_csv(output_csv_tile, sep=csv_separator)
    assert set(df.columns) == expected_cols | {"tile"}

    expected_rows = 5  # 5 classes
    assert utils.csv_num_rows(output_csv) == expected_rows

    df = pd.read_csv(output_csv, sep=csv_separator)
    assert set(df.columns) == expected_cols


def test_run_main():
    c1_dir = Path("./data/mpla0/c1/intrinsic")
    ref_dir = Path("./data/mpla0/ref/intrinsic")
    output_csv = TMP_PATH / "unit_test_run_main_mpla0_relative.csv"
    output_csv_tile = TMP_PATH / "unit_test_run_main_mpla0_relative_tile.csv"
    class_weights = dict({"1": 1, "2": 1})
    cmd = f"""python -m coclico.mpla0.mpla0_relative \
        --input-dir {c1_dir} \
        --ref-dir {ref_dir} \
        --class-weights '{json.dumps(class_weights)}' \
        --output-csv {output_csv} \
        --output-csv-tile {output_csv_tile} \
    """

    sp.run(cmd, shell=True, check=True)
    logging.info(cmd)

    expected_rows = 2 * 2  # 2 files * 2 classes
    assert utils.csv_num_rows(output_csv_tile) == expected_rows

    expected_rows = 2  # 2 classes
    assert utils.csv_num_rows(output_csv) == expected_rows
