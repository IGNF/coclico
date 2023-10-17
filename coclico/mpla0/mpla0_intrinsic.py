import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Tuple

import laspy
import numpy as np
import rasterio

from coclico.metrics.commons import split_composed_class


def create_2d_binary_map(
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


def compute_metric_intrinsic(las_file: Path, class_weights: Dict, output_tif: Path, pixel_size: float = 0.5):
    """Create 2d occupancy map for each classe that is in class_weights keys, and save result in a single output_tif
    file with one layer per class (the classes are sorted).

    Args:
        las_file (Path): path to the las file on which to generate mpla0 intrinsic metric
        class_weights (Dict): class weights dict (to know for which classes to generate the binary map)
        output_tif (Path): path to output
        pixel_size (float): size of the output raster pixels
    """
    with laspy.open(las_file) as f:
        las = f.read()
        xs, ys = las.x, las.y
        classifs = las.classification
        crs = las.header.parse_crs()

    x_min = np.round(np.min(xs) / pixel_size) * pixel_size
    y_min = np.round(np.min(ys) / pixel_size) * pixel_size
    x_max = np.round(np.max(xs) / pixel_size) * pixel_size
    y_max = np.round(np.max(ys) / pixel_size) * pixel_size
    logging.debug(f"Raster min/max cell centers infered from in las file: ({x_min}, {x_max}), ({y_min}, {y_max})")

    # add 1 to x_pixel and y_pixel because the map should be able to include the extreme points
    x_pixels = int(np.ceil((x_max - x_min) / pixel_size)) + 1
    y_pixels = int(np.ceil((y_max - y_min) / pixel_size)) + 1
    logging.debug(f"Raster number of pixels infered from in las file: ({x_pixels}, {y_pixels})")

    def create_binary_map_from_class(class_key):
        splitted_class_key = split_composed_class(class_key)
        splitted_class_key_int = [int(ii) for ii in splitted_class_key]

        map = create_2d_binary_map(
            xs[np.isin(classifs, splitted_class_key_int)],
            ys[np.isin(classifs, splitted_class_key_int)],
            pixel_size,
            x_min,
            y_max,
            (x_pixels, y_pixels),
        )

        return map

    # get results for classes that are in weights dictionary (merged if necessary) in a 3d array
    # which represents a raster with 1 layer per class
    # keys are sorted to make sure that raster layers can be retrieved in the same order
    binary_maps = np.array([create_binary_map_from_class(k) for k in sorted(class_weights.keys())], dtype=np.uint8)

    logging.debug(f"Creating binary maps with shape {binary_maps.shape}")
    logging.debug(f"The binary maps order is {sorted(class_weights.keys())}")

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


def parse_args():
    parser = argparse.ArgumentParser("Run mpla0 intrinsic metric on one tile")
    parser.add_argument("-i", "--input-file", type=Path, required=True, help="Path to the LAS file")
    parser.add_argument("-o", "--output-file", type=Path, required=True, help="Path to the TIF output file")
    parser.add_argument(
        "-w",
        "--class-weights",
        type=json.loads,
        required=True,
        help="Dictionary of the classes weights for the metric (as a string)",
    )
    parser.add_argument("-p", "--pixel-size", type=float, required=True, help="Size of the output raster pixels")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    compute_metric_intrinsic(
        las_file=Path(args.input_file), class_weights=args.class_weights, output_tif=Path(args.output_file)
    )
