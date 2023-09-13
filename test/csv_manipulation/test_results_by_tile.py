import pandas as pd
from typing import Callable, List
import coclico.csv_manipulation.results_by_tile
from test.utils import check_df_exists_with_no_empty_data
import subprocess as sp
import shutil
from gpao_utils.utils_store import Store
import json

from pathlib import Path


TMP_PATH = Path("./tmp/csv_merging/results_by_tile")


def setup_module():
    if TMP_PATH.is_dir():
        shutil.rmtree(TMP_PATH)


def generate_csv_result(
    out: Path,
    tiles: List[str] = ["tile1", "tile2"],
    metrics: List[str] = ["metric1", "metric2"],
    classes: List[str] = [0, 1],
    results_fn: Callable = (lambda ii: ii),
):
    """Generate a toy csv file containing fake tile by tile results for provided tiles, metrics, classes
    using results_fn to generate the result for each [tile, metric, class] from its creation index
    This method aims to mimick coclico.main.compare_to_ref results

    Args:
        out (Path): path to the output csv file
        tiles (List[str], optional): tiles names for which to generate results. Defaults to ["tile1", "tile2"].
        metrics (List[str], optional): metrics for which to generate results. Defaults to ["metric1", "metric2"].
        classes (List[str], optional): classes for which to generate results. Defaults to ["0", "1"].
        results_fn (_type_, optional): function to use to generate values from the creation index.
        Defaults to (lambda ii: ii).
    """
    out.mkdir(parents=True, exist_ok=True)
    for metric in metrics:
        out_metric = out / metric / "to_ref"
        out_metric.mkdir(parents=True)
        ii = 0
        results_list = []
        for tile in tiles:
            for cl in classes:
                result_dict = {"tile": tile, "class": cl}
                result_dict[metric] = results_fn(ii)
                ii += 1
                results_list.append(result_dict)

        df = pd.DataFrame(results_list)
        df.to_csv(out_metric / "result_tile.csv", index=False)

        results_list = []
        for cl in classes:
            result_dict = {"class": cl}
            result_dict[metric] = results_fn(ii)
            ii += 1
            results_list.append(result_dict)

        df = pd.DataFrame(results_list)
        df.to_csv(out_metric / "result.csv", index=False)


def test_merge_results_for_one_classif():
    metrics = ["m1", "m2", "m3"]
    classes = [0, 1]
    tiles = ["tile1", "tile2"]
    base_path = TMP_PATH / Path("toy_results/results_by_tile")
    out = base_path / "result.csv"
    # out_tile = base_path / "result_tile.csv"
    out = base_path / "result.csv"
    generate_csv_result(base_path, tiles, metrics, classes, (lambda ii: 2 * ii))

    coclico.csv_manipulation.results_by_tile.merge_results_for_one_classif(base_path, out)

    df = check_df_exists_with_no_empty_data(out)
    assert set(df.columns) == set(["class"] + metrics)
    # assert len(df.index) == len(tiles) * len(classes)
    # assert set(df["tile"]) == set(tiles)
    # assert not df.isnull().values.any()

    # block used to test tile result
    # df = check_df_exists_with_no_empty_data(out_tile)
    # assert set(df.columns) == set(["tile", "class"] + metrics)
    # assert len(df.index) == len(tiles) * len(classes)
    # assert set(df["tile"]) == set(tiles)
    # assert not df.isnull().values.any()

    # df = check_df_exists_with_no_empty_data(out)
    # nb_classes = 2
    #
    # assert len(df.index) == nb_classes * len(tiles)


def test_run_main():
    metrics = ["m1", "m2", "m3"]
    classes = [0, 1]
    tiles = ["tile1", "tile2"]
    base_path = TMP_PATH / Path("toy_results/results_by_tile_cli")
    out = base_path / "result_by_tile.csv"

    generate_csv_result(base_path, tiles, metrics, classes, (lambda ii: 2 * ii))

    cmd = f"""python -m coclico.csv_manipulation.results_by_tile \
    --metrics_root_folder {base_path} \
    --output_path {out}
    """

    sp.run(cmd, shell=True, check=True)


def test_create_job_merge_tile_results():
    out = Path("local_store/out")
    metrics_root_folder = Path("local_store/input")
    store = Store("local_store", "win_store", "unix_store")

    job = coclico.csv_manipulation.results_by_tile.create_job_merge_results(metrics_root_folder, out, store)
    job_json = json.loads(job.to_json())  # return a string
    assert job_json["name"].startswith("merge_tiles")  # check that it is running the right method
