import json
import shutil
import subprocess as sp
import test.utils as tu
from pathlib import Path

import numpy as np
import pytest
from gpao_utils.gpao_test import wait_running_job
from gpao_utils.store import Store

from coclico import main
from coclico.metrics.listing import METRICS

TMP_PATH = Path("./tmp/main")

STORE = Store("local_store", "win_store", "unix_store")

URL_API = "http://localhost:8080/api/"


def setup_module():
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_read_metrics_weights_ok():
    weights_file = Path("./test/configs/metrics_weights_test.yaml")
    weights = main.read_metrics_weights(weights_file)
    assert all([k in METRICS.keys() for k in weights.keys()])
    for _, val in weights.items():
        assert isinstance(val, dict)
        assert all([isinstance(cl, str) for cl in val.keys()])


def test_read_metrics_weights_fail():
    weights_file = Path("./test/configs/metrics_weights_fail.yaml")
    with pytest.raises(ValueError):
        main.read_metrics_weights(weights_file)


def test_read_metrics_weights_different_spacing():
    weights_file = Path("./test/configs/metrics_weights_different_spacing.yaml")
    weights = main.read_metrics_weights(weights_file)
    assert all([k in METRICS.keys() for k in weights.keys()])
    expected_classes = {"1", "2", "3_4"}
    for _, val in weights.items():
        assert isinstance(val, dict)
        assert all([cl in expected_classes for cl in val.keys()])


def test_create_compare_project_error():
    # C1 and C2 ends with the same name, should raise RuntimeError
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    c3 = Path("./same/name/niv1/")

    ref = Path("./data/test1/ref/")
    out = TMP_PATH / "create_compare_project_error"
    project_name = "test_create_compare_projects_errors"
    metrics_weights = {"mpap0": {"0": 1, "2": 2}}

    with pytest.raises(ValueError):
        main.create_compare_project([c1, c2, c3], ref, out, STORE, project_name, metrics_weights)


def test_create_compare_project(ensure_test1_data):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / "create_compare_project"
    project_name = "coclico_test_create_compare_projects"
    metrics_weights = {"mpap0": {"0": 1, "1_2": 2}, "mpla0": {"0": 1, "3_4": 2}, "malt0": {"6": 2, "0": 1}}

    project = main.create_compare_project([c1, c2], ref, out, STORE, project_name, metrics_weights)

    assert project is not None
    project_json = json.loads(project.to_json())
    assert len(project_json["jobs"]) > 0  # No empty projects
    assert project_json["name"].startswith(project_name)


def test_create_compare_project_existing_ref(ensure_test1_data):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / "create_compare_project_existing_ref"

    project_name = "test_create_compare_projects_existing_ref"
    metrics_weights = {"mpap0": {"0": 1, "2": 2}}

    project = main.create_compare_project([c1, c2], ref, out, STORE, project_name, metrics_weights)

    assert np.sum([job.name.startswith("mpap0_intrinsic_ref") for job in project.jobs]) == 4

    shutil.rmtree(out / "niv1")
    shutil.rmtree(out / "niv4")

    project = main.create_compare_project([c1, c2], ref, out, STORE, project_name, metrics_weights)

    assert np.sum([job.name.startswith("mpap0_intrinsic_ref") for job in project.jobs]) == 0


def test_create_compare_project_existing_c2(ensure_test1_data):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / "create_compare_project_existing_c2"

    project_name = "test_create_compare_projects_existing_c2"
    metrics_weights = {"mpap0": {"0": 1, "2": 2}}

    project = main.create_compare_project([c1, c2], ref, out, STORE, project_name, metrics_weights)

    assert np.sum([job.name.startswith("mpap0_intrinsic_niv4") for job in project.jobs]) == 4
    assert np.sum([job.name.startswith("mpap0_niv4_relative_to_ref") for job in project.jobs]) == 1

    shutil.rmtree(out / "niv1")
    shutil.rmtree(out / "ref")

    project = main.create_compare_project([c1, c2], ref, out, STORE, project_name, metrics_weights)

    assert np.sum([job.name.startswith("mpap0_intrinsic_niv4") for job in project.jobs]) == 0
    assert np.sum([job.name.startswith("mpap0_niv4_relative_to_ref") for job in project.jobs]) == 0


def test_create_compare_project_unlock(ensure_test1_data):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / "create_compare_project_unlock"
    project_name = "coclico_test_create_compare_projects_unlock"
    metrics_weights = {"mpap0": {"0": 1, "1-2": 2}, "mpla0": {"0": 1, "1-2": 2}}

    project = main.create_compare_project([c1, c2], ref, out, STORE, project_name, metrics_weights, unlock=False)

    assert all(["unlock" not in job.name for job in project.jobs])  # No unlock job

    shutil.rmtree(out)

    project = main.create_compare_project([c1, c2], ref, out, STORE, project_name, metrics_weights, unlock=True)
    assert np.sum([job.name.endswith("_unlock") for job in project.jobs]) == 3


