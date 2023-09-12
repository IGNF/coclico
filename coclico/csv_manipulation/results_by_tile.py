import pandas as pd
import argparse

from pathlib import Path, PurePosixPath
from gpao.job import Job
from gpao_utils.utils_store import Store
from coclico._version import __version__
import logging
from typing import List


def merge_results_for_one_classif(metrics_root_folder: Path, output_path: Path):
    """Merge all individual csv results for the comparison of one classification to the reference

    From a root folder containing:
    - one subfolder for each metric
    - in this subfolder, one csv file for each tile with results for all classes on this metric/tile

    Args:
        metrics_root_folder (Path): root folder
        output_path (Path): Path to the output csv file
    """
    metric_folders = [f for f in metrics_root_folder.iterdir() if f.is_dir()]
    merged_df = pd.DataFrame(columns=["class"])
    merged_df_tile = pd.DataFrame(columns=["tile", "class"])
    for folder in metric_folders:
        metric_df_tile = pd.concat([pd.read_csv(folder / "to_ref" / "result_tile.csv", dtype={"class": str})])
        merged_df_tile = merged_df_tile.merge(metric_df_tile, on=["tile", "class"], how="right")

        metric_df = pd.concat([pd.read_csv(folder / "to_ref" / "result.csv", dtype={"class": str})])
        merged_df = merged_df.merge(metric_df, on=["class"], how="right")

    merged_df_tile.to_csv(output_path.parent / (output_path.stem + "_tile.csv"), index=False)
    merged_df.to_csv(output_path, index=False)
    logging.debug(merged_df.to_markdown())


def create_job_merge_results(metrics_root_folder: Path, out: Path, store: Store, deps: List[Job] = None) -> Job:
    """Create gpao job to merge tile results for one classification

    Args:
        metrics_root_folder (Path): _description_
        out (Path): _description_
        store (Store): _description_
        deps (List[Job]): jobs dependencies

    Returns:
        List[Job]: _description_
    """
    command = f"""
    docker run -t --rm --userns=host --shm-size=2gb
    -v {store.to_unix(metrics_root_folder)}:/input
    -v {store.to_unix(out.parent)}:/out
    lidar_hd/coclico:{__version__}
    python -m coclico.csv_manipulation.results_by_tile
    --metrics_root_folder /input
    --out {PurePosixPath("/out") / out.name}
    """
    job = Job(f"merge_tiles_{out.name.split('.')[0]}", command, tags=["docker"], deps=deps)

    return job


def parse_args():
    parser = argparse.ArgumentParser("Merge CSV result")
    parser.add_argument(
        "--metrics_root_folder",
        "-m",
        type=Path,
        required=True,
        help="Path to the root folder of the csv files generated for each metric + tile",
    )
    parser.add_argument("--output_path", type=Path, required=True, help="Path to output csv file")

    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    args = parse_args()
    merge_results_for_one_classif(args.metrics_root_folder, args.output_path)
