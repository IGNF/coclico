from gpao.job import Job
from typing import List
from pathlib import Path


class Metric:
    def create_metric_intrinsic_jobs(
        self, name: str, tile_names: List[str], input_path: Path, out_path: Path
    ) -> List[Job]:
        return [self.create_metric_intrinsic_one_job(name, input_path / f, out_path) for f in tile_names]

    def create_metric_intrinsic_one_job(self, name: str, input: Path, output: Path) -> Job:
        raise NotImplementedError

    def create_metric_relative_to_ref_jobs(
        self, name: str, out_c1: Path, out_ref: Path, output: Path, c1_jobs: List[Job], ref_jobs: List[Job]
    ) -> List[Job]:
        raise NotImplementedError

    def create_score_jobs(
        self,
        name: str,
        out_c1_to_ref,
        out_c2_to_ref,
        output: Path,
        c1_to_ref_jobs: List[Job],
        c2_to_ref_jobs: List[Job],
    ) -> Job:
        raise NotImplementedError
