import argparse
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from coclico.config import csv_separator
from coclico.metrics.commons import bounded_affine_function


def compute_absolute_diff(c1_count: Dict, ref_count: Dict, classes: List) -> Dict:
    return {k: np.abs(c1_count.get(k, 0) - ref_count.get(k, 0)) for k in classes}


def compute_note(abs_diff: Dict, ref_count: Dict) -> Dict:
    def compute_one_note(abs_diff, count):
        if count >= 1000:
            relative_diff = abs_diff / count
            note = bounded_affine_function((0, 1), (0.1, 0), relative_diff)
        else:
            note = bounded_affine_function((20, 1), (100, 0), abs_diff)

        return note

    notes = {k: compute_one_note(abs_diff[k], ref_count.get(k, 0)) for k in abs_diff.keys()}

    return notes


def compute_metric_relative(c1_dir: Path, ref_dir: Path, class_weights: Dict, output_csv: Path, output_csv_tile: Path):
    """Count points on las file from c1 classification, for all classes, relative to reference classification.
    Compute also a score depending on class_weights keys, and save result in output_csv file.
    In case of "composed classes" in the class_weight dict (eg: "3,4"), the returned value is the
    sum of the points counts of each class from the compose class (count(3) + count(4))

    Args:
        c1_dir (Path):  path to the c1 classification directory,
                        where there are json files with the result of mpap0 intrinsic metric
        ref_dir (Path): path to the reference classification directory,
                        where there are json files with the result of mpap0 intrinsic metric
        class_weights (Dict):   class weights dict
        output_csv (Path):  path to output csv file
        output_csv_tile (Path):  path to output csv file, result by tile
    """
    metric = "mpap0"
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
        note = compute_note(abs_diff, ref_count)

        total_ref_count += Counter(ref_count)
        total_c1_count += Counter(c1_count)

        new_line = [{"tile": ref_file.stem, "class": cl, metric: note[cl]} for cl in classes]
        data.extend(new_line)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv(output_csv_tile, index=False, sep=csv_separator)
    logging.debug(df.to_markdown())

    total_abs_diff = compute_absolute_diff(total_c1_count, total_ref_count, classes)
    total_notes = compute_note(total_abs_diff, total_ref_count)

    data = [{"class": cl, metric: total_notes.get(cl, 0)} for cl in classes]
    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False, sep=csv_separator)

    logging.debug(df.to_markdown())


def parse_args():
    parser = argparse.ArgumentParser("Run mpap0 metric on one tile")
    parser.add_argument(
        "-i",
        "--input_dir",
        required=True,
        type=Path,
        help="Path to the classification directory, \
        where there are json files with the result of mpap0 intrinsic metric",
    )
    parser.add_argument(
        "-r",
        "--ref_dir",
        required=True,
        type=Path,
        help="Path to the reference directory, where there are json files with the result of mpap0 intrinsic metric",
    )
    parser.add_argument("--output_csv", required=True, type=Path, help="Path to the CSV output file")
    parser.add_argument(
        "--output_csv_tile", required=True, type=Path, help="Path to the CSV output file, result by tile"
    )
    parser.add_argument(
        "-w",
        "--class_weights",
        required=True,
        type=json.loads,
        help="Dictionary of the classes weights for the metric (as a string)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    compute_metric_relative(
        c1_dir=Path(args.input_dir),
        ref_dir=Path(args.ref_dir),
        class_weights=args.class_weights,
        output_csv=Path(args.output_csv),
        output_csv_tile=Path(args.output_csv_tile),
    )
