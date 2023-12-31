import json
import logging
import shutil
import subprocess as sp
from pathlib import Path

import pytest
from pdaltools.las_info import las_info_metadata

from coclico.mpla0 import mpla0_intrinsic

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/mpla0_intrinsic")
CONFIG_FILE_METRICS = Path("./test/configs/config_test_metrics.yaml")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_compute_metric_intrinsic(ensure_test1_data):
    las_file = Path("./data/test1/niv1/tile_splitted_2818_32247.laz")
    pixel_size = 0.5
    las_mtd = las_info_metadata(las_file)
    las_extent = (las_mtd["minx"], las_mtd["miny"], las_mtd["maxx"], las_mtd["maxy"])
    logging.debug(f"Test compute_metric_intrinsic on las with extent {las_extent}")

    output_tif = TMP_PATH / "unit_test_mpla0_intrinsic.tif"
    mpla0_intrinsic.compute_metric_intrinsic(las_file, CONFIG_FILE_METRICS, output_tif, pixel_size=pixel_size)

    assert output_tif.exists()


def test_run_main(ensure_test1_data):
    pixel_size = 0.5
    input_file = Path("./data/test1/ref/tile_splitted_2818_32247.laz")
    output_tif = TMP_PATH / "unit_test_run_main_mpla0_intrinsic.tif"
    cmd = f"""python -m coclico.mpla0.mpla0_intrinsic \
    --input-file {input_file} \
    --output-file {output_tif} \
    --config-file {CONFIG_FILE_METRICS} \
    --pixel-size {pixel_size}
    """
    sp.run(cmd, shell=True, check=True)

    logging.info(cmd)

    assert output_tif.exists()
