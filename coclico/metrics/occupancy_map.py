import logging
from pathlib import Path
from typing import Tuple

import laspy
import numpy as np
import rasterio

from coclico.metrics.commons import (
    get_raster_geometry_from_las_bounds,
    split_composed_class,
)


def _create_2d_occupancy_array(
    xs: np.array,
    ys: np.array,
    pixel_size: float,
    x_min: float,
    y_max: float,
    nb_pixels: Tuple[int, int] = (1000, 1000),
) -> np.array:
    """Create 2d binary occupancy map from points coordinates:
    boolean 2d map with 1 where at least one point falls in the pixel, 0 everywhere else.

    Args:
        xs (np.array): vector of x coordinates of all points
        ys (np.array): vector of y coordinates of all points
        pixel_size (float): pixel size (in meters) of the output map
        x_min (float): x coordinate (in meters) of the pixel center of the upper left corner of the map
        y_max (float): y coordinate (in meters) of the pixel center of the upper left corner of the map
        nb_pixels (float, optional): number of pixels on each axis in format (x, y). Defaults to (1000, 1000).

    Returns:
        np.array: Boolean output map
    """
    # numpy array is filled with (y, x) instead of (x, y)
    grid = np.zeros((nb_pixels[1], nb_pixels[0]), dtype=bool)

    for x, y in zip(xs, ys):
        grid_x = min(int((x - (x_min - pixel_size / 2)) / pixel_size), nb_pixels[0] - 1)  # x_min is left pixel center
        grid_y = min(int(((y_max + pixel_size / 2) - y) / pixel_size), nb_pixels[1] - 1)  # y_max is upper pixel center
        grid[grid_y, grid_x] = True

    return grid


def read_las(las_file: Path):
    with laspy.open(las_file) as f:
        las = f.read()

    xs, ys = las.x, las.y
    classifs = las.classification
    crs = las.header.parse_crs()

    return xs, ys, classifs, crs


def create_occupancy_map_array(xs: np.array, ys: np.array, classifs: np.array, pixel_size: float, class_weights: dict):
    las_bounds = (np.min(xs), np.min(ys), np.max(xs), np.max(ys))

    top_left, nb_pixels = get_raster_geometry_from_las_bounds(las_bounds, pixel_size)
    x_min, y_max = top_left

    def create_binary_map_from_class(class_key):
        splitted_class_key = split_composed_class(class_key)
        splitted_class_key_int = [int(ii) for ii in splitted_class_key]

        map = _create_2d_occupancy_array(
            xs[np.isin(classifs, splitted_class_key_int)],
            ys[np.isin(classifs, splitted_class_key_int)],
            pixel_size,
            x_min,
            y_max,
            nb_pixels,
        )

        return map

    # get results for classes that are in weights dictionary (merged if necessary) in a 3d array
    # which represents a raster with 1 layer per class
    # keys are sorted to make sure that raster layers can be retrieved in the same order
    binary_maps = np.array([create_binary_map_from_class(k) for k in sorted(class_weights.keys())], dtype=np.uint8)

    logging.debug(f"Creating binary maps with shape {binary_maps.shape}")
    logging.debug(f"The binary maps order is {sorted(class_weights.keys())}")
    return binary_maps, x_min, y_max


def create_occupancy_map(las_file, class_weights, output_tif, pixel_size):
    """Create 2d occupancy map for each class that is in class_weights keys, and save result in a single output_tif
    file with one layer per class (the classes are sorted alphabetically).

    Args:
        las_file (Path): path to the las file on which to generate occupancy map
        class_weights (Dict): class weights dict (to know for which classes to generate the binary map)
        output_tif (Path): path to output
        pixel_size (float): size of the output raster pixels
    """
    xs, ys, classifs, crs = read_las(las_file)

    binary_maps, x_min, y_max = create_occupancy_map_array(xs, ys, classifs, pixel_size, class_weights)

    output_tif.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.Env():
        with rasterio.open(
            output_tif,
            "w",
            driver="GTiff",
            height=binary_maps.shape[1],
            width=binary_maps.shape[2],
            count=binary_maps.shape[0],
            dtype=rasterio.uint8,
            crs=crs,
            transform=rasterio.transform.from_origin(
                x_min - pixel_size / 2, y_max + pixel_size / 2, pixel_size, pixel_size
            ),
        ) as out_file:
            out_file.write(binary_maps.astype(rasterio.uint8))
