from coclico.csv_manipulation import merge_results
from gpao_utils.utils_store import Store
import json
import operator as op
from pathlib import Path
import shutil
import subprocess as sp
from test.utils import csv_num_rows
import pytest

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/csv_merge_results")


def setup_module():
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_compute_weighted_result():
    input = Path("./data/csv/c1/c1_result.csv")
    weights = {"mpap0": {"1": 1, "2": 2, "3,4": 3}, "mpap0_test": {"1": 1, "2": 2, "3,4": 3}}
    score = merge_results.compute_weighted_result(input, weights)
    assert score == 7


def test_merge_all_results():
    input_c1 = Path("./data/csv/c1/c1_result.csv")
    input_c2 = Path("./data/csv/c2/c2_result.csv")
    weights = {"mpap0": {"0": 1, "2": 2, "3,4": 3}, "mpap0_test": {"0": 1, "2": 2, "3,4": 3}}
    result = TMP_PATH / "results_c1_c2.csv"

    merge_results.merge_all_results([input_c1, input_c2], result, weights)
    assert csv_num_rows(result) == 2


def test_run_main():
    base_path = TMP_PATH / Path("merge_run_main/")
    base_path.mkdir(parents=True)
    input_c1 = Path("./data/csv/c1/c1_result.csv")
    input_c2 = Path("./data/csv/c2/c2_result.csv")
    weights = {"mpap0": {"0": 1, "2": 2, "3,4": 3}, "mpap0_test": {"0": 1, "2": 2, "3,4": 3}}
    result = base_path / "results.csv"

    cmd = f"""python -m coclico.csv_manipulation.merge_results \
    -i {input_c1} \
     {input_c2} \
    --result_out {result} \
    --metric_weights '{json.dumps(weights)}'
    """

    sp.run(cmd, shell=True, check=True)
    assert csv_num_rows(result) == 2


def test_create_merge_all_results_job():
    weights = {"mpap0": {"0": 1, "2": 2, "3,4": 3}, "mpap0_test": {"0": 1, "2": 2, "3,4": 3}}
    input_c1 = Path("./data/csv/c1/c1_result.csv")
    input_c2 = Path("./data/csv/c2/c2_result.csv")
    result = Path("local_store/results.csv")
    store = Store("local_store", "win_store", "unix_store")

    job = merge_results.create_merge_all_results_job([input_c1, input_c2], result, store, weights, result)

    assert job is not None
    assert not op.contains(job.command, "local_store")
    assert op.contains(job.command, "unix_store")
