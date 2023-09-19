from gpao.job import Job
from typing import List
from pathlib import Path
from gpao_utils.store import Store
from typing import Dict


class Metric:
    def __init__(self, store: Store, class_weights: Dict):
        self.store = store
        self.class_weights = class_weights

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
