from coclico import main
from pathlib import Path
import shutil
import pytest
import subprocess as sp

from test.utils import check_df_exists_with_no_empty_data


TMP_PATH = Path("./tmp/main")


def setup_module():
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_compare_to_ref_test1(ensure_test1_data):
    c1 = Path("./data/test1/niv1/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("test1/niv1/compare_to_ref.csv")
    metrics_weights = {"mpap0": {0: 1, 1: 2}, "mpap0_test": {0: 1, 1: 2}}
    out.parent.mkdir(parents=True, exist_ok=True)
    nb_classes = 2
    tiles = [f.stem for f in ref.iterdir() if f.name.lower().endswith(("las", "laz"))]

    main.compare_to_ref(c1, ref, out, metrics_weights)
    df = check_df_exists_with_no_empty_data(out)
    assert set(df.columns) == set(["tile", "class"] + [k for k in metrics_weights.keys()])
    assert set(df["tile"]) == set(tiles)
    assert len(df.index) == nb_classes * len(tiles)


def test_compare_test1_default(ensure_test1_data):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("test1/compare")

    main.compare(c1, c2, ref, out)

    result_by_tile_c1_file = out / "c1" / "result_by_tile.csv"
    check_df_exists_with_no_empty_data(result_by_tile_c1_file)
    result_by_tile_c2_file = out / "c2" / "result_by_tile.csv"
    check_df_exists_with_no_empty_data(result_by_tile_c2_file)
    result_by_metric_file = out / "result_by_metric.csv"
    check_df_exists_with_no_empty_data(result_by_metric_file)
    result_file = out / "result.csv"
    check_df_exists_with_no_empty_data(result_file)


def test_compare_test1_w_weights(ensure_test1_data):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("test1/compare_w_weights")
    weights_file = Path("./test/configs/metrics_weights_test.yaml")

    main.compare(c1, c2, ref, out, weights_file)

    result_by_tile_c1_file = out / "c1" / "result_by_tile.csv"
    check_df_exists_with_no_empty_data(result_by_tile_c1_file)
    result_by_tile_c2_file = out / "c2" / "result_by_tile.csv"
    check_df_exists_with_no_empty_data(result_by_tile_c2_file)
    result_by_metric_file = out / "result_by_metric.csv"
    result_by_metric = check_df_exists_with_no_empty_data(result_by_metric_file)
    assert set(result_by_metric["metric"]) == set(["mpap0", "mpap0_test"])
    result_file = out / "result.csv"
    check_df_exists_with_no_empty_data(result_file)


def test_compare_test1_fail(ensure_test1_data):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("test1/compare_fail")
    weights_file = Path("./test/configs/metrics_weights_fail.yaml")
    with pytest.raises(ValueError):
        main.compare(c1, c2, ref, out, weights_file)


def test_run_cli_test1(ensure_test1_data):
    c1 = Path("./data/test1/niv1/")
    c2 = Path("./data/test1/niv4/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("test1/compare_cli")
    weights_file = Path("./test/configs/metrics_weights_test.yaml")
    cmd = f"""python -m coclico.main \
        --c1 {str(c1)} \
        --c2 {str(c2)} \
        --ref {str(ref)} \
        --out {str(out)} \
        --weights_file {str(weights_file)}"""
    sp.run(cmd, shell=True, check=True)
