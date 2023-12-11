import shutil
from pathlib import Path

import pandas as pd
import pytest

from coclico.mpla0.mpla0 import MPLA0

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/mpla0")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def generate_metric_dataframes():
    # Cases:
    # - tile a: more than 1000 points
    # - tile b: less than 1000 points
    input_df = pd.DataFrame(
        {
            "tile": ["a", "a", "a", "a", "b", "b", "b", "b", "b"],
            "class": ["6", "0", "1", "2_3", "6", "0", "1", "2_3", "7"],
            "ref_pixel_count": [1000, 1000, 1000, 1000, 500, 500, 500, 500, 500],
            "union": [100, 100, 100, 100, 100, 100, 100, 200, 200],
            "intersection": [100, 95, 90, 85, 95, 80, 40, 100, 50],
        }
    )

    expected_out = pd.DataFrame(
        {
            "tile": ["a", "a", "a", "a", "b", "b", "b", "b", "b"],
            "class": ["6", "0", "1", "2_3", "6", "0", "1", "2_3", "7"],
            "mpla0": [1, 0.5, 0, 0, 1, 1, 0.5, 0, 0],
        }
    )

    return input_df, expected_out


def test_compute_note():
    input_df, expected_out = generate_metric_dataframes()
    out_df = MPLA0.compute_note(input_df)
    assert out_df.equals(expected_out)
