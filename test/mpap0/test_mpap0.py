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
