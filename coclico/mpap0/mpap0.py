from pathlib import Path
from typing import List
import json

from gpao.job import Job

from coclico.version import __version__
from coclico.metrics.metric import Metric


class MPAP0(Metric):
    """Metric MPAP0 (for "Métrique point à point 0")
    Comparison of the number of points for each class between the classification and the reference
    - metric intrinsic: compute number of points for each class
    - metric relative: compare number of points for each class
    - note:
        * if reference data has more than 1000 points: affine function on the relative difference in number of points
        * otherwise: affine function on the absolute difference in number of points
    """

    metric_name = "MPAP0"

    def create_metric_intrinsic_one_job(self, name: str, input: Path, output: Path):
        job_name = f"{self.metric_name}_intrinsic_{name}_{input.stem}"

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
"""

        job = Job(job_name, command, tags=["docker"])

        [job.add_dependency(c1_job) for c1_job in c1_jobs]
        [job.add_dependency(ref_job) for ref_job in ref_jobs]

        return [job]
