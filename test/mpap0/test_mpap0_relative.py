import json
import logging
import shutil
import subprocess as sp
from pathlib import Path
from test import utils

import pandas as pd
import pytest

from coclico.config import csv_separator
from coclico.mpap0 import mpap0_relative

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/mpap0")


def setup_module(module):
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_compute_absolute_diff():
    count_c1 = dict({"1": 12, "2": 20, "3_4": 2})
    count_ref = dict({"1": 10, "2": 20, "5": 2})
    classes = ["1", "3_4"]
    score = mpap0_relative.compute_absolute_diff(count_c1, count_ref, classes)
    assert score == dict({"1": 2, "3_4": 2})


note_mpap0_data = [
    ({}, {}, {}),  # limit case
    (
        {"0": 0, "1": 50, "2_3": 300},  # diff c1 to ref
        {"0": 1000, "1": 1000, "2_3": 2000},  # count_ref (point per class)
        {"0": 1, "1": 0.5, "2_3": 0},  # expected score
    ),  # cases over 1000 ref points
    (
        {"0": 10, "1": 60, "2": 100, "3_4_5": 500},  # diff c1 to ref
        {"1": 100, "2": 200, "3_4_5": 100},  # count_ref (point per class)
        {"0": 1, "1": 0.5, "2": 0, "3_4_5": 0},  # expected score
    ),  # cases under 1000 ref points
]


@pytest.mark.parametrize("diff,counts_ref,expected", note_mpap0_data)
def test_compute_note(diff, counts_ref, expected):
    assert mpap0_relative.compute_note(diff, counts_ref) == expected


def test_compute_metric_relative():
    c1_dir = Path("./data/mpap0/c1/intrinsic")
    ref_dir = Path("./data/mpap0/ref/intrinsic")
    class_weights = dict({"1": 1, "2": 0, "3_4_5": 1, "9": 1})  # simple classes  # composed class
    output_csv = TMP_PATH / "relative" / "result.csv"
    output_csv_tile = TMP_PATH / "relative" / "result_tile.csv"

    mpap0_relative.compute_metric_relative(c1_dir, ref_dir, class_weights, output_csv, output_csv_tile)

    expected_rows = 4 * 4  # 4 files * 4 classes
    assert utils.csv_num_rows(output_csv_tile) == expected_rows

    expected_rows = 4  # 4 classes
    assert utils.csv_num_rows(output_csv) == expected_rows

    df = pd.read_csv(output_csv, sep=csv_separator)
    mpap0_score_class_9 = df["mpap0"][df.index[df["class"] == "9"][0]]
    assert mpap0_score_class_9 == 1  # score for class 9 is 1. Case: 0 point for classe 9 in c1 and ref.


def test_run_main():
    c1_dir = Path("./data/mpap0/c1/intrinsic")
    ref_dir = Path("./data/mpap0/ref/intrinsic")
    output_csv = TMP_PATH / "unit_test_run_main_mpap0_relative.csv"
    output_csv_tile = TMP_PATH / "unit_test_run_main_mpap0_relative_tile.csv"
    class_weights = dict({"1": 1, "2": 1})
    cmd = f"""python -m coclico.mpap0.mpap0_relative \
        --input-dir {c1_dir} \
        --ref-dir {ref_dir} \
        --class-weights '{json.dumps(class_weights)}' \
        --output-csv {output_csv} \
        --output-csv-tile {output_csv_tile} \
    """

    sp.run(cmd, shell=True, check=True)
    logging.info(cmd)

    expected_rows = 4 * 2  # 4 files * 2 classes
    assert utils.csv_num_rows(output_csv_tile) == expected_rows

    expected_rows = 2  # 2 classes
    assert utils.csv_num_rows(output_csv) == expected_rows
