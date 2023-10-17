from pathlib import Path
from typing import List
import json

from gpao.job import Job

from coclico.version import __version__
from coclico.metrics.metric import Metric


class MPLA0(Metric):
    """Metric MPLA0 (for "Métrique planimetric 0")
    Comparison of 2d classification maps (occupancy maps) for each class between the classification and the
    reference

    - metric_intrinsic:
        for each input file, generate a tif file with one layer by class in the class_weight dictionary
        for each class, the corresponding layer contains a kind of 2d occupancy map for the class (ie. if any point
        of this class belongs to the pixel, the pixel has a value of 1, the value is 0 everywhere else)

    - metric extrinsic: compute intersection and union of the classification maps

    - note:
        * if reference data has more than 1000 points: affine function on the intersection over union for each class
        * otherwise: affine function on {union - intersection}
    """

    # Pixel size for the intermediate result: 2d binary maps for each class
    map_pixel_size = 0.5
    metric_name = "MPLA0"

    def create_metric_intrinsic_one_job(self, name: str, input: Path, output: Path):
        job_name = f"{self.metric_name}_intrinsic_{name}_{input.stem}"

        command = f"""
docker run -t --rm --userns=host --shm-size=2gb
-v {self.store.to_unix(input)}:/input
-v {self.store.to_unix(output)}:/output
ignimagelidar/coclico:{__version__}
python -m coclico.mpla0.mpla0_intrinsic
--input_file /input
--output_file /output/{input.stem}.json
--class_weights '{json.dumps(self.class_weights)}'
--pixel_size {self.map_pixel_size}
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
--input_dir /input
--ref_dir /ref
--output_csv_tile /output/result_tile.csv
--output_csv /output/result.csv
--class_weights '{json.dumps(self.class_weights)}'
"""

        job = Job(job_name, command, tags=["docker"])
        for c1_job in c1_jobs:
            job.add_dependency(c1_job)
        for ref_job in ref_jobs:
            job.add_dependency(ref_job)

        return [job]
