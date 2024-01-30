import argparse
import logging
from pathlib import Path

import cv2
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from osgeo import gdal
from rasterio.features import shapes as rasterio_shapes
from shapely.geometry import shape as shapely_shape

import coclico.io
from coclico.metrics.occupancy_map import create_occupancy_map_array, read_las
from coclico.mobj0.mobj0 import MOBJ0

gdal.UseExceptions()


def create_objects_array(las_file, pixel_size, class_weights):
    xs, ys, classifs, crs = read_las(las_file)
    kernel = 3  # rendre accessible le kernel à l'opérateur

    binary_maps, x_min, y_max = create_occupancy_map_array(xs, ys, classifs, pixel_size, class_weights)
    object_maps = np.zeros_like(binary_maps)
    for index in range(len(class_weights)):
        object_maps[index, :, :] = operate_morphology_transformations(binary_maps[index, :, :], kernel)

    return object_maps, crs, x_min, y_max


def vectorize_occupancy_map(binary_maps, crs, x_min, y_max, pixel_size):
    # Create empty dataframe
    gdf_list = []

    for ii, map_layer in enumerate(binary_maps):
        shapes_layer = rasterio_shapes(
            map_layer,
            connectivity=8,
            transform=rasterio.transform.from_origin(
                x_min - pixel_size / 2, y_max + pixel_size / 2, pixel_size, pixel_size
            ),
        )

        geometries = [shapely_shape(shapedict) for shapedict, value in shapes_layer if value != 0]
        nb_geometries = len(geometries)
        gdf_list.append(
            gpd.GeoDataFrame(
                {"layer": ii * np.ones(nb_geometries), "geometry": geometries},
                geometry="geometry",
                crs=crs,
            )
        )

    gdf = pd.concat(gdf_list)

    return gdf


def operate_morphology_transformations(obj_array: np.ndarray, kernel: int):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel, kernel))

    img = cv2.morphologyEx(obj_array, cv2.MORPH_CLOSE, kernel)
    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

    return img


def compute_metric_intrinsic(las_file: Path, config_file: Path, output_geojson: Path, pixel_size: float = 0.5):
    config_dict = coclico.io.read_config_file(config_file)
    class_weights = config_dict[MOBJ0.metric_name]["weights"]
    output_geojson.parent.mkdir(parents=True, exist_ok=True)
    obj_array, crs, x_min, y_max = create_objects_array(las_file, pixel_size, class_weights)
    polygons_gdf = vectorize_occupancy_map(obj_array, crs, x_min, y_max, pixel_size)
    polygons_gdf.simplify(tolerance=0.05, preserve_topology=False)
    polygons_gdf.to_file(output_geojson)


def parse_args():
    parser = argparse.ArgumentParser("Run mobj0 intrinsic metric on one tile")
    parser.add_argument("-i", "--input-file", type=Path, required=True, help="Path to the LAS file")
    parser.add_argument("-o", "--output-geojson", type=Path, required=True, help="Path to the output geojson")
    parser.add_argument(
        "-c",
        "--config-file",
        type=Path,
        required=True,
        help="Coclico configuration file",
    )
    parser.add_argument(
        "-p", "--pixel-size", type=float, required=True, help="Pixel size of the intermediate occupancy map"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    compute_metric_intrinsic(
        las_file=Path(args.input_file),
        config_file=args.config_file,
        output_geojson=Path(args.output_geojson),
    )
