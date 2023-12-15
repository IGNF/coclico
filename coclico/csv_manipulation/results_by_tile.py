import argparse
import logging
from pathlib import Path, PurePosixPath
from typing import List

import pandas as pd
from gpao.job import Job
from gpao_utils.store import Store

import coclico.io as io
from coclico.config import csv_separator
from coclico.metrics.listing import METRICS
from coclico.version import __version__


def merge_results_for_one_classif(metrics_root_folder: Path, output_path: Path, config_file: Path):
    """Merge all individual csv results for the comparison of one classification to the reference

    From a root folder containing:
    - one subfolder for each metric
    - in this subfolder, one csv file for each tile with results for all classes on this metric/tile

    Args:
        metrics_root_folder (Path): root folder
        output_path (Path): Path to the output csv file
        config_file (Path): Coclico configuration file
    """
    config_dict = io.read_config_file(config_file)

    merged_df = pd.DataFrame(columns=["class"])
    merged_df_tile = pd.DataFrame(columns=["tile", "class"])

    for metric_name, metric_class in METRICS.items():
        if metric_name in config_dict.keys():
            metric_folder = metrics_root_folder / metric_name
            notes_config = config_dict[metric_name]["notes"]
            metric_df_tile = pd.read_csv(
                metric_folder / "to_ref" / "result_tile.csv", dtype={"class": str}, sep=csv_separator
            )
            metric_df_tile = metric_class.compute_note(metric_df_tile, notes_config)

            merged_df_tile = merged_df_tile.merge(metric_df_tile, on=["tile", "class"], how="outer")
            print(merged_df_tile)

            metric_df = pd.read_csv(metric_folder / "to_ref" / "result.csv", dtype={"class": str}, sep=csv_separator)
            metric_df = metric_class.compute_note(metric_df, notes_config)
            merged_df = merged_df.merge(metric_df, on=["class"], how="outer")

        output_path.parent.mkdir(exist_ok=True, parents=True)
        merged_df_tile.to_csv(output_path.parent / (output_path.stem + "_tile.csv"), index=False, sep=csv_separator)
        merged_df.to_csv(output_path, index=False, sep=csv_separator)
        logging.debug(merged_df.to_markdown())


def create_job_merge_results(
    metrics_root_folder: Path, out: Path, store: Store, config_file: Path, deps: List[Job] = None
) -> Job:
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
    -v {store.to_unix(config_file.parent)}:/config
    ignimagelidar/coclico:{__version__}
    python -m coclico.csv_manipulation.results_by_tile
    --metrics-root-folder /input
    --output-path {PurePosixPath("/out") / out.name}
    --config-file {PurePosixPath("/config") / config_file.name}
    """
    job = Job(f"merge_tiles_{out.name.split('.')[0]}", command, tags=["docker"], deps=deps)

    return job


def parse_args():
    parser = argparse.ArgumentParser("Merge CSV result")
    parser.add_argument(
        "--metrics-root-folder",
        "-m",
        type=Path,
        required=True,
        help="Path to the root folder of the csv files generated for each metric + tile",
    )
    parser.add_argument("--output-path", "-o", type=Path, required=True, help="Path to output csv file")
    parser.add_argument("--config-file", "-w", type=Path, help="Coclico configuration file")

    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    args = parse_args()
    merge_results_for_one_classif(args.metrics_root_folder, args.output_path, args.config_file)
