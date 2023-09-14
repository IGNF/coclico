from pathlib import Path
from typing import Dict, List
import json
from gpao_utils.utils_store import Store

from gpao.job import Job

from coclico._version import __version__
from coclico.metrics.metric import Metric


class MPAP0(Metric):
    def __init__(self, store: Store, class_weights: Dict, test=False):
        super().__init__(store, class_weights)
        self.test = test
        self.metric_name = "MPAP0_test" if test else "MPAP0"

    def create_metric_intrinsic_one_job(self, name: str, input: Path, output: Path):
        job_name = f"{self.metric_name}_initrinsic_{name}_{input.stem}"

        command = f"""
docker run -t --rm --userns=host --shm-size=2gb
-v {self.store.to_unix(input)}:/input
-v {self.store.to_unix(output)}:/output
ignimagelidar/coclico:{__version__}
python -m coclico.mpap0.mpap0_intrinsic
--input_file /input
--output_file /output/{input.stem}.json
--class_weights '{json.dumps(self.class_weights)}'
"""

        job = Job(job_name, command, tags=["docker"])
        return job

    def create_metric_relative_to_ref_jobs(
        self, name: str, out_c1: Path, out_ref: Path, output: Path, c1_jobs: List[Job], ref_jobs: List[Job]
    ) -> Job:
        job_name = f"{self.metric_name}_{name}_relative_to_ref"

        test_option = " -t " if self.test else ""

        command = f"""
docker run -t --rm --userns=host --shm-size=2gb
-v {self.store.to_unix(out_c1)}:/input
-v {self.store.to_unix(out_ref)}:/ref
-v {self.store.to_unix(output)}:/output
ignimagelidar/coclico:{__version__}
python -m coclico.mpap0.mpap0_relative
--input_dir /input
--ref_dir /ref
--output_csv_tile /output/result_tile.csv
--output_csv /output/result.csv
--class_weights '{json.dumps(self.class_weights)}'
{test_option}
"""

        job = Job(job_name, command, tags=["docker"])

        [job.add_dependency(c1_job) for c1_job in c1_jobs]
        [job.add_dependency(ref_job) for ref_job in ref_jobs]

        return [job]


class MPAP0_test(MPAP0):
    def __init__(self, store: Store, class_weights: Dict):
        super().__init__(store, class_weights, test=True)
