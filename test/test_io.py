from pathlib import Path

import pytest

import coclico.io as io
from coclico.metrics.listing import METRICS


def test_read_config_file_ok():
    config_file = Path("./test/configs/config_test_main.yaml")
    weights = io.read_config_file(config_file)
    assert all([k in METRICS.keys() for k in weights.keys()])
    for _, val in weights.items():
        assert isinstance(val, dict)
        assert "weights" in val.keys()
        assert all([isinstance(cl, str) for cl in val["weights"].keys()])


def test_read_config_file_fail():
    config_file = Path("./test/configs/config_test_read_fail.yaml")
    with pytest.raises(ValueError):
        io.read_config_file(config_file)
