import logging
from typing import List, Tuple

import numpy as np

from coclico.config import composed_class_separator


def split_composed_class(class_key: str) -> List[str]:
    """Split composed class key (separated by COMPOSED_CLASS_SEPARATOR) into its elementary classes.
    Example "3_4_5" becomes ["3", "4", "5"]
    Args:
        class_key (str): origin key

    Returns:
        List[str]: splitted keys
    """
    return class_key.split(composed_class_separator)


def bounded_affine_function(coordinates_min: Tuple, coordinates_max: Tuple, x_query: np.array) -> np.array:
    """Compute clamped affine function
               max ________ or ______min
              /                         \\
             /                           \\
    _____min/                             \\max________

    Args:
        coordinates_min (Tuple): (x, y) tuple for the first point with the lowest x value
        coordinates_max (Tuple): (x, y) tuple for the first point with the highest x value
        x_query (float): query value

    Returns:
        float: _description_
    """

    x_min, y_min = coordinates_min
    x_max, y_max = coordinates_max

    # affine function y = a*x + b
    a = (y_max - y_min) / (x_max - x_min)
    b = y_min - a * x_min
    y_query = a * x_query + b

    y_query[x_query < x_min] = y_min
    y_query[x_query > x_max] = y_max

    return y_query


def get_raster_geometry_from_las_bounds(las_bounds: Tuple[float], pixel_size: float):
    """Compute expected raster top left corner (cell center) and number of pixels from las min/max values and pixel
    size

    Args:
        las_bounds (Tuple(float)): Las min/max values : (x_min, y_min, x_max, ymax)
        pixel_size (float): Pixel size of the raster

    Returns:
        (Tuple(float, float), Tuple(int, int)) coordinates of the top-left corner, and number of pixels on each axis
    """
    x_min_las, y_min_las, x_max_las, y_max_las = las_bounds
    x_min = np.round(x_min_las / pixel_size) * pixel_size
    y_min = np.round(y_min_las / pixel_size) * pixel_size
    x_max = np.round(x_max_las / pixel_size) * pixel_size
    y_max = np.round(y_max_las / pixel_size) * pixel_size
    logging.debug(
        f"Raster min/max cell centers infered from in las file: min: ({x_min}, {y_min}) max:({x_max}, {y_max})"
    )

    # add 1 to x_pixel and y_pixel because the map should be able to include the extreme points
    x_pixels = int(np.ceil((x_max - x_min) / pixel_size)) + 1
    y_pixels = int(np.ceil((y_max - y_min) / pixel_size)) + 1
    logging.debug(f"Raster number of pixels infered from in las file: ({x_pixels}, {y_pixels})")

    return (x_min, y_max), (x_pixels, y_pixels)


