from coclico.mpap0 import mpap0_intrinsic

import json
import logging
import subprocess as sp
from pathlib import Path
import shutil
import pytest

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/mpap0")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_compute_metric_intrinsic(ensure_test1_data):
    las_file = Path("./data/test1/niv1/tile_splitted_2818_32247.laz")
    class_weights = dict(
        {
            "0": 1,
            "1": 1,
            "2": 0,  # simple classes
            "3-4-5": 1,  # composed class
            "3 - 4": 2,  # composed class with spaces
        }
    )
    output_json = TMP_PATH / "unit_test_mpap0_intrinsic.json"
    counter = mpap0_intrinsic.compute_metric_intrinsic(las_file, class_weights, output_json)

    assert output_json.exists()
    with open(output_json, "r") as openfile:
        counter = json.load(openfile)
        print(counter)
        assert counter == dict({"0": 0, "1": 543, "2": 103791, "3-4-5": 1625 + 3145 + 31074, "3 - 4": 1625 + 3145})


def test_run_main(ensure_test1_data):
    input_file = Path("./data/test1/ref/tile_splitted_2818_32247.laz")
    output_json = TMP_PATH / "unit_test_run_main_mpap0_intrinsic.json"
    class_weights = dict({"0": 1, "1": 1})
    cmd = f"""python -m coclico.mpap0.mpap0_intrinsic \
    --input_file {input_file} \
    --output_file {output_json} \
    --class_weights '{json.dumps(class_weights)}' \
    """
    sp.run(cmd, shell=True, check=True)

    logging.info(cmd)

    assert output_json.exists()
    with open(output_json, "r") as openfile:
        counter = json.load(openfile)
        print(counter)
        assert counter == dict({"0": 0, "1": 543})
