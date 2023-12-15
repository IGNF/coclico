from pathlib import Path

import pytest

import coclico.io as io
from coclico.metrics.listing import METRICS


def test_read_metrics_weights_ok():
    weights_file = Path("./test/configs/metrics_weights_test.yaml")
    weights = io.read_metrics_weights(weights_file)
    assert all([k in METRICS.keys() for k in weights.keys()])
    for _, val in weights.items():
        assert isinstance(val, dict)
        assert "weights" in val.keys()
        assert all([isinstance(cl, str) for cl in val["weights"].keys()])


def test_read_metrics_weights_fail():
    weights_file = Path("./test/configs/metrics_weights_fail.yaml")
    with pytest.raises(ValueError):
        io.read_metrics_weights(weights_file)
