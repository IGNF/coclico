from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from gpao.job import Job

from coclico.metrics.commons import bounded_affine_function
from coclico.metrics.metric import Metric
from coclico.version import __version__


class MOBJ0(Metric):
    """Metric MOBJ0 (for "Métrique par objet 0")
    Comparison of detected objects (distinct blobs in the occupancy map) each class between the classification and the
    reference

    See doc/mobj0.md
    """

    metric_name = "mobj0"
    pixel_size = 0.5  # Pixel size for occupancy map
    kernel = 3  # parameter for morphological operations on rasters
    tolerance_shp = 0.05  # parameter for simplification on geometries of the shapefile

    def create_metric_intrinsic_one_job(self, name: str, input: Path, output: Path):
        job_name = f"{self.metric_name}_intrinsic_{name}_{input.stem}"
        command = f"""
docker run -t --rm --userns=host --shm-size=2gb
-v {self.store.to_unix(input)}:/input
-v {self.store.to_unix(output)}:/output
-v {self.store.to_unix(self.config_file.parent)}:/config
ignimagelidar/coclico:{__version__}
python -m coclico.mobj0.mobj0_intrinsic \
--input-file /input \
--output-geojson /output/{input.stem}.json \
--config-file /config/{self.config_file.name} \
--pixel-size {self.pixel_size} \
--kernel {self.kernel} \
--tolerance-shp {self.tolerance_shp}
"""
        job = Job(job_name, command, tags=["docker"])
        return job

    def create_metric_relative_to_ref_jobs(
        self, name: str, out_c1: Path, out_ref: Path, output: Path, c1_jobs: List[Job], ref_jobs: List[Job]
    ) -> Job:
        job_name = f"{self.metric_name}_{name}_relative_to_ref"
        command = f"""
docker run -t --rm --userns=host --shm-size=2gb
-v {self.store.to_unix(out_c1)}:/input
-v {self.store.to_unix(out_ref)}:/ref
-v {self.store.to_unix(output)}:/output
-v {self.store.to_unix(self.config_file.parent)}:/config
ignimagelidar/coclico:{__version__}
python -m coclico.mobj0.mobj0_relative \
--input-dir /input
--ref-dir /ref
--output-csv-tile /output/result_tile.csv \
--output-csv /output/result.csv \
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
        """Compute mobj0 note from mobj0_relative results.
        This method expects a pandas dataframe with columns:
            - ref_object_count
            - paired_count
            - not_paired_count
        (these columns are described in the mobj0_relative function docstring)

        Args:
            metric_df (pd.DataFrame): mobj0 relative results as a pandas dataframe

        Returns:
            metric_df: the updated metric_df input with notes instead of metrics
        """

        metric_df[MOBJ0.metric_name] = np.where(
            metric_df["ref_object_count"] >= note_config["ref_object_count_threshold"],
            bounded_affine_function(
                (
                    note_config["above_threshold"]["min_point"]["metric"],
                    note_config["above_threshold"]["min_point"]["note"],
                ),
                (
                    note_config["above_threshold"]["max_point"]["metric"],
                    note_config["above_threshold"]["max_point"]["note"],
                ),
                metric_df["paired_count"] / (metric_df["paired_count"] + metric_df["not_paired_count"]),
            ),
            bounded_affine_function(
                (
                    note_config["under_threshold"]["min_point"]["metric"],
                    note_config["under_threshold"]["min_point"]["note"],
                ),
                (
                    note_config["under_threshold"]["max_point"]["metric"],
                    note_config["under_threshold"]["max_point"]["note"],
                ),
                metric_df["not_paired_count"],
            ),
        )

        metric_df.drop(columns=["ref_object_count", "paired_count", "not_paired_count"], inplace=True)

        return metric_df
