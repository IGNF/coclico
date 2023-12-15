import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import coclico.io as io
from coclico.malt0.malt0 import MALT0

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/malt0")
CONFIG_FILE_METRICS = Path("./test/configs/config_test_metrics.yaml")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def generate_metric_dataframes():
    # Cases:
    # - tile a: Test with mean condition only
    # - tile b: Test with standard deviation condition only
    # - tile c: Test with maximum condition only
    # - tile d: Test all conditions together
    input_tile_a = pd.DataFrame(
        {
            "tile": ["a"] * 3,
            "class": ["6", "0", "2_3"],
            "max_diff": [0, 0, 0],
            "mean_diff": [0.01, 0.5, 0.01 + (0.5 - 0.01) / 2],
            "std_diff": [0, 0, 0],
        }
    )
    expected_tile_a = pd.DataFrame({"tile": ["a"] * 3, "class": ["6", "0", "2_3"], "malt0": [1, 3 / 5, 4 / 5]})

    input_tile_b = pd.DataFrame(
        {
            "tile": ["b"] * 4,
            "class": ["6", "0", "2_3", "4"],
            "max_diff": [0, 0, 0, 0],
            "mean_diff": [0, 0, 0, 0],
            "std_diff": [0.01, 0.5, 0.01 + (0.5 - 0.01) / 2, np.nan],
        }
    )
    expected_tile_b = pd.DataFrame(
        {"tile": ["b"] * 4, "class": ["6", "0", "2_3", "4"], "malt0": [1, 3 / 5, 4 / 5, np.nan]}
    )

    input_tile_c = pd.DataFrame(
        {
            "tile": ["c"] * 3,
            "class": ["6", "0", "2_3"],
            "max_diff": [0.1, 4, 0.1 + (4 - 0.1) / 2],
            "mean_diff": [0, 0, 0],
            "std_diff": [0, 0, 0],
        }
    )

    expected_tile_c = pd.DataFrame({"tile": ["c"] * 3, "class": ["6", "0", "2_3"], "malt0": [1, 4 / 5, 4.5 / 5]})

    input_tile_d = pd.DataFrame(
        {
            "tile": ["d"] * 3,
            "class": ["6", "0", "2_3"],
            "max_diff": [0.09, 4.0001, 0.1 + (4 - 0.1) / 2],
            "mean_diff": [0.01, 0.5, 0.01 + (0.5 - 0.01) / 2],
            "std_diff": [0.01, 0.5, 0.01 + (0.5 - 0.01) / 2],
        }
    )

    expected_tile_d = pd.DataFrame({"tile": ["d"] * 3, "class": ["6", "0", "2_3"], "malt0": [1, 0, 0.5]})

    input_df = pd.concat([input_tile_a, input_tile_b, input_tile_c, input_tile_d])
    expected_out = pd.concat([expected_tile_a, expected_tile_b, expected_tile_c, expected_tile_d])

    return input_df, expected_out


def test_compute_note():
    input_df, expected_out = generate_metric_dataframes()
    notes_config = io.read_config_file(CONFIG_FILE_METRICS)["malt0"]["notes"]
    out_df = MALT0.compute_note(input_df, notes_config)
    assert out_df.equals(expected_out)
