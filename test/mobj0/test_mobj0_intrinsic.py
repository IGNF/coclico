import logging
import shutil
import subprocess as sp
from pathlib import Path

import geopandas as gpd
import pytest

import coclico.io
from coclico.mobj0 import mobj0_intrinsic

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/mobj0_intrinsic")
CONFIG_FILE_METRICS = Path("./test/configs/config_test_metrics.yaml")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_compute_metric_intrinsic(ensure_test1_data):
    las_file = Path("./data/test1/niv1/tile_splitted_2818_32247.laz")
    pixel_size = 0.5
    output_geojson = TMP_PATH / "intrinsic" / "unit_test_mpla0_intrinsic.geojson"
    config = coclico.io.read_config_file(CONFIG_FILE_METRICS)
    nb_layers = len(config["mobj0"]["weights"])

    mobj0_intrinsic.compute_metric_intrinsic(las_file, CONFIG_FILE_METRICS, output_geojson, pixel_size=pixel_size)

    assert output_geojson.exists()
    gdf = gpd.read_file(output_geojson)
    logging.debug(gdf.to_markdown())
    assert len(gdf.index) > 0
    assert len(set(gdf["layer"])) == nb_layers


def test_run_main(ensure_test1_data):
    pixel_size = 0.5
    input_file = Path("./data/test1/niv1/tile_splitted_2818_32247.laz")
    output_geojson = TMP_PATH / "intrinsic" / "tile_splitted_2818_32247.geojson"

    cmd = f"""python -m coclico.mobj0.mobj0_intrinsic \
    --input-file {input_file} \
    --output-geojson {output_geojson} \
    --config-file {CONFIG_FILE_METRICS} \
    --pixel-size {pixel_size}
    """
    sp.run(cmd, shell=True, check=True)

    logging.info(cmd)

    assert output_geojson.exists()
