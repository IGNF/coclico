import shutil
from pathlib import Path

import pytest

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/mobj0_relative")
CONFIG_FILE_METRICS = Path("./test/configs/config_test_metrics.yaml")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_compute_metric_relative(ensure_mobj0_data):
    raise NotImplementedError


def test_run_main(ensure_mobj0_data):
    raise NotImplementedError
