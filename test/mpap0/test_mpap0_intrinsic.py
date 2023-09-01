from test.mpap0.test_mpap0 import TMP_PATH


import json
import logging
import subprocess as sp
from pathlib import Path


def test_run_mpap0_intrinsic_cli(ensure_test1_data):
    input_file = Path("./data/test1/ref/tile_splitted_2818_32247.laz")
    output_json = TMP_PATH / Path("unit_test_run_mpap0_intrinsic_cli.json")
    class_weights = dict({"0": 1, "1": 1})
    cmd = f"""python -m coclico.mpap0.mpap0_intrinsic \
    --input_file {input_file} \
    --output_file {output_json} \
    --class_weights '{json.dumps(class_weights)}' \
    """
    sp.run(cmd, shell=True, check=True)
    logging.info(cmd)
