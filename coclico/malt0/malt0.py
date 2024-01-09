from pathlib import Path
from typing import Dict, List

import pandas as pd
from gpao.job import Job

from coclico.metrics.commons import bounded_affine_function
from coclico.metrics.metric import Metric
from coclico.version import __version__


class MALT0(Metric):
    """Metric MALT0 (for "Métrique altimétrique 0")
    Comparison of 2d height maps (digital surface model for one class only) for each class between the
    classification and the reference. The comparison is done only for the pixels of the map that contain
    points in the reference tile (based on an occupancy map similar to the one used in MPLA0).

    See doc/malt0.md
    """

    # Pixel size for MNx
    pixel_size = 0.5
    metric_name = "malt0"

    def create_metric_intrinsic_one_job(self, name: str, input: Path, output: Path, is_ref: bool):
        job_name = f"{self.metric_name}_intrinsic_{name}_{input.stem}"
        occupancy_map_arg = ""
        mnx_out = output / "mnx"
        mnx_out.mkdir(exist_ok=True, parents=True)
        if is_ref:
            occ_out = output / "occupancy"
            occ_out.mkdir(exist_ok=True, parents=True)
            occupancy_map_arg = f"--output-occupancy-file /output/occupancy/{input.stem}.tif"

        command = f"""
docker run -t --rm --userns=host --shm-size=2gb
-v {self.store.to_unix(input)}:/input
-v {self.store.to_unix(output)}:/output
-v {self.store.to_unix(self.config_file.parent)}:/config
ignimagelidar/coclico:{__version__}
python -m coclico.malt0.malt0_intrinsic
--input-file /input
--output-mnx-file /output/mnx/{input.stem}.tif
{occupancy_map_arg}
--config-file /config/{self.config_file.name}
--pixel-size {self.pixel_size}

"""

        job = Job(job_name, command, tags=["docker"])
        return job

    def create_metric_relative_to_ref_jobs(
        self, name: str, out_c1: Path, out_ref: Path, output: Path, c1_jobs: List[Job], ref_jobs: List[Job]
    ) -> Job:
        job_name = f"{self.metric_name}_{name}_relative_to_ref"
        command = f"""
docker run -t --rm --userns=host --shm-size=2gb
-v {self.store.to_unix(out_c1) / "mnx"}:/input
-v {self.store.to_unix(out_ref) / "mnx"}:/ref
-v {self.store.to_unix(out_ref) / "occupancy"}:/occupancy
-v {self.store.to_unix(output)}:/output
-v {self.store.to_unix(self.config_file.parent)}:/config
ignimagelidar/coclico:{__version__}
python -m coclico.malt0.malt0_relative
--input-dir /input
--ref-dir /ref
--occupancy-dir /occupancy
--output-csv-tile /output/result_tile.csv
--output-csv /output/result.csv
--config-file /config/{self.config_file.name}
"""

        job = Job(job_name, command, tags=["docker"])
        for c1_job in c1_jobs:
            job.add_dependency(c1_job)
        for ref_job in ref_jobs:
            job.add_dependency(ref_job)

        return [job]

    @staticmethod
    def compute_note(metric_df: pd.DataFrame, note_config: Dict):
        """Compute malt0 note from malt0_relative results.
        This method expects a pandas dataframe with columns:
            - max_diff
            - mean_diff
            - std_diff
        (these columns are described in the malt0_relative function docstring)

        Args:
            metric_df (pd.DataFrame): malt0 relative results as a pandas dataframe

        Returns:
            metric_df: the updated metric_df input with notes instead of metrics
        """
        max_note = bounded_affine_function(
            (note_config["max_diff"]["min_point"]["metric"], note_config["max_diff"]["min_point"]["note"]),
            (note_config["max_diff"]["max_point"]["metric"], note_config["max_diff"]["max_point"]["note"]),
            metric_df["max_diff"],
        )  # 0 <= max_note <= 1
        mean_note = bounded_affine_function(
            (note_config["mean_diff"]["min_point"]["metric"], note_config["mean_diff"]["min_point"]["note"]),
            (note_config["mean_diff"]["max_point"]["metric"], note_config["mean_diff"]["max_point"]["note"]),
            metric_df["mean_diff"],
        )  # 0 <= mean_note <= 1
        std_note = bounded_affine_function(
            (note_config["std_diff"]["min_point"]["metric"], note_config["mean_diff"]["min_point"]["note"]),
            (note_config["std_diff"]["max_point"]["metric"], note_config["mean_diff"]["max_point"]["note"]),
            metric_df["std_diff"],
        )  # 0 <= std_note <= 1

        sum_coefs = (
            note_config["max_diff"]["coefficient"]
            + note_config["mean_diff"]["coefficient"]
            + note_config["std_diff"]["coefficient"]
        )
        metric_df[MALT0.metric_name] = (
            note_config["max_diff"]["coefficient"] * max_note
            + note_config["mean_diff"]["coefficient"] * mean_note
            + note_config["std_diff"]["coefficient"] * std_note
        ) / sum_coefs

        metric_df.drop(columns=["max_diff", "mean_diff", "std_diff"], inplace=True)

        return metric_df
