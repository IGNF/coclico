import shutil
from pathlib import Path

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
    raise NotImplementedError


def test_compute_note():
    input_df, expected_out = generate_metric_dataframes()
    notes_config = io.read_config_file(CONFIG_FILE_METRICS)["mobj0"]["notes"]
    out_df = MOBJ0.compute_note(input_df, notes_config)
    assert out_df.equals(expected_out)