@pytest.mark.gpao
def test_compare_test1_default(ensure_test1_data, use_gpao_server):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("compare_test1_default")
    gpao_hostname = "localhost"
    runner_store_path = Path("./data").resolve()
    local_store_path = Path("data").resolve()
    project_name = "coclico_test_compare_test1_default"

    main.compare([c1, c2], ref, out, gpao_hostname, local_store_path, runner_store_path, project_name)
    tu.execute_gpao_client(tags="docker", num_thread=4)
    wait_running_job(URL_API, project_name, delay_second=1, delay_log_second=10)

    expected_classes_weights = {"mpap0": 7, "mpla0": 5, "malt0": 3}

    for metric, nb_classes_weights in expected_classes_weights.items():
        c1_to_ref_tile = out / "niv1" / metric / "to_ref" / "result_tile.csv"
        assert tu.csv_num_rows(c1_to_ref_tile) == 4 * nb_classes_weights  # 4 files * classes_weights

        c1_to_ref = out / "niv1" / metric / "to_ref" / "result.csv"
        assert tu.csv_num_rows(c1_to_ref) == nb_classes_weights

    c1_all_metrics = out / "niv1" / "niv1_result.csv"
    assert tu.csv_num_rows(c1_all_metrics) == 8  # 8 classes in total (1, 2, "3_4_5", "4_5", 6, 9, 17, 64)
    assert tu.csv_num_col(c1_all_metrics) == 4  # class, mpap0, mpla0, malt0

    all_scores = out / "result.csv"
    assert tu.csv_num_rows(all_scores) == 2  # niv1, niv4

    tu.delete_projects_starting_with(project_name)  # runs only if asserts are all true


@pytest.mark.gpao
def test_compare_test1_weights(ensure_test1_data, use_gpao_server):
    niv1 = Path("./data/test1/niv1/")
    niv2 = Path("./data/test1/niv2/")
    niv4 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("compare_test1_weights")
    weights_file = Path("./test/configs/metrics_weights_test.yaml")
    gpao_hostname = "localhost"
    runner_store_path = Path("./data").resolve()
    local_store_path = Path("data").resolve()
    project_name = "coclico_test_compare_test1_w_weights"

    main.compare(
        [niv1, niv2, niv4], ref, out, gpao_hostname, local_store_path, runner_store_path, project_name, weights_file
    )
    tu.execute_gpao_client(tags="docker", num_thread=4)
    wait_running_job(URL_API, project_name, delay_second=1, delay_log_second=10)

    c1_to_ref_tile = out / "niv1" / "mpap0" / "to_ref" / "result_tile.csv"
    assert tu.csv_num_rows(c1_to_ref_tile) == 4 * 3  # 4 files * 3 classes_weights
    c1_to_ref = out / "niv1" / "mpap0" / "to_ref" / "result.csv"
    assert tu.csv_num_rows(c1_to_ref) == 3  # 3 classes_weights

    c2_to_ref_tile = out / "niv4" / "mpap0" / "to_ref" / "result_tile.csv"
    assert tu.csv_num_rows(c2_to_ref_tile) == 4 * 3  # 4 files * 3 classes_weights
    c2_to_ref = out / "niv4" / "mpap0" / "to_ref" / "result.csv"
    assert tu.csv_num_rows(c2_to_ref) == 3  # 3 classes_weights

    c1_all_metrics = out / "niv1" / "niv1_result.csv"
    assert tu.csv_num_rows(c1_all_metrics) == 4  # 4 classes_weights (one differs between mpap0, mpla0 and malt0)
    assert tu.csv_num_col(c1_all_metrics) == 4  # class, mpap0, mpla0, malt0

    all_scores = out / "result.csv"
    assert tu.csv_num_rows(all_scores) == 3  # 3 classif (niv1 niv2 niv4)

    tu.delete_projects_starting_with(project_name)


@pytest.mark.gpao
def test_run_main_test1(ensure_test1_data, use_gpao_server):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("run_main_test1")
    weights_file = Path("./test/configs/metrics_weights_test.yaml")
    gpao_hostname = "localhost"
    runner_store_path = Path("./data").resolve()
    local_store_path = runner_store_path
    project_name = "coclico_test_run_main_test1"
    cmd = f"""python -m coclico.main \
        -i {str(c1)} {str(c2)} \
        --ref {str(ref)} \
        --out {str(out)} \
        --weights-file {str(weights_file)} \
        --gpao-hostname {gpao_hostname} \
        --runner-store-path {runner_store_path} \
        --project-name {project_name} \
        --local-store-path {local_store_path}"""
    sp.run(cmd, shell=True, check=True)
    tu.execute_gpao_client(tags="docker", num_thread=4)
    wait_running_job(URL_API, project_name, delay_second=1, delay_log_second=10)

    tu.delete_projects_starting_with(project_name)


@pytest.mark.gpao
def test_run_main_test1_unlock(ensure_test1_data, use_gpao_server):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("run_main_test1_unlock")
    weights_file = Path("./test/configs/metrics_weights_test.yaml")
    gpao_hostname = "localhost"
    runner_store_path = Path("./data").resolve()
    local_store_path = runner_store_path
    project_name = "coclico_test_run_main_test1_unlock"
    cmd = f"""python -m coclico.main \
        -i {str(c1)} {str(c2)} \
        --ref {str(ref)} \
        --out {str(out)} \
        --weights-file {str(weights_file)} \
        --gpao-hostname {gpao_hostname} \
        --runner-store-path {runner_store_path} \
        --project-name {project_name} \
        --local-store-path {local_store_path} \
        --unlock"""
    sp.run(cmd, shell=True, check=True)
    tu.execute_gpao_client(tags="docker", num_thread=4)
    wait_running_job(URL_API, project_name, delay_second=1, delay_log_second=10)

    tu.delete_projects_starting_with(project_name)
