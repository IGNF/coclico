import json
import logging
import shutil
import subprocess as sp
from pathlib import Path

import pytest

from coclico.mpap0 import mpap0_intrinsic

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/mpap0_intrinsic")
CONFIG_FILE_METRICS = Path("./test/configs/config_test_metrics.yaml")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_compute_metric_intrinsic(ensure_test1_data):
    las_file = Path("./data/test1/niv1/tile_splitted_2818_32247.laz")

    output_json = TMP_PATH / "unit_test_mpap0_intrinsic.json"
    counter = mpap0_intrinsic.compute_metric_intrinsic(las_file, CONFIG_FILE_METRICS, output_json)

    assert output_json.exists()
    with open(output_json, "r") as openfile:
        counter = json.load(openfile)
        print(counter)
        assert counter == dict({"0": 0, "1": 543, "2": 103791, "3_4_5": 1625 + 3145 + 31074, "3_4": 1625 + 3145, "9":0})


def test_run_main(ensure_test1_data):
    input_file = Path("./data/test1/ref/tile_splitted_2818_32247.laz")
    output_json = TMP_PATH / "unit_test_run_main_mpap0_intrinsic.json"

    cmd = f"""python -m coclico.mpap0.mpap0_intrinsic \
    --input-file {input_file} \
    --output-file {output_json} \
    --config-file {CONFIG_FILE_METRICS} \
    """
    sp.run(cmd, shell=True, check=True)

    logging.info(cmd)

    assert output_json.exists()
    with open(output_json, "r") as openfile:
        counter = json.load(openfile)
        print(counter)
        assert counter == dict({"0": 0, "1": 543, "2": 103791, "3_4_5": 1625 + 3145 + 31074, "3_4": 1625 + 3145, "9":0})
