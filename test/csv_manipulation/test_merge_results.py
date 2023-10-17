import json
import operator as op
import shutil
import subprocess as sp
import test.utils as tu
from pathlib import Path

import pytest
from gpao_utils.store import Store

from coclico.csv_manipulation import merge_results

pytestmark = pytest.mark.docker

TMP_PATH = Path("./tmp/csv_merge_results")


def setup_module():
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_compute_weighted_result():
    input = Path("./data/csv/c1/c1_result.csv")
    weights = {"mpap0": {"1": 1, "2": 2, "3_4": 3}, "mpla0": {"1": 1, "2": 2, "5": 3}}
    score = merge_results.compute_weighted_result(input, weights)
    assert score == {"classification": "c1", "score": 7.0, "mpap0": 4.6, "mpla0": 2.4}


def test_merge_all_results():
    input_c1 = Path("./data/csv/c1/c1_result.csv")
    input_c2 = Path("./data/csv/c2/c2_result.csv")
    weights = {"mpap0": {"0": 1, "2": 2, "3_4": 3}, "mpla0": {"2": 2, "5": 3}}
    result = TMP_PATH / "results_c1_c2.csv"
    result_detailed = TMP_PATH / "results_c1_c2_by_metric.csv"

    merge_results.merge_all_results([input_c1, input_c2], result, weights)
    df = tu.check_df_exists_with_no_empty_data(result)
    assert len(df.index) == 2

    df = tu.check_df_exists_with_no_empty_data(result_detailed)
    assert len(df.index) == 2
    assert set(df.columns) == set(["classification", "score"] + list(weights.keys()))


def test_merge_result_append_existing_file():
    input_c1 = Path("./data/csv/c1/c1_result.csv")
    input_c2 = Path("./data/csv/c2/c2_result.csv")
    weights = {"mpap0": {"0": 1, "2": 2, "3_4": 3}, "mpla0": {"2": 2, "5": 3}}
    result = TMP_PATH / "results_c1_c2_append.csv"
    result_detailed = TMP_PATH / "results_c1_c2_append_by_metric.csv"

    merge_results.merge_all_results([input_c1], result, weights)

    df = tu.check_df_exists_with_no_empty_data(result)
    assert len(df.index) == 1
    df = tu.check_df_exists_with_no_empty_data(result_detailed)
    assert len(df.index) == 1

    merge_results.merge_all_results([input_c2], result, weights)

    df = tu.check_df_exists_with_no_empty_data(result)
    assert len(df.index) == 2
    df = tu.check_df_exists_with_no_empty_data(result_detailed)
    assert len(df.index) == 2


def test_merge_result_merge_existing_file():
    input_c1 = Path("./data/csv/c1/c1_result.csv")
    input_c2 = Path("./data/csv/c2/c2_result.csv")
    weights = {"mpap0": {"0": 1, "2": 2, "3_4": 3}, "mpla0": {"2": 2, "5": 3}}
    result = TMP_PATH / "results_c1_existing.csv"
    result_detailed = TMP_PATH / "results_c1_existing_by_metric.csv"

    merge_results.merge_all_results([input_c1, input_c2], result, weights)

    df = tu.check_df_exists_with_no_empty_data(result)
    assert len(df.index) == 2
    df = tu.check_df_exists_with_no_empty_data(result_detailed)
    assert len(df.index) == 2
    assert set(df.columns) == set(["classification", "score"] + list(weights.keys()))

    merge_results.merge_all_results([input_c1], result, weights)

    df = tu.check_df_exists_with_no_empty_data(result)
    assert len(df.index) == 2
    df = tu.check_df_exists_with_no_empty_data(result_detailed)
    assert len(df.index) == 2
    assert set(df.columns) == set(["classification", "score"] + list(weights.keys()))


def test_run_main():
    base_path = TMP_PATH / Path("merge_run_main/")
    base_path.mkdir(parents=True)
    input_c1 = Path("./data/csv/c1/c1_result.csv")
    input_c2 = Path("./data/csv/c2/c2_result.csv")
    weights = {"mpap0": {"0": 1, "2": 2, "3_4": 3}, "mpla0": {"0": 1, "2": 2, "5": 3}}
    result = base_path / "results.csv"

    cmd = f"""python -m coclico.csv_manipulation.merge_results \
    -i {input_c1} \
     {input_c2} \
    --output {result} \
    --metric_weights '{json.dumps(weights)}'
    """

    sp.run(cmd, shell=True, check=True)
    assert tu.csv_num_rows(result) == 2


def test_create_merge_all_results_job():
    weights = {"mpap0": {"0": 1, "2": 2, "3_4": 3}, "mpla0": {"0": 1, "2": 2, "5": 3}}
    input_c1 = Path("./data/csv/c1/c1_result.csv")
    input_c2 = Path("./data/csv/c2/c2_result.csv")
    result = Path("local_store/results.csv")
    store = Store("local_store", "win_store", "unix_store")

    job = merge_results.create_merge_all_results_job([input_c1, input_c2], result, store, weights, result)

    assert job is not None
    assert not op.contains(job.command, "local_store")
    assert op.contains(job.command, "unix_store")
