import argparse
import logging
from pathlib import Path

import pandas as pd

from coclico.config import csv_separator
from coclico.io import read_config_file
from coclico.mobj0.mobj0 import MOBJ0


def compute_metric_relative(
    c1_dir: Path, ref_dir: Path, occupancy_dir: Path, config_file: str, output_csv: Path, output_csv_tile: Path
):
    """Compute metrics that describe the difference between c1 and ref height maps.
    The occupancy map is used to mask the pixels for which the difference is computed

    The metrics are:
    - mean_diff: the average difference in z between the height maps
    - max_diff: the maximum difference in z between the height maps
    - std_diff: the standard deviation of the difference in z betweeen the height maps

    These metrics are stored tile by tile and class by class in the output_csv_tile file
    These metrics are stored class by class for the whole data in the output_csv file

    Args:
        c1_dir (Path):  path to the c1 classification directory,
                        where there are json files with the result of mpap0 intrinsic metric
        ref_dir (Path): path to the reference classification directory,
                        where there are json files with the result of mpap0 intrinsic metric
        class_weights (Dict):   class weights dict
        output_csv (Path):  path to output csv file
        output_csv_tile (Path):  path to output csv file, result by tile

    """
    config_dict = read_config_file(config_file)
    class_weights = config_dict[MOBJ0.metric_name]["weights"]
    classes = sorted(class_weights.keys())
    classes
    csv_data = []

    df = pd.DataFrame(csv_data)
    df.to_csv(output_csv, index=False, sep=csv_separator)

    logging.debug(df.to_markdown())
    raise NotImplementedError


def parse_args():
    parser = argparse.ArgumentParser("Run malt0 metric on one tile")
    parser.add_argument(
        "-i",
        "--input-dir",
        required=True,
        type=Path,
        help="Path to the classification directory, \
        where there are tif files with the result of malt0 intrinsic metric (MNx for each class)",
    )
    raise NotImplementedError
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    compute_metric_relative(
        c1_dir=Path(args.input_dir),
        ref_dir=Path(args.ref_dir),
        occupancy_dir=Path(args.occupancy_dir),
        config_file=args.config_file,
        output_csv=Path(args.output_csv),
        output_csv_tile=Path(args.output_csv_tile),
    )
    raise NotImplementedError
