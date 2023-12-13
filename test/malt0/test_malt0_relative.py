import json
import logging
import shutil
import subprocess as sp
from pathlib import Path
from test import utils

import numpy as np
import pandas as pd
import pytest

from coclico.config import csv_separator
from coclico.malt0 import malt0_relative

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/malt0_relative")
CONFIG_FILE_METRICS = Path("./test/configs/config_test_metrics.yaml")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_compute_stats_single_raster():
    layer1 = np.array([[0, 0, 2], [1, 1, 2], [2, 2, 10]])
    layer2 = np.array([[0, 0, 0], [1, 1, 1], [15, 3, 4]])
    raster = np.stack([layer1, layer2], axis=0)
    occupancy1 = np.array(([0, 0, 0], [1, 1, 1], [1, 1, 0]))
    occupancy2 = np.array(([0, 1, 1], [0, 1, 1], [0, 1, 1]))
    occupancy = np.stack([occupancy1, occupancy2], axis=0)

    out = malt0_relative.compute_stats_single_raster(raster, occupancy)
    max_val, count, mean_val, std_val, m2 = out

    expected_count = [5, 6]
    expected_m2 = np.array(
        [2 * 0.6**2 + 3 * 0.4**2, (2 * (-1.5) ** 2 + 2 * 0.5**2 + 1 * 1.5**2 + 1 * 2.5**2)]
    )
    expected_mean = np.array([8, 9]) / expected_count  # [1.6, 1.5]
    assert np.allclose(max_val, [2, 4])
    assert np.allclose(count, expected_count)
    assert np.allclose(mean_val, expected_mean)
    assert np.allclose(std_val**2, expected_m2 / expected_count)
    assert np.allclose(m2, expected_m2)


def test_update_overall_stats():
    nb_classes = 3
    raster1 = np.array(np.arange(nb_classes * 4 * 5)).reshape((nb_classes, 4, 5))
    raster2 = raster1.copy()
    raster3 = raster1.copy()
    occupancy1 = raster1 % 3 != 0
    occupancy2 = raster2 % 2 != 0
    occupancy3 = raster3 > 0
    rasters = [raster1, raster2, raster3]
    occupancies = [occupancy1, occupancy2, occupancy3]

    # Generate stats using the composed process: get stats from each raster +
    # update overall stats
    overall_max = np.zeros(nb_classes)
    overall_count = np.zeros(nb_classes)
    overall_mean = np.zeros(nb_classes)
    overall_m2 = np.zeros(nb_classes)

    for raster, occupancy in zip(rasters, occupancies):
        local_max, local_count, local_mean, _, local_m2 = malt0_relative.compute_stats_single_raster(raster, occupancy)
        overall_max, overall_count, overall_mean, overall_m2 = malt0_relative.update_overall_stats(
            local_max, overall_max, local_count, overall_count, local_mean, overall_mean, local_m2, overall_m2
        )

    overall_std = np.sqrt(overall_m2 / overall_count)

    # Generate result with the expected equivalent behaviour : concatenate rasters
    # and get stats on the concatenated raster

    raster = np.concatenate(rasters, axis=1)
    occupancy = np.concatenate(occupancies, axis=1)
    expected_max, expected_count, expected_mean, expected_std, _ = malt0_relative.compute_stats_single_raster(
        raster, occupancy
    )

    assert np.allclose(overall_max, expected_max)
    assert np.allclose(overall_count, expected_count)
    assert np.allclose(overall_mean, expected_mean)
    assert np.allclose(overall_std, expected_std)
    # no check on m2 as it is only meant to be an intermediate value that has no meaning by itself and
    # is ok as long as std is the same between the 2 methods


def test_compute_metric_relative(ensure_malt0_data):
    c1_dir = Path("./data/malt0/c1/intrinsic/mnx")
    ref_dir = Path("./data/malt0/ref/intrinsic/mnx")
    occupancy_dir = Path("./data/malt0/ref/intrinsic/occupancy")
    output_csv = TMP_PATH / "relative" / "result.csv"
    output_csv_tile = TMP_PATH / "relative" / "result_tile.csv"
    expected_cols = {"class", "max_diff", "mean_diff", "std_diff"}

    malt0_relative.compute_metric_relative(c1_dir, ref_dir, occupancy_dir, CONFIG_FILE_METRICS, output_csv, output_csv_tile)

    df = pd.read_csv(output_csv_tile, sep=csv_separator)
    assert set(df.columns) == expected_cols | {"tile"}

    expected_rows = 2 * 5  # 2 files * 5 classes
    assert utils.csv_num_rows(output_csv_tile) == expected_rows

    df = pd.read_csv(output_csv, sep=csv_separator)
    assert set(df.columns) == expected_cols

    expected_rows = 5  # 5 classes
    assert utils.csv_num_rows(output_csv) == expected_rows

    df = pd.read_csv(output_csv, sep=csv_separator)
    logging.debug(df.to_markdown())


def test_run_main(ensure_malt0_data):
    c1_dir = Path("./data/malt0/c1/intrinsic/mnx")
    ref_dir = Path("./data/malt0/ref/intrinsic/mnx")
    occ_dir = Path("./data/malt0/ref/intrinsic/occupancy")
    output_csv = TMP_PATH / "unit_test_run_main_mpla0_relative.csv"
    output_csv_tile = TMP_PATH / "unit_test_run_main_mpla0_relative_tile.csv"

    cmd = f"""python -m coclico.malt0.malt0_relative \
        --input-dir {c1_dir} \
        --ref-dir {ref_dir} \
        --occupancy-dir {occ_dir} \
        --config-file '{CONFIG_FILE_METRICS}' \
        --output-csv {output_csv} \
        --output-csv-tile {output_csv_tile} \
    """

    sp.run(cmd, shell=True, check=True)
    logging.info(cmd)

    expected_rows = 5 * 2  # 2 files * 2 classes
    assert utils.csv_num_rows(output_csv_tile) == expected_rows

    expected_rows = 5  # 2 classes
    assert utils.csv_num_rows(output_csv) == expected_rows
