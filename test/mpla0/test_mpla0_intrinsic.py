from coclico.mpla0 import mpla0_intrinsic

import json
import logging
import numpy as np
import subprocess as sp
from pathlib import Path
import shutil
import pytest
import rasterio
from pdaltools.las_info import las_info_metadata

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/mpla0")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_compute_metric_intrinsic(ensure_test1_data):
    las_file = Path("./data/test1/niv1/tile_splitted_2818_32247.laz")
    pixel_size = 0.5
    las_mtd = las_info_metadata(las_file)
    las_extent = (las_mtd["minx"], las_mtd["miny"], las_mtd["maxx"], las_mtd["maxy"])
    logging.debug(f"Test compute_metric_intrinsic on las with extent {las_extent}")
    class_weights = dict(
        {
            "0": 1,
            "1": 1,
            "2": 0,  # simple classes
            "3_4_5": 1,  # composed class
            "3 _ 4": 2,  # composed class with spaces
        }
    )
    output_tif = TMP_PATH / "unit_test_mpla0_intrinsic.tif"
    mpla0_intrinsic.compute_metric_intrinsic(las_file, class_weights, output_tif, pixel_size=pixel_size)

    assert output_tif.exists()
    with rasterio.Env():
        with rasterio.open(output_tif) as f:
            output_data = f.read()
            output_bounds = f.bounds

    # check that las extent is comprised inside tif extent but tif has no border pixels
    assert (output_bounds.left < las_extent[0]) and (output_bounds.left > las_extent[0] - pixel_size)  # x_min
    assert (output_bounds.right > las_extent[2]) and (output_bounds.right < las_extent[2] + pixel_size)  # x_max
    assert (output_bounds.top > las_extent[3]) and (output_bounds.top < las_extent[3] + pixel_size)  # y_max
    assert (output_bounds.bottom < las_extent[1]) and (output_bounds.bottom > las_extent[1] - pixel_size)  # y_min

    assert output_data.shape[0] == len(class_weights.keys())
    # input las does not contain points with class 0 so output layer should contain only zeroes
    assert np.all(output_data[0, :, :] == 0)
    # all other classes have data, so their layers should not contain only zeroes
    for ii in range(1, len(class_weights.keys())):
        assert np.any(output_data[ii, :, :] == 1)


def test_run_main(ensure_test1_data):
    pixel_size = 0.5
    input_file = Path("./data/test1/ref/tile_splitted_2818_32247.laz")
    output_tif = TMP_PATH / "unit_test_run_main_mpla0_intrinsic.tif"
    class_weights = dict({"0": 1, "1": 1})
    cmd = f"""python -m coclico.mpla0.mpla0_intrinsic \
    --input_file {input_file} \
    --output_file {output_tif} \
    --class_weights '{json.dumps(class_weights)}' \
    --pixel_size {pixel_size}
    """
    sp.run(cmd, shell=True, check=True)

    logging.info(cmd)

    assert output_tif.exists()
