from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from gpao.job import Job

from coclico.metrics.commons import bounded_affine_function
from coclico.metrics.metric import Metric


class MOBJ0(Metric):
    """Metric MOBJ0 (for "Métrique par objet 0")
    TODO Description
    See doc/mobj0.md
    """

    # Pixel size for occupancy map
    pixel_size = 0.5
    metric_name = "mobj0"

    def create_metric_intrinsic_one_job(self, name: str, input: Path, output: Path, is_ref: bool):
        raise NotImplementedError

    def create_metric_relative_to_ref_jobs(
        self, name: str, out_c1: Path, out_ref: Path, output: Path, c1_jobs: List[Job], ref_jobs: List[Job]
    ) -> Job:
        raise NotImplementedError

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
