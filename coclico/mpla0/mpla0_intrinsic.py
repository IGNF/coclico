import argparse
import json
import logging
from pathlib import Path
from typing import Dict

import coclico.metrics.occupancy_map as occupancy_map


def compute_metric_intrinsic(las_file: Path, class_weights: Dict, output_tif: Path, pixel_size: float = 0.5):
    """Create 2d occupancy map for each class that is in class_weights keys, and save result in a single output_tif
    file with one layer per class (the classes are sorted alphabetically).

    Args:
        las_file (Path): path to the las file on which to generate mpla0 intrinsic metric
        class_weights (Dict): class weights dict (to know for which classes to generate the binary map)
        output_tif (Path): path to output
        pixel_size (float): size of the output raster pixels
    """
    occupancy_map.create_occupancy_map(las_file, class_weights, output_tif, pixel_size)


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
