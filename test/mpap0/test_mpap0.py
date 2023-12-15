import shutil
from pathlib import Path

import pandas as pd
import pytest

import coclico.io as io
from coclico.mpap0.mpap0 import MPAP0

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/mpap0")
CONFIG_FILE_METRICS = Path("./test/configs/config_test_metrics.yaml")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def generate_metric_dataframes():
    # Cases:
    # - tile a: more than 1000 points
    # - tile b: less than 1000 points
    # - tile c: no points in reference
    input_df = pd.DataFrame(
        {
            "tile": ["a", "a", "a", "b", "b", "b", "b", "c", "c"],
            "class": ["0", "1", "2_3", "0", "1", "2", "3_4_5", "1", "2"],
            "absolute_diff": [0, 50, 300, 10, 60, 100, 500, 0, 40],
            "ref_count": [1000, 1000, 200, 0, 100, 200, 100, 0, 0],
        }
    )

    expected_out = pd.DataFrame(
        {
            "tile": ["a", "a", "a", "b", "b", "b", "b", "c", "c"],
            "class": ["0", "1", "2_3", "0", "1", "2", "3_4_5", "1", "2"],
            "mpap0": [1, 0.5, 0, 1, 0.5, 0, 0, 1, 0.75],
        }
    )

    return input_df, expected_out


def test_compute_note():
    input_df, expected_out = generate_metric_dataframes()
    notes_config = io.read_config_file(CONFIG_FILE_METRICS)["mpap0"]["notes"]
    out_df = MPAP0.compute_note(input_df, notes_config)
    assert out_df.equals(expected_out)
