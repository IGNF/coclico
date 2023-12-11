import json
import logging
import shutil
import subprocess as sp
from pathlib import Path

import numpy as np
import pytest
import rasterio
from pdaltools.las_info import las_info_metadata

from coclico.malt0 import malt0_intrinsic

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/malt0_intrinsic")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_create_multilayer_2d_mnx_map(ensure_test1_data):
    las_file = Path("./data/test1/niv1/tile_splitted_2818_32247.laz")
    pixel_size = 0.5
    no_data_value = -9999
    las_mtd = las_info_metadata(las_file)
    las_extent = (las_mtd["minx"], las_mtd["miny"], las_mtd["maxx"], las_mtd["maxy"])
    logging.debug(f"Test create_multilayer_2d_mnx_map on las with extent {las_extent}")
    class_weights = dict(
        {
            "0": 1,
            "1": 1,
            "2": 0,  # simple classes
            "3_4_5": 1,  # composed class
            "3 _ 4": 2,  # composed class with spaces
        }
    )
    classes_z_minmax = dict(
        {
            "0": None,
            "1": [85.68, 101.65],
            "2": [84.96, 105.88],
            "3_4_5": [85.5, 124.17],
            "3 _ 4": [85.5, 105.41],
        }
    )  # fetched via metadata from a pdal pipeline with classification filter and stats
    output_tif = TMP_PATH / "unit_create_multilayer_2d_mnx_map.tif"
    output_tif.parent.mkdir(parents=True, exist_ok=True)
    malt0_intrinsic.create_mnx_map(las_file, class_weights, output_tif, pixel_size, no_data_value=no_data_value)

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

    # Check tif shape
    assert output_data.shape[0] == len(class_weights.keys())

    x_las_extent = las_extent[2] - las_extent[0]
    y_las_extent = las_extent[3] - las_extent[1]
    assert output_data.shape[1] == np.ceil(y_las_extent / pixel_size)
    assert output_data.shape[2] == np.ceil(x_las_extent / pixel_size)

    for ii, k in enumerate(sorted(class_weights.keys())):
        layer_data = output_data[ii, :, :]
        if k == "0":
            # input las does not contain points with class 0 so output layer should contain only no_data
            assert np.all(layer_data == no_data_value)
        else:
            # all other classes have data, so their layers should not contain only no-data
            # Where the layers have data, they should be between z_min and z_max of the class points
            has_data = layer_data != -9999
            assert np.any(has_data)
            assert np.min(layer_data[has_data]) >= classes_z_minmax[k][0]
            assert np.max(layer_data[has_data]) <= classes_z_minmax[k][1]


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
    malt0_intrinsic.compute_metric_intrinsic(las_file, class_weights, output_tif, pixel_size=pixel_size)

    assert output_tif.exists()


def test_compute_metric_intrinsic_w_occupancy(ensure_test1_data):
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
    output_tif = TMP_PATH / "mpla0_intrinsic_w_metadata" / "mnx.tif"
    occupancy_tif = TMP_PATH / "mpla0_intrinsic_w_metadata" / "occupancy.tif"
    malt0_intrinsic.compute_metric_intrinsic(las_file, class_weights, output_tif, occupancy_tif, pixel_size=pixel_size)

    assert output_tif.exists()
    assert occupancy_tif.exists()

    with rasterio.Env():
        with rasterio.open(output_tif) as f:
            mnx_data = f.read()
            mnx_bounds = f.bounds
        with rasterio.open(occupancy_tif) as f:
            occupancy_data = f.read()
            occupancy_bounds = f.bounds

    assert mnx_data.shape == occupancy_data.shape
    assert mnx_bounds == occupancy_bounds


def test_run_main(ensure_test1_data):
    pixel_size = 0.5
    input_file = Path("./data/test1/niv1/tile_splitted_2818_32247.laz")
    output_tif = TMP_PATH / "intrinsic" / "mnx" / "tile_splitted_2818_32247.tif"
    output_occupancy_tif = TMP_PATH / "intrinsic" / "occupancy" / "tile_splitted_2818_32247.tif"
    class_weights = dict(
        {
            "0": 1,
            "1": 1,
            "2": 0,  # simple classes
            "3_4_5": 1,  # composed class
            "3 _ 4": 2,  # composed class with spaces
        }
    )
    cmd = f"""python -m coclico.malt0.malt0_intrinsic \
    --input-file {input_file} \
    --output-mnx-file {output_tif} \
    --output-occupancy-file {output_occupancy_tif} \
    --class-weights '{json.dumps(class_weights)}' \
    --pixel-size {pixel_size}
    """
    sp.run(cmd, shell=True, check=True)

    logging.info(cmd)

    assert output_tif.exists()
    assert output_occupancy_tif.exists()
