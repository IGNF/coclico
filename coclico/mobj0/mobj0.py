from pathlib import Path
from typing import Dict, List

import pandas as pd
from gpao.job import Job

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
        raise NotImplementedError
