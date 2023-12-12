from pathlib import Path
from typing import Dict, List

import pandas as pd
from gpao.job import Job
from gpao_utils.store import Store


class Metric:
    """Base class for metrics"""

    def __init__(self, store: Store, class_weights: Dict):
        """Initialize Metric object

        Args:
            store (Store): Store object (as defined in gpao_utils) to handle mount points of distant stores on various
            computers
            class_weights (Dict): Dictionnary of the weights of the metric for each class (cf. config file)
        """
        self.store = store
        self.class_weights = class_weights

    def create_metric_intrinsic_jobs(
        self, name: str, tile_names: List[str], input_path: Path, out_path: Path, is_ref: bool
    ) -> List[Job]:
        """Create jobs for a single classified point cloud folder (eg. ref, c1 or c2)
        These jobs are aimed to compute intermediate results on the input las that will be used in
        `create_metric_relative_to_ref_jobs` to compute the relative metric
        Args:
            name (str): classification name (used for job name creation)
            tile_names (List[str]): list of the filenames of the tiles on which to calculate the result
            input_path (Path): input folder path (path to the results of the classification)
            out_path (Path): path for the intermediate results to be saved
            is_ref (bool): flag that says if the input classification folder is the reference folder
        Returns:
            List[Job]: List of GPAO jobs to create
        """
        return [self.create_metric_intrinsic_one_job(name, input_path / f, out_path, is_ref) for f in tile_names]

    def create_metric_intrinsic_one_job(self, name: str, input: Path, output: Path, is_ref: bool) -> Job:
        """Create a job to compute the intrinsic metric for a single point cloud file.

        Args:
            name (str): classification name (used for job name creation)
            input (Path): full path of the input tile
            output (Path): output folder for the result
            is_ref (bool):  flag that says if the input classification folder is the reference folder (in case it has
            to be treated differently)

        Raises:
            NotImplementedError: should be implemented in children classes

        Returns:
            Job: GPAO job to create
        """
        raise NotImplementedError

    def create_metric_relative_to_ref_jobs(
        self, name: str, out_c1: Path, out_ref: Path, output: Path, c1_jobs: List[Job], ref_jobs: List[Job]
    ) -> List[Job]:
        """Create jobs to compute a metric that compares a classification folder (ex: c1) to the reference folder.
        It uses intermediary results produced by jobs created by create_metric_intrinsic_jobs.

        Args:
            name (str):  classification name (used for job name creation)
            out_c1 (Path): path to the results of the intrinsic metric jobs for c1 (input for this part)
            out_ref (Path): path to the results of the intrinsic metric jobs for ref (input for this part)
            output (Path): path to the results of the relative metric
            c1_jobs (List[Job]): Jobs created in create_metric_intrinsic_jobs for c1. Note: Each new job must depend on
            these jobs, to ensure it will computed after them.
            ref_jobs (List[Job]): Jobs created in create_metric_intrinsic_jobs for ref. Note: Each new job must depend
            on these jobs, to ensure it will computed after them.

        Raises:
            NotImplementedError: should be implemented in children classes

        Returns:
            List[Job]: List of GPAO jobs to create
        """
        raise NotImplementedError

    @staticmethod
    def compute_note(df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError
