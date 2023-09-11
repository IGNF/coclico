import argparse

import numpy as np
import pdal
import json
import logging
from pathlib import Path
from typing import Dict


def compute_metric_intrinsic_mpap0(las_file: Path, class_weights: Dict, output_json: Path):
    """Count points on las file for all classes that are in class_weights keys, and save result in output_json file.
    In case of "composed classes" in the class_weight dict (eg: "3,4"), the returned value is the
    sum of the points counts of each class from the compose class (count(3) + count(4))

    Args:
        las_file (Path): path to the las file on which to generate mpap0 intrinsic metric
        class_weights (Dict): class weights dict (to know for which classes to generate the count)
        output_json (Path): path to output
    """

    # TODO: replace with function imported from pdaltools
    # (pdaltools.count_occurences.count_occurences_for_attribute import compute_count_one_file)
    # not done yet as this module is not accessible from outside the library
    pipeline = pdal.Reader.las(str(las_file))
    pipeline |= pdal.Filter.stats(dimensions="Classification", count="Classification")
    pipeline.execute()
    raw_counts = pipeline.metadata["metadata"]["filters.stats"]["statistic"][0]["counts"]
    split_counts = [c.split("/") for c in raw_counts]
    # metadata class key is a float represented as a string with 6 trailing zeros(eg 1.000000)
    points_counts = dict({value.split(".")[0]: int(count) for value, count in split_counts})

    def merge_counts(class_key):
        splitted_class_key = class_key.split(",")
        count = np.sum([points_counts.get(k.strip(), 0) for k in splitted_class_key])

        return count

    # get results for classes that are in weights dictionary (merged if necessary)
    out_counts = dict({k: int(merge_counts(k)) for k in class_weights.keys()})

    logging.debug(f"Class weights: {class_weights}")
    logging.debug(f"Points counts: {points_counts}")
    logging.debug(f"out counts: {out_counts}")

    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w") as outfile:
        json.dump(out_counts, outfile, indent=4)


def parse_args():
    parser = argparse.ArgumentParser("Run mpap0 metric on one tile")
    parser.add_argument("--input_file", type=Path, help="Path to the LAS file")
    parser.add_argument("--output_file", type=Path, help="Path to the JSON output file")
    parser.add_argument(
        "--class_weights", type=json.loads, help="Dictionary of the classes weights for the metric (as a string)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    compute_metric_intrinsic_mpap0(
        las_file=Path(args.input_file), class_weights=args.class_weights, output_json=Path(args.output_file)
    )
