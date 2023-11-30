import json
from pathlib import Path
from typing import List

from gpao.job import Job

from coclico.metrics.metric import Metric
from coclico.version import __version__


class MALT0(Metric):
    """Metric MALT0 (for "Métrique altimétrique 0")
    Comparison of 2d height maps (digital surface model for one class only) for each class between the
    classification and the reference. The comparison is done only for the pixels of the map that contain
    points in the reference tile (based on an occupancy map similar to the one used in MPLA0).

    - metric_intrinsic:
        - for each input file, generate a tif file with one layer by class in the class_weight dictionary
    for each class, the corresponding layer contains a height map of the class, created the same way as a digital
    surface model:
            - generate a 2D delaunay triangulation of the points of the given class
            - interpolate the values on a raster with the desired pixel size (pdal faceraster filter)

        - for the tiles of the reference folder, generate also an addditional "occupancy map":
    a tif file with one layer by class in the class_weight dictionary for each class, the corresponding layer contains
    a kind of 2d occupancy map for the class (ie. if any point of this class belongs to the pixel, the pixel has a
    value of 1, the value is 0 everywhere else)


    - metric relative:
        Compare the Z values between the classification and the reference, then compute the mean, max and standard
        deviation of the difference. (only where the occupancy map of the reference is True)

    - note:
        Linear combination of notes:
        - a bounded affine function of the max dfference
        - a bounded affine function of the mean dfference
        - a bounded affine function of the standard deviation of the dfference
    """

    # Pixel size for MNx
    pixel_size = 0.5
    metric_name = "MALT0"

    def create_metric_intrinsic_one_job(self, name: str, input: Path, output: Path, is_ref: bool):
        job_name = f"{self.metric_name}_intrinsic_{name}_{input.stem}"
        occupancy_map_arg = ""
        mnx_out = output / "mnx"
        mnx_out.mkdir(exist_ok=True, parents=True)
        if is_ref:
            occ_out = output / "occupancy"
            occ_out.mkdir(exist_ok=True, parents=True)
            occupancy_map_arg = f"--output-occupancy-file /output/occupancy/{input.stem}.tif"

        command = f"""
docker run -t --rm --userns=host --shm-size=2gb
-v {self.store.to_unix(input)}:/input
-v {self.store.to_unix(output)}:/output
ignimagelidar/coclico:{__version__}
python -m coclico.malt0.malt0_intrinsic
--input-file /input
--output-mnx-file /output/mnx/{input.stem}.tif
{occupancy_map_arg}
--class-weights '{json.dumps(self.class_weights)}'
--pixel-size {self.pixel_size}
"""

        job = Job(job_name, command, tags=["docker"])
        return job

    def create_metric_relative_to_ref_jobs(
        self, name: str, out_c1: Path, out_ref: Path, output: Path, c1_jobs: List[Job], ref_jobs: List[Job]
    ) -> Job:
        job_name = f"{self.metric_name}_{name}_relative_to_ref"
        command = f"""
docker run -t --rm --userns=host --shm-size=2gb
-v {self.store.to_unix(out_c1) / "mnx"}:/input
-v {self.store.to_unix(out_ref) / "mnx"}:/ref
-v {self.store.to_unix(out_ref) / "occupancy"}:/occupancy
-v {self.store.to_unix(output)}:/output
ignimagelidar/coclico:{__version__}
python -m coclico.malt0.malt0_relative
--input-dir /input
--ref-dir /ref
--occupancy-dir /occupancy
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
