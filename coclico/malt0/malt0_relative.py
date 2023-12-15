import argparse
import logging
from pathlib import Path

import numpy as np
import numpy.ma as ma
import pandas as pd
import rasterio

from coclico.config import csv_separator
from coclico.io import read_metrics_weights
from coclico.malt0.malt0 import MALT0


def compute_stats_single_raster(raster: np.array, occupancy_raster: np.array):
    """Compute stats for a single raster, masked by an occupancy raster.

    Returns a np.array for each statistic:
    - maximum value
    - active pixels count
    - mean
    - standard deviation
    - m2 (square distance to the mean), used to calculate the variance
    (as in https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Parallel_algorithm)

    Each array contains one value for each layer of the raster.

    Args:
        raster (np.array): raster for which to compute
        occupancy_raster (np.array): occupancy map of the raster (1 where there are values to compare, 0 anywhere else)

    Returns:
        np.arrays: max value, pixel count, mean, standard deviation and m2 values
    """
    masked_raster = ma.masked_array(raster, 1 - occupancy_raster)
    max_val = ma.max(masked_raster, axis=(1, 2))
    count = np.sum(occupancy_raster, axis=(1, 2))
    mean_val = ma.mean(masked_raster, axis=(1, 2))
    std_val = ma.std(masked_raster, axis=(1, 2))
    m2 = ma.sum(np.square(masked_raster - mean_val[:, None, None]), axis=(1, 2))  # distance to the mean

    return max_val, count, mean_val, std_val, m2


def update_overall_stats(
    max_val: np.array,
    max_previous: np.array,
    count: np.array,
    count_previous: np.array,
    mean_val: np.array,
    mean_previous: np.array,
    m2: np.array,
    m2_previous: np.array,
):
    """Update stats of all values in a bunch of rasters based on the stats computed on a single raster

    Args:
        max_val (np.array): max value of the current raster
        max_previous (np.array): max value of the bunch of rasters before updating
        count (np.array): pixels count of the current raster
        count_previous (np.array): pixels count of the bunch of rasters before updating
        mean_val (np.array): mean value of the current raster
        mean_previous (np.array): mean of the bunch of rasters before updating
        m2 (np.array): sum of square distance to the mean of the current raster
        m2_previous (np.array): m2 value of the bunch of rasters before updating

    Returns:
        np.arrays: updated statistics
    """
    # Update total values
    max_updated = np.maximum(max_previous, max_val)
    count_updated = count_previous + count
    delta = mean_previous - mean_val
    m2_updated = m2_previous + m2 + delta**2 * count_previous * count / count_updated
    mean_updated = count_previous / count_updated * mean_previous + count / count_updated * mean_val

    return max_updated, count_updated, mean_updated, m2_updated


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
    config_dict = read_metrics_weights(config_file)
    class_weights = config_dict[MALT0.metric_name]["weights"]
    classes = sorted(class_weights.keys())
    csv_data = []

    # Store the mean of the differences between elevation rasters where occupancy map is true
    # in the previously seen rasters
    total_mean_diff = np.zeros(len(classes))
    # Store the number of pixels that are true in the occupancy maps of the previously seen rasters
    total_count = np.zeros(len(classes))
    # Store the maximum difference in rasters values (where occupancy map is true)
    # in the previously seen rasters
    total_max_diff = np.zeros(len(classes))
    # Use Chan algorithm for parallel variance computation to calculate standard deviation
    # in a single pass on raster files
    # cf. https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Parallel_algorithm
    # Store the squared distance to the current mean of the rasters differences
    # in the previously seen rasters
    total_m2 = np.zeros(len(classes))

    for ref_file in ref_dir.iterdir():
        c1_file = c1_dir / ref_file.name
        occupancy_file = occupancy_dir / ref_file.name
        with rasterio.Env():
            with rasterio.open(c1_file) as c1:
                c1_raster = c1.read()

            with rasterio.open(ref_file) as ref:
                ref_raster = ref.read()

            with rasterio.open(occupancy_file) as occ:
                occupancy_raster = occ.read()

        max_diff, count, mean_diff, std_diff, m2_diff = compute_stats_single_raster(
            np.abs(c1_raster - ref_raster), occupancy_raster
        )

        new_line = [
            {
                "tile": ref_file.stem,
                "class": cl,
                "max_diff": max_diff[ii],
                "mean_diff": mean_diff[ii],
                "std_diff": std_diff[ii],
            }
            for ii, cl in enumerate(classes)
        ]
        csv_data.extend(new_line)

        total_max_diff, total_count, total_mean_diff, total_m2 = update_overall_stats(
            max_diff, total_max_diff, count, total_count, mean_diff, total_mean_diff, m2_diff, total_m2
        )

    total_std_diff = np.sqrt(total_m2 / total_count)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(csv_data)
    df.to_csv(output_csv_tile, index=False, sep=csv_separator)
    logging.debug(df.to_markdown())

    data = [
        {
            "class": cl,
            "max_diff": total_max_diff[ii],
            "mean_diff": total_mean_diff[ii],
            "std_diff": total_std_diff[ii],
        }
        for ii, cl in enumerate(classes)
    ]

    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False, sep=csv_separator)

    logging.debug(df.to_markdown())


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
    parser.add_argument(
        "-r",
        "--ref-dir",
        required=True,
        type=Path,
        help="Path to the reference directory, \
        where there are tif files with the result of malt0 intrinsic metric (MNx for each class)",
    )
    parser.add_argument(
        "-oc",
        "--occupancy-dir",
        required=True,
        type=Path,
        help="Path to the occupancydirectory, where there are occupancy maps to use to exclude pixels from "
        "calculation (usually occupancy from the reference classification)",
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
        occupancy_dir=Path(args.occupancy_dir),
        config_file=args.config_file,
        output_csv=Path(args.output_csv),
        output_csv_tile=Path(args.output_csv_tile),
    )
