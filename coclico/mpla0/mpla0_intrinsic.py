import argparse
import logging
from pathlib import Path

import coclico.metrics.occupancy_map as occupancy_map
from coclico.io import read_config_file
from coclico.mpla0.mpla0 import MPLA0


def compute_metric_intrinsic(las_file: Path, config_file: Path, output_tif: Path, pixel_size: float = 0.5):
    """Create 2d occupancy map for each class that is in the config_file,
    and save result in a single output_tif file with one layer per class
    (the classes are sorted alphabetically).

    Args:
        las_file (Path): path to the las file on which to generate mpla0 intrinsic metric
        config_file (Path): Coclico configuration file (to know for which classes
        to generate the binary map)
        output_tif (Path): path to output
        pixel_size (float): size of the output raster pixels
    """
    config_dict = read_config_file(config_file)
    class_weights = config_dict[MPLA0.metric_name]["weights"]
    occupancy_map.create_occupancy_map(las_file, class_weights, output_tif, pixel_size)


def parse_args():
    parser = argparse.ArgumentParser("Run mpla0 intrinsic metric on one tile")
    parser.add_argument("-i", "--input-file", type=Path, required=True, help="Path to the LAS file")
    parser.add_argument("-o", "--output-file", type=Path, required=True, help="Path to the TIF output file")
    parser.add_argument(
        "-c",
        "--config-file",
        type=Path,
        required=True,
        help="Coclico configuration file",
    )
    parser.add_argument("-p", "--pixel-size", type=float, required=True, help="Size of the output raster pixels")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    compute_metric_intrinsic(
        las_file=Path(args.input_file), config_file=args.config_file, output_tif=Path(args.output_file)
    )
