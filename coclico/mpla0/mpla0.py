import json
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from gpao.job import Job

from coclico.metrics.commons import bounded_affine_function
from coclico.metrics.metric import Metric
from coclico.version import __version__


class MPLA0(Metric):
    """Metric MPLA0 (for "Métrique planimetric 0")
    Comparison of 2d classification maps (occupancy maps) for each class between the classification and the
    reference

    - metric_intrinsic:
        for each input file, generate a tif file with one layer by class in the class_weight dictionary
        for each class, the corresponding layer contains a kind of 2d occupancy map for the class (ie. if any point
        of this class belongs to the pixel, the pixel has a value of 1, the value is 0 everywhere else)

        The layers are sorted alphabetically using their class name from their class_weights dict in order to have a
        repeatable order

    - metric extrinsic: compute intersection and union of the classification maps

    - note:
        * if reference data has more than 1000 points: affine function on the intersection over union for each class
        * otherwise: affine function on {union - intersection}
    """

    # Pixel size for the intermediate result: 2d binary maps for each class
    map_pixel_size = 0.5
    metric_name = "mpla0"

    def create_metric_intrinsic_one_job(self, name: str, input: Path, output: Path, is_ref: bool = False):
        job_name = f"{self.metric_name}_intrinsic_{name}_{input.stem}"

        command = f"""
docker run -t --rm --userns=host --shm-size=2gb
-v {self.store.to_unix(input)}:/input
-v {self.store.to_unix(output)}:/output
ignimagelidar/coclico:{__version__}
python -m coclico.mpla0.mpla0_intrinsic
--input-file /input
--output-file /output/{input.stem}.tif
--class-weights '{json.dumps(self.class_weights)}'
--pixel-size {self.map_pixel_size}
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
ignimagelidar/coclico:{__version__}
python -m coclico.mpla0.mpla0_relative
--input-dir /input
--ref-dir /ref
--output-csv-tile /output/result_tile.csv
--output-csv /output/result.csv
--class-weights '{json.dumps(self.class_weights)}'
"""

        job = Job(job_name, command, tags=["docker"])
        for c1_job in c1_jobs:
            job.add_dependency(c1_job)
        for ref_job in ref_jobs:
            job.add_dependency(ref_job)

        return [job]

    @staticmethod
    def compute_note(metric_df: pd.DataFrame):
        """Compute mpla0 note from mpla0_relative results.
        This method expects a pandas dataframe with columns:
            - intersection
            - union
            - ref_pixel_count
        (these columns are described in the mpla0_relative function docstring)

        Args:
            metric_df (pd.DataFrame): mpla0 relative results as a pandas dataframe

        Returns:
            metric_df: the updated metric_df input with notes instead of metrics
        """

        metric_df[MPLA0.metric_name] = np.where(
            metric_df["ref_pixel_count"] >= 1000,
            bounded_affine_function((0.9, 0), (1, 1), metric_df["intersection"] / metric_df["union"]),
            bounded_affine_function((20, 1), (100, 0), metric_df["union"] - metric_df["intersection"]),
        )

        metric_df.drop(columns=["ref_pixel_count", "intersection", "union"], inplace=True)

        return metric_df
