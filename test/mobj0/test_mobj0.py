import shutil
from pathlib import Path

import pandas as pd
import pytest

import coclico.io as io
from coclico.mobj0.mobj0 import MOBJ0

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/mobj0")
CONFIG_FILE_METRICS = Path("./test/configs/config_test_metrics.yaml")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def generate_metric_dataframes():
    # Cases:
    # - tile a: more than 20 objects
    # - tile b: less than 20 objects
    input_df = pd.DataFrame(
        {
            "tile": ["a", "a", "a", "a", "a", "b", "b", "b", "b"],
            "class": ["6", "1", "9", "12", "3_4_5", "6", "1", "2", "9"],
            "ref_object_count": [20, 10, 0, 10, 19, 20, 90, 200, 100],
            "paired_count": [20, 0, 1, 0, 100, 20, 80, 100, 90],
            "not_paired_count": [0, 1, 2, 3, 4, 0, 20, 150, 10],
        }
    )

    expected_out = pd.DataFrame(
        {
            "tile": ["a", "a", "a", "a", "a", "b", "b", "b", "b"],
            "class": ["6", "1", "9", "12", "3_4_5", "6", "1", "2", "9"],
            "mobj0": [1, 3 / 4, 1 / 2, 1 / 4, 0, 1, 0, 0, 0.5],
        }
    )

    return input_df, expected_out


def test_compute_note():
    input_df, expected_out = generate_metric_dataframes()
    notes_config = io.read_config_file(CONFIG_FILE_METRICS)["mobj0"]["notes"]
    out_df = MOBJ0.compute_note(input_df, notes_config)

    assert out_df.equals(expected_out)
