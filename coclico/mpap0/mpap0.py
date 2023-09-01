import numpy as np

from pathlib import Path
from typing import Dict, List
import json
from gpao_utils.utils_store import Store

from gpao.job import Job

from coclico.metrics.commons import bounded_affine_function
from coclico._version import __version__
from coclico.metrics.metric import Metric


class MPAP0(Metric):
    def create_metric_intrinsic_one_job(self, name: str, input: Path, output: Path):
        job_name = f"MPAP0_initrinsic_{name}_{input.stem}"
        job = Job(job_name, f"echo {job_name}")
        return job

    def create_metric_relative_to_ref_jobs(
        self, name: str, out_c1: Path, out_ref: Path, output: Path, c1_jobs: List[Job], ref_jobs: List[Job]
    ) -> Job:
        job_name = f"MPAP0_{name}_relative_to_ref"
        job = Job(job_name, f"echo {job_name}")

        [job.add_dependency(c1_job) for c1_job in c1_jobs]
        [job.add_dependency(ref_job) for ref_job in ref_jobs]

        return [job]


def compute_metric_relative_mpap0(pts_counts_ci: Dict, pts_counts_ref: Dict) -> Dict:
    all_keys = set(list(pts_counts_ci.keys()) + list(pts_counts_ref.keys()))
    counts_absolute_diff = {k: np.abs(pts_counts_ci.get(k, 0) - pts_counts_ref.get(k, 0)) for k in all_keys}

    return counts_absolute_diff


def compute_note_mpap0(counts_absolute_diff: Dict, pts_counts_ref: Dict) -> Dict:
    def compute_one_note(abs_diff, count):
        if count >= 1000:
            relative_diff = abs_diff / count
            note = bounded_affine_function((0, 1), (0.1, 0), relative_diff)
        else:
            note = bounded_affine_function((20, 1), (100, 0), abs_diff)

        return note

    notes = {
        k: compute_one_note(counts_absolute_diff[k], pts_counts_ref.get(k, 0)) for k in counts_absolute_diff.keys()
    }

    return notes


def create_job_one_tile_mpap0(
    ci: Path,
    ref: Path,
    out: Path,
    tile_fn: str,
    class_weights: Dict,
    store: Store,
    metric_name: str = "mpap0",
) -> List[Job]:
    """_summary_

    Args:
        ci (Path): Path to the classified pointclouds folder (on the local machine)
        ref (Path): Path to the reference pointclouds folder (on the local machine)
        out (Path): Path to the output csv files folder (on the local machine)
        tile_fn (str): filename of the tile
        class_weights (Dict): class weights dictionary (to know on which classes to run the metric)
        metric_name (str, optional): metric name (to display in the csv file). Defaults to "mpap0".

    Returns:
        List[Job]: _description_
    """
    command = f"""
    docker run -t --rm --userns=host --shm-size=2gb
    -v {store.to_unix(ci)}:/ci
    -v {store.to_unix(ref)}:/ref
    -v {store.to_unix(out)}:/out
    lidar_hd/coclico:{__version__}
    python -m coclico.metrics.mpap0
    --ci "/ci"
    --ref "/ref"
    --out "/out"
    --tile_filename {tile_fn}
    --class_weights '{json.dumps(class_weights)}'
    --metric_name {metric_name}
    """
    job = Job(f"{tile_fn.split('.')[0]}_{metric_name}", command, tags=["docker"])

    return [job]


# def compare_one_tile_mpap0(
#     ci: Path, ref: Path, out: Path, tile_fn: str, class_weights: Dict, metric_name: str = "mpap0"
# ):
#     logging.debug(f"Compare Ci: {ci} to Ref: {ref} in out {out} for metric MPAP0")
#     tile_stem = Path(tile_fn).stem
#     out.mkdir(parents=True, exist_ok=True)
#     out_file = out / (tile_stem + ".csv")
#     points_counts_ci = compute_metric_intrinsic_mpap0(ci / tile_fn, class_weights)
#     points_counts_ref = compute_metric_intrinsic_mpap0(ref / tile_fn, class_weights)

#     score = compute_metric_relative_mpap0(points_counts_ci, points_counts_ref)
#     note = compute_note_mpap0(score, points_counts_ref)
#     data = [{"tile": tile_stem, "class": cl, metric_name: note[cl]} for cl in class_weights.keys()]
#     df = pd.DataFrame(data)
#     df.to_csv(out_file, index=False)


# def parse_args():
#     parser = argparse.ArgumentParser("Run mpap0 metric on one tile")
#     parser.add_argument("--ci", type=Path, help="Path to the folder containing the classification to compare")
#     parser.add_argument("--ref", type=Path, help="Path to the folder containing the reference point cloud")
#     parser.add_argument("--out", type=Path, help="Path to the folder to save the metric csv")
#     parser.add_argument("--tile_filename", type=str, help="Filename of the tile on which to compute the metric")
#     parser.add_argument(
#         "--class_weights", type=json.loads, help="Dictionary of the classes weights for the metric (as a string)"
#     )
#     parser.add_argument("--metric_name", type=str, help="Name of the metric (as displayed in the csv)")

#     return parser.parse_args()


# if __name__ == "__main__":
#     args = parse_args()
#     compare_one_tile_mpap0(args.ci, args.ref, args.out, args.tile_filename, args.class_weights, args.metric_name)
