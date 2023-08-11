import pandas as pd
import argparse

from pathlib import Path, PurePosixPath
from gpao.job import Job
from gpao_utils.utils_store import Store
from coclico._version import __version__


def merge_tile_results_for_one_classif(metrics_root_folder: Path, output_path: Path):
    """Merge all individual csv results for the comparison of one classification to the reference

    From a root folder containing:
    - one subfolder for each metric
    - in this subfolder, one csv file for each tile with results for all classes on this metric/tile

    Args:
        metrics_root_folder (Path): root folder
        output_path (Path): Path to the output csv file
    """
    metric_folders = [f for f in metrics_root_folder.iterdir() if f.is_dir()]
    merged_df = pd.DataFrame(columns=["tile", "class"])
    for folder in metric_folders:
        metric_df = pd.concat(
            [pd.read_csv(f, dtype={"class": str}) for f in folder.iterdir() if f.name.endswith("csv")]
        )
        merged_df = merged_df.merge(metric_df, on=["tile", "class"], how="right")

    merged_df.to_csv(output_path, index=False)


def create_job_merge_tile_results(metrics_root_folder: Path, out: Path, store: Store) -> Job:
    """Create gpao job to merge tile results for one classification

    Args:
        metrics_root_folder (Path): _description_
        out (Path): _description_
        store (_type_): _description_

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
    job = Job(f"merge_tiles_{out.name.split('.')[0]}", command, tags=["docker"])

    return job


def parse_args():
    parser = argparse.ArgumentParser("Run mpap0 metric on one tile")
    parser.add_argument(
        "--metrics_root_folder",
        "-m",
        type=Path,
        help="Path to the root folder of the csv files generated for each metric + tile",
    )
    parser.add_argument("--output_path", type=Path, help="Path to output csv file")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    merge_tile_results_for_one_classif(args.metrics_root_folder, args.output_path)
