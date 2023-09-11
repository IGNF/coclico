import pytest
from coclico.mpap0 import mpap0
import shutil
from pathlib import Path
from gpao_utils.utils_store import Store
import operator as op

from test.utils import check_df_exists_with_no_empty_data


TMP_PATH = Path("./tmp/mpap0")


def setup_module():
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def test_compute_metric_relative_mpap0_toy():
    count_c1 = dict({"1": 12, "2": 20, "3,4": 2})
    count_ref = dict({"1": 10, "2": 20, "5": 2})
    score = mpap0.compute_metric_relative_mpap0(count_c1, count_ref)
    assert score == dict({"1": 2, "2": 0, "3,4": 2, "5": 2})


note_mpap0_data = [
    ({}, {}, {}),  # limit case
    (
        {"0": 0, "1": 50, "2,3": 300},  # diff c1 to ref
        {"0": 1000, "1": 1000, "2,3": 2000},  # count_ref (point per class)
        {"0": 1, "1": 0.5, "2,3": 0},  # expected score
    ),  # cases over 1000 ref points
    (
        {"0": 10, "1": 60, "2": 100, "3,4,5": 500},  # diff c1 to ref
        {"1": 100, "2": 200, "3,4,5": 100},  # count_ref (point per class)
        {"0": 1, "1": 0.5, "2": 0, "3,4,5": 0},  # expected score
    ),  # cases under 1000 ref points
]


@pytest.mark.parametrize("diff,counts_ref,expected", note_mpap0_data)
def test_compute_note_mpap0_toy(diff, counts_ref, expected):
    assert mpap0.compute_note_mpap0(diff, counts_ref) == expected


@pytest.mark.skip
def test_compare_one_tile_mpap0_test1(ensure_test1_data):
    ci = Path("./data/test1/niv1/")
    ref = Path("./data/test1/ref/")
    out = TMP_PATH / Path("test1/compare_one_tile/niv1/mpap0")
    out.mkdir(parents=True)
    tile_stem = "tile_splitted_2818_32247"
    tile_fn = f"{tile_stem}.laz"
    out_fn = f"{tile_stem}.csv"
    class_weights = {"0": 1, "1": 2, "2,3": 2}
    mpap0.compare_one_tile_mpap0(ci, ref, out, tile_fn, metric_name="mpap0_test", class_weights=class_weights)
    df = check_df_exists_with_no_empty_data(out / out_fn)
    assert set(df.columns) == set(["tile", "class", "mpap0_test"])
    assert set(df["tile"]) == set([tile_stem])


@pytest.mark.skip()
def test_create_job_one_tile_mpap0():
    ci = Path("local_store/ci")
    ref = Path("local_store/ref")
    out = Path("local_store/out")
    tile_fn = "tile_1.las"
    class_weights = dict(
        {
            "0": 1,
            "1": 1,
        }
    )
    store = Store("local_store", "win_store", "unix_store")
    metric_name = "mpap0"

    jobs = mpap0.create_job_one_tile_mpap0(ci, ref, out, tile_fn, class_weights, store, metric_name)
    assert len(jobs) == 1
    job_json = jobs[0].to_json()  # return a string
    assert op.contains(job_json, "mpap0")  # check that it is running the right method
    assert not op.contains(job_json, "local_store")  # check that the path are provided to the unix store
    assert op.contains(job_json, "unix_store")  # check that the path are provided to the unix store
