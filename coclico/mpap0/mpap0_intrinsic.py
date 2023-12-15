import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pdal

from coclico.io import read_config_file
from coclico.metrics.commons import split_composed_class
from coclico.mpap0.mpap0 import MPAP0


def compute_metric_intrinsic(las_file: Path, config_file: Path, output_json: Path):
    """Count points on las file for all classes in class_weights keys in the config file, and save result
    in output_json file.
    In case of "composed classes" in the class_weight dict (eg: "3,4"), the returned value is the
    sum of the points counts of each class from the compose class (count(3) + count(4))

    Args:
        las_file (Path): path to the las file on which to generate mpap0 intrinsic metric
        config_file (Path): class weights dict (to know for which classes to generate the count)
        output_json (Path): path to output
    """

    config_dict = read_config_file(config_file)
    class_weights = config_dict[MPAP0.metric_name]["weights"]

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
        splitted_class_key = split_composed_class(class_key)
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
    parser.add_argument("-i", "--input-file", type=Path, required=True, help="Path to the LAS file")
    parser.add_argument("-o", "--output-file", type=Path, required=True, help="Path to the JSON output file")
    parser.add_argument("--config-file", type=Path, required=True, help="Coclico configuration file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    compute_metric_intrinsic(
        las_file=Path(args.input_file), config_file=args.config_file, output_json=Path(args.output_file)
    )
