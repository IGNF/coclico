import argparse
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import rasterio

from coclico.config import csv_separator


def generate_sum_by_layer(raster: np.array, layers: List[str]) -> Dict:
    """Generate the sum on a raster by class:
     * the input raster should be a 3d raster with shape (nb_layers, width, height)
     * The list of layers should correspond to the ids of the layers in the output dict

    Args:
        raster (np.array): 3d input raster
        layers (List[str]): List of layer ids

    Returns:
        Dict: dictionary with the sum of the raster for each layer
    """
    sum_raster = np.sum(raster, axis=(1, 2))  # keep first axis (classes axis)
    sum_dict = {k: v for (k, v) in zip(layers, sum_raster)}

    return sum_dict


def compute_metric_relative(c1_dir: Path, ref_dir: Path, class_weights: Dict, output_csv: Path, output_csv_tile: Path):
    """Compute metrics that describe the difference between c1 and ref occupancy maps.

    The metrics are:
    - union: the number of pixels that contain the requested class in c1 OR in the reference
    - intersection: the number of pixels that contain the requested class in c1 AND in the reference
    - ref_pixel_count: the number of pixels that contain the requested class in the reference

    These metrics are stored tile by tile and class by class in the output_csv_tile file
    These metrics are stored class by class for the whole data in the output_csv file

    Args:
        c1_dir (Path):  path to the c1 classification directory,
                        where there are json files with the result of mpla0 intrinsic metric
        ref_dir (Path): path to the reference classification directory,
                        where there are json files with the result of mpla0 intrinsic metric
        class_weights (Dict):   class weights dict
        output_csv (Path):  path to output csv file
        output_csv_tile (Path):  path to output csv file, result by tile
    """
    total_ref_pixel_count = Counter()
    total_union = Counter()
    total_intersection = Counter()
    data = []
    classes = sorted(class_weights.keys())
    for ref_file in ref_dir.iterdir():
        c1_file = c1_dir / ref_file.name
        with rasterio.Env():
            with rasterio.open(c1_file) as c1:
                c1_raster = c1.read()

            with rasterio.open(ref_file) as ref:
                ref_raster = ref.read()

        union = generate_sum_by_layer(np.logical_or(c1_raster, ref_raster), classes)
        intersection = generate_sum_by_layer(np.logical_and(c1_raster, ref_raster), classes)
        ref_pixel_count = generate_sum_by_layer(ref_raster, classes)

        total_ref_pixel_count += Counter(ref_pixel_count)
        total_union += Counter(union)
        total_intersection += Counter(intersection)

        new_line = [
            {
                "tile": ref_file.stem,
                "class": cl,
                "ref_pixel_count": ref_pixel_count.get(cl, 0),
                "intersection": intersection.get(cl, 0),
                "union": union.get(cl, 0),
            }
            for cl in classes
        ]
        data.extend(new_line)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv(output_csv_tile, index=False, sep=csv_separator)
    logging.debug(df.to_markdown())

    data = [
        {
            "class": cl,
            "ref_pixel_count": total_ref_pixel_count.get(cl, 0),
            "intersection": total_intersection.get(cl, 0),
            "union": total_union.get(cl, 0),
        }
        for cl in classes
    ]
    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False, sep=csv_separator)

    logging.debug(df.to_markdown())


def parse_args():
    parser = argparse.ArgumentParser("Run mpla0 metric on one tile")
    parser.add_argument(
        "-i",
        "--input-dir",
        required=True,
        type=Path,
        help="Path to the classification directory, \
        where there are tif files with the result of mpla0 intrinsic metric",
    )
    parser.add_argument(
        "-r",
        "--ref-dir",
        required=True,
        type=Path,
        help="Path to the reference directory, where there are json files with the result of mpla0 intrinsic metric",
    )
    parser.add_argument("-o", "--output-csv", required=True, type=Path, help="Path to the CSV output file")
    parser.add_argument(
        "-t", "--output-csv-tile", required=True, type=Path, help="Path to the CSV output file, result by tile"
    )
    parser.add_argument(
        "-w",
        "--class-weights",
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
