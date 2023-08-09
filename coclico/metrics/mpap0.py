import logging
import numpy as np
import pandas as pd
import pdal

from pathlib import Path
from typing import Dict

from coclico.metrics.commons import bounded_affine_function


def compute_metric_intrisic_mpap0(las_file: Path, class_weights: Dict) -> Dict:
    """Count points on las file for all classes that are in class_weights keys

    Args:
        las_file (Path): path to the las file on which to generate mpap0 intrinsic metric
        class_weights (Dict): class weights dict (to know for which classes to generate the count)

    Returns:
        Dict: count for each class in class_weights keys
    """

    # TODO: replace with function imported from pdaltools
    # (pdaltools.count_occurences.count_occurences_for_attribute import compute_count_one_file)
    # not done yet as this module is not accessible from outside the library
    pipeline = pdal.Reader.las(str(las_file))
    pipeline |= pdal.Filter.stats(dimensions="Classification", count="Classification")
    pipeline.execute()
    raw_counts = pipeline.metadata["metadata"]["filters.stats"]["statistic"][0]["counts"]
    split_counts = [c.split("/") for c in raw_counts]

    points_counts = dict({str(int(float(value))): int(count) for value, count in split_counts})
    # get results only for classes that are in weights dictionary
    out_counts = dict({k: points_counts.get(str(k), 0) for k in class_weights.keys()})

    return out_counts


def compute_metric_relative_mpap0(pts_counts_ci: Dict, pts_counts_ref: Dict) -> Dict:
    all_keys = set(list(pts_counts_ci.keys()) + list(pts_counts_ref.keys()))
    counts_absolute_diff = {k: np.abs(pts_counts_ci.get(k, 0) - pts_counts_ref.get(k, 0)) for k in all_keys}

    return counts_absolute_diff


def compute_note_mpap0(counts_absolute_diff: Dict, pts_counts_ref: Dict) -> Dict:
    def compute_one_note(abs_diff, count):
        if count >= 1000:
            relative_diff = abs_diff / count
            note = bounded_affine_function((0, 1), (0.1, 0), relative_diff)
        else:
            note = bounded_affine_function((20, 1), (100, 0), abs_diff)

        return note

    notes = {
        k: compute_one_note(counts_absolute_diff[k], pts_counts_ref.get(k, 0)) for k in counts_absolute_diff.keys()
    }

    return notes


def compare_one_tile_mpap0(
    ci: Path, ref: Path, out: Path, tile_fn: str, class_weights: Dict, metric_name: str = "mpap0"
):
    logging.debug(f"Compare Ci: {ci} to Ref: {ref} in out {out} for metric MPAP0")
    tile_stem = Path(tile_fn).stem
    out_file = out / (tile_stem + ".csv")
    points_counts_ci = compute_metric_intrisic_mpap0(ci / tile_fn, class_weights)
    points_counts_ref = compute_metric_intrisic_mpap0(ref / tile_fn, class_weights)

    score = compute_metric_relative_mpap0(points_counts_ci, points_counts_ref)
    note = compute_note_mpap0(score, points_counts_ref)
    data = [{"tile": tile_stem, "class": cl, metric_name: note[cl]} for cl in class_weights.keys()]
    df = pd.DataFrame(data)
    df.to_csv(out_file, index=False)
