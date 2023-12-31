import argparse
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from coclico.config import csv_separator
from coclico.io import read_config_file
from coclico.mpap0.mpap0 import MPAP0


def compute_absolute_diff(c1_count: Dict, ref_count: Dict, classes: List) -> Dict:
    return {k: np.abs(c1_count.get(k, 0) - ref_count.get(k, 0)) for k in classes}


def compute_metric_relative(c1_dir: Path, ref_dir: Path, config_file: Path, output_csv: Path, output_csv_tile: Path):
    """Count points on las file from c1 classification, for all classes, relative to reference classification.
    Compute also a score depending on weights in the config_file keys, and save result in output_csv file.
    In case of "composed classes" in the class_weight dict in the config file (eg: "3_4"), the returned value is the
    sum of the points counts of each class from the compose class (count(3) + count(4))

    The computed metrics are:
    - absolute_diff: the difference of number of points
    - ref_count: the number of points in the reference

    These metrics are stored tile by tile and class by class in the output_csv_tile file
    These metrics are stored class by class for the whole data in the output_csv file

    Args:
        c1_dir (Path):  path to the c1 classification directory,
                        where there are json files with the result of mpap0 intrinsic metric
        ref_dir (Path): path to the reference classification directory,
                        where there are json files with the result of mpap0 intrinsic metric
        config_file (Path):  Coclico configuration file
        output_csv (Path):  path to output csv file
        output_csv_tile (Path):  path to output csv file, result by tile
    """
    config_dict = read_config_file(config_file)
    class_weights = config_dict[MPAP0.metric_name]["weights"]

    total_ref_count = Counter()
    total_c1_count = Counter()
    data = []
    classes = class_weights.keys()
    for ref_file in ref_dir.iterdir():
        c1_file = c1_dir / ref_file.name

        with open(c1_file, "r") as f:
            c1_count = json.load(f)

        with open(ref_file, "r") as f:
            ref_count = json.load(f)

        abs_diff = compute_absolute_diff(c1_count, ref_count, classes)

        total_ref_count += Counter(ref_count)
        total_c1_count += Counter(c1_count)

        new_line = [
            {
                "tile": ref_file.stem,
                "class": cl,
                "absolute_diff": abs_diff.get(cl, 0),
                "ref_count": ref_count.get(cl, 0),
            }
            for cl in classes
        ]
        data.extend(new_line)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv(output_csv_tile, index=False, sep=csv_separator)
    logging.debug(df.to_markdown())

    total_abs_diff = compute_absolute_diff(total_c1_count, total_ref_count, classes)

    data = [
        {"class": cl, "absolute_diff": total_abs_diff.get(cl, 0), "ref_count": total_ref_count.get(cl, 0)}
        for cl in classes
    ]
    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False, sep=csv_separator)

    logging.debug(df.to_markdown())


def parse_args():
    parser = argparse.ArgumentParser("Run mpap0 metric on one tile")
    parser.add_argument(
        "-i",
        "--input-dir",
        required=True,
        type=Path,
        help="Path to the classification directory, \
        where there are json files with the result of mpap0 intrinsic metric",
    )
    parser.add_argument(
        "-r",
        "--ref-dir",
        required=True,
        type=Path,
        help="Path to the reference directory, where there are json files with the result of mpap0 intrinsic metric",
    )
    parser.add_argument("-o", "--output-csv", required=True, type=Path, help="Path to the CSV output file")
    parser.add_argument(
        "-t", "--output-csv-tile", required=True, type=Path, help="Path to the CSV output file, result by tile"
    )
    parser.add_argument(
        "-c",
        "--config-file",
        required=True,
        type=Path,
        help="Coclico configuration file",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    compute_metric_relative(
        c1_dir=Path(args.input_dir),
        ref_dir=Path(args.ref_dir),
        config_file=args.config_file,
        output_csv=Path(args.output_csv),
        output_csv_tile=Path(args.output_csv_tile),
    )
