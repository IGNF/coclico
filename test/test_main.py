from coclico import main
from pathlib import Path
import shutil
import pytest
import subprocess as sp
from gpao_utils.utils_store import Store
from gpao_utils.utils_test import wait_running_job
import test.utils as tu
import json


TMP_PATH = Path("./tmp/main")

STORE = Store("local_store", "win_store", "unix_store")

URL_API = "http://localhost:8080/api/"


def setup_module():
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def read_metrics_weights_ok():
    weights_file = Path("./test/configs/metrics_weights.yaml")
    weights = main.read_metrics_weights(weights_file)
    assert all([k in main.METRICS.keys() for k in weights.keys()])
    for _, val in weights.items():
        assert isinstance(val, dict)
        assert all([isinstance(cl, str) for cl in val.keys()])


def read_metrics_weights_fail():
    weights_file = Path("./test/configs/metrics_weights_fail.yaml")
    with pytest.raises(ValueError):
        main.read_metrics_weights(weights_file)


def read_metrics_weights_different_spacing():
    weights_file = Path("./test/configs/metrics_weights_fail.yaml")
    with pytest.raises(ValueError):
        weights = main.read_metrics_weights(weights_file)
    assert all([k in main.METRICS.keys() for k in weights.keys()])
    expected_classes = {"1", "2", "3,4"}
    for _, val in weights.items():
        assert isinstance(val, dict)
        assert all([cl in expected_classes for cl in val.keys()])


def test_create_compare_projects_test1_ok(ensure_test1_data):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / "create_compare_projects_test1_ok"
    project_name = "coclico_test_compare_create_compare_projects_test1_fail"
    metrics_weights = {"mpap0": {"0": 1, "1,2": 2}, "mpap0_test": {"0": 1, "1,2": 2}}

    projects = main.create_compare_projects(c1, c2, ref, out, STORE, project_name, metrics_weights)

    assert len(projects) == 1
    projects_jsons = [json.loads(pr.to_json()) for pr in projects]
    for pr_json in projects_jsons:
        assert len(pr_json["jobs"]) > 0  # No empty projects
        assert pr_json["name"].startswith(project_name)
    # Assert both comparison projects have the same number of jobs
    # assert len(projects_jsons[0]["jobs"]) == len(projects_jsons[1]["jobs"])
    # # Assert that the merge project has one job with correct dependencies
    # assert len(projects_jsons[2]["jobs"]) == 1
    # assert len(projects_jsons[2]["deps"]) == 2


def test_compare_test1_default(ensure_test1_data, use_gpao_server):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("test1/compare")
    gpao_hostname = "localhost"
    runner_store_path = Path("./data").resolve()
    local_store_path = Path("data").resolve()
    project_name = "coclico_test_compare_test1_default"

    main.compare(c1, c2, ref, out, gpao_hostname, local_store_path, runner_store_path, project_name)
    tu.execute_gpao_client(tags="docker", num_thread=4)
    wait_running_job(URL_API, project_name, delay_second=1, delay_log_second=10)

    # result_by_tile_c1_file = out / "c1" / "result_by_tile.csv"
    # tu.check_df_exists_with_no_empty_data(result_by_tile_c1_file)
    # result_by_tile_c2_file = out / "c2" / "result_by_tile.csv"
    # tu.check_df_exists_with_no_empty_data(result_by_tile_c2_file)
    # result_by_metric_file = out / "result_by_metric.csv"
    # tu.check_df_exists_with_no_empty_data(result_by_metric_file)
    # result_file = out / "result.csv"
    # tu.check_df_exists_with_no_empty_data(result_file)
    # assert (out / "gpao_project.json").is_file()

    # tu.delete_projects_starting_with(project_name)  # runs only if asserts are all true


def test_compare_test1_w_weights(ensure_test1_data, use_gpao_server):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("test1/compare_w_weights")
    weights_file = Path("./test/configs/metrics_weights_test.yaml")
    gpao_hostname = "localhost"
    runner_store_path = Path("./data").resolve()
    local_store_path = Path("data").resolve()
    project_name = "coclico_test_compare_test1_w_weights"

    main.compare(c1, c2, ref, out, gpao_hostname, local_store_path, runner_store_path, project_name, weights_file)
    tu.execute_gpao_client(tags="docker", num_thread=4)
    wait_running_job(URL_API, project_name, delay_second=1, delay_log_second=10)

    # result_by_tile_c1_file = out / "c1" / "result_by_tile.csv"
    # tu.check_df_exists_with_no_empty_data(result_by_tile_c1_file)
    # result_by_tile_c2_file = out / "c2" / "result_by_tile.csv"
    # tu.check_df_exists_with_no_empty_data(result_by_tile_c2_file)
    # result_by_metric_file = out / "result_by_metric.csv"
    # result_by_metric = tu.check_df_exists_with_no_empty_data(result_by_metric_file)
    # assert set(result_by_metric["metric"]) == set(["mpap0", "mpap0_test"])
    # result_file = out / "result.csv"
    # tu.check_df_exists_with_no_empty_data(result_file)

    tu.delete_projects_starting_with(project_name)


def test_run_cli_test1(ensure_test1_data, use_gpao_server):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("test1/compare_cli")
    weights_file = Path("./test/configs/metrics_weights_test.yaml")
    gpao_hostname = "localhost"
    runner_store_path = Path("./data").resolve()
    local_store_path = runner_store_path
    project_name = "coclico_test_run_cli_test1"
    cmd = f"""python -m coclico.main \
        --c1 {str(c1)} \
        --c2 {str(c2)} \
        --ref {str(ref)} \
        --out {str(out)} \
        --weights_file {str(weights_file)} \
        --gpao_hostname {gpao_hostname} \
        --runner_store_path {runner_store_path} \
        --project_name {project_name} \
        --local_store_path {local_store_path}"""
    sp.run(cmd, shell=True, check=True)
    tu.execute_gpao_client(tags="docker", num_thread=4)
    wait_running_job(URL_API, project_name, delay_second=1, delay_log_second=10)

    tu.delete_projects_starting_with(project_name)
