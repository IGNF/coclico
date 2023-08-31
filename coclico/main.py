import argparse
from coclico.gpao_utils import save_projects_as_json
from gpao.builder import Builder
from gpao.project import Project
from gpao_utils.utils_store import Store
import logging
from pathlib import Path, PurePosixPath
from typing import Dict, List
import yaml

from coclico.metrics.mpap0 import MPAP0

METRICS = {"mpap0": MPAP0(), "mpap0_test": MPAP0()}


def parse_args():
    parser = argparse.ArgumentParser(description="COmparaison de CLassIfication par rapport à une référence COmmune")
    parser.add_argument("--c1", type=Path, help="Dossier C1 contenant une des classifications à comparer")
    parser.add_argument("--c2", type=Path, help="Dossier C2 contenant l'autre classification à comparer")
    parser.add_argument("--ref", type=Path, help="Dossier contenant la classification de référence")
    parser.add_argument("--out", type=Path, help="Dossier de sortie de la comparaison")
    parser.add_argument("--gpao_hostname", type=str, help="Hostname du serveur GPAO")
    parser.add_argument("--local_store_path", type=Path, help="Chemin vers le store sur le PC qui lance ce script")
    parser.add_argument(
        "--runner_store_path",
        type=PurePosixPath,
        help="Chemin vers le store sur les clients GPAO (Unix path)",
        default=PurePosixPath("/var/data/store-lidarhd/"),
    )
    parser.add_argument("--project_name", type=str, default="coclico", help="Nom de projet pour la GPAO")
    parser.add_argument(
        "--weights_file",
        type=Path,
        default=Path("./configs/metrics_weights.yaml"),
        help="(Optionel) Fichier yaml contenant les poids pour chaque classe/métrique "
        + "si on veut utiliser d'autres valeurs que le défaut",
    )

    return parser.parse_args()


# def create_compare_to_ref_project(
#     ci: Path,
#     ref: Path,
#     out: Path,
#     metric_weights: Dict,
#     tiles_filenames: List[str],
#     store: Store,
#     project_name: str,
#     filename_result_by_tile: str = "result_by_tile.csv",
# ) -> Project:
#     """Prepare gpao projects to compare one classification folder to a reference folder based on a list of
#     filenames
#     It generates a csv file for each metrics for each tile (results for all classes are in the same file)
#     in path out / {metric_name}
#     Args:
#         ci (Path): classified pointclouds folder
#         ref (Path): reference pointclouds folder
#         out (Path): output_folder
#         metric_weights (Dict): weights of the different metrics
#           (to know for which classes to generate the comparison)
#         tiles_filenames (List[str]): list of filenames to know for which tile to generate the csv
#         store (Store): Store object used to generate paths on gpao runner
#         project_name (str): project name for gpao projects
#         filename_result_by_tile (str, optional): filename for concatenated result by tile.
#         Defaults to "result_by_tile.csv".

#     Returns:
#         Project: A project to send to GPAO
#     """
#     logging.debug(f"Compare Ci: {ci} to Ref: {ref} in out {out}")
#     out.mkdir(parents=True, exist_ok=True)

#     metrics_jobs = []
#     for metric_name, metric_fn in METRICS.items():
#         if metric_name in metric_weights.keys():
#             metric_out = out / metric_name
#             # exist_ok = false in order to force working from clean directory
#             # to make sure that the concatenation is done only on the expected csv files
#             metric_out.mkdir(parents=True, exist_ok=False)
#             for tile_fn in tiles_filenames:
#                 jobs = metric_fn(
#                     ci,
#                     ref,
#                     metric_out,
#                     tile_fn,
#                     class_weights=metric_weights[metric_name],
#                     store=store,
#                     metric_name=metric_name,
#                 )
#                 metrics_jobs.extend(jobs)

#     merge_job = results_by_tile.create_job_merge_tile_results(out, out / filename_result_by_tile, store)
#     for job in metrics_jobs:
#         merge_job.add_dependency(job)

#     all_jobs = metrics_jobs + [merge_job]
#     project = Project(project_name, all_jobs)

#     return project


def read_metrics_weights(weights_file: str) -> Dict:
    with open(weights_file, "r") as f:
        weights = yaml.safe_load(f)
        logging.info(f"Loaded weights from {weights_file}:")

    # basic check for potential malformations of the weights file
    if not set(weights.keys()).issubset(set(METRICS.keys())):
        raise ValueError(
            f"Metrics in {weights_file}: {list(weights.keys())} do not match expected metrics: {list(METRICS.keys())}"
        )

    # remove spaces from classes keys
    weights_clean = dict()
    for metric, value in weights.items():
        metric_dict = {k.replace(" ", ""): v for k, v in value.items()}
        weights_clean[metric] = metric_dict
    logging.info(weights_clean)

    return weights_clean


def get_tile_names(folder: Path) -> List[str]:
    """Get tiles filenames from the content of a folder: las an laz files only

    Args:
        folder (Path): input folder

    Returns:
        List[str]: list of filenames
    """
    filenames = [f.name for f in folder.iterdir() if f.name.lower().endswith(("las", "laz"))]

    return filenames


def create_compare_projects(
    c1: Path,
    c2: Path,
    ref: Path,
    out: Path,
    store: Store,
    project_name: str,
    metrics_weights: Dict,
) -> List[Project]:
    """Main function to generate all GPAO projects needed to compare 2 classification (c1, c2) with respect to a
    reference classification (ref) and save it as json files in out.
    This function works on folders containing las files.

    Args:
        c1 (Path): path to the folder containing c1 classified point clouds
        c2 (Path): path to the folder containing c2 classified point clouds
        ref (Path): path to the folder containing the reference classified point clouds
        out (Path): output path for the json outputs
        store (Store): store object to convert local paths to runner paths
        project_name (str): base project name for gpao projects
        metrics_weights (Dict): Dict containing the weight of each metric for each class.
    """

    logging.debug(f"Create GPAO projects to Compare C1: {c1} to Ref: {ref} AND C2:{c2} to {ref} in out {out}.")
    Project.reset()

    out_c1 = out / "c1"
    out_c2 = out / "c2"
    out_ref = out / "ref"

    out.mkdir(parents=True, exist_ok=True)
    # filename_result_by_tile = "result_by_tile.csv"
    # filename_result_by_metric = "result_by_metric.csv"
    # filename_result = "result.csv"

    # get filenames of tiles from the local machine
    tile_names = get_tile_names(ref)

    jobs = []

    for metric_name, metric_class in METRICS.items():
        if metric_name in metrics_weights.keys():
            out_c1_metric = out_c1 / metric_name
            out_c2_metric = out_c2 / metric_name
            out_ref_metric = out_ref / metric_name

            ref_jobs = metric_class.create_metric_intrinsic_jobs("ref", tile_names, ref, out_ref_metric)
            c1_jobs = metric_class.create_metric_intrinsic_jobs("c1", tile_names, c1, out_c1_metric)
            c2_jobs = metric_class.create_metric_intrinsic_jobs("c2", tile_names, c2, out_c2_metric)

            out_c1_to_ref = out_c1_metric / "to_ref"
            out_c1_to_ref.mkdir(parents=True, exist_ok=True)

            out_c2_to_ref = out_c2_metric / "to_ref"
            out_c2_to_ref.mkdir(parents=True, exist_ok=True)

            out_score = out / "score"
            out_score.mkdir(parents=True, exist_ok=True)

            c1_to_ref_jobs = metric_class.create_metric_relative_to_ref_jobs(
                "c1", out_c1_metric, out_ref_metric, out_c1_to_ref, c1_jobs, ref_jobs
            )
            c2_to_ref_jobs = metric_class.create_metric_relative_to_ref_jobs(
                "c2", out_c2_metric, out_ref_metric, out_c2_to_ref, c2_jobs, ref_jobs
            )

            score_jobs = metric_class.create_score_jobs(
                out_c1_to_ref, out_c2_to_ref, out_score, c1_to_ref_jobs, c2_to_ref_jobs
            )

            jobs.extend(c1_jobs)
            jobs.extend(c2_jobs)
            jobs.extend(ref_jobs)
            jobs.extend(c1_to_ref_jobs)
            jobs.extend(c2_to_ref_jobs)
            jobs.extend(score_jobs)

    return [Project(project_name, jobs)]

    # project_c1 = create_compare_to_ref_project(
    #     c1,
    #     ref,
    #     out_c1,
    #     metrics_weights,
    #     tiles_filenames=tile_names,
    #     store=store,
    #     project_name=f"{project_name}_c1",
    #     filename_result_by_tile=filename_result_by_tile,
    # )

    # project_c2 = create_compare_to_ref_project(
    #     c2,
    #     ref,
    #     out_c2,
    #     metrics_weights,
    #     tiles_filenames=tile_names,
    #     store=store,
    #     project_name=f"{project_name}_c2",
    #     filename_result_by_tile=filename_result_by_tile,
    # )

    # project_merge = merge.create_merge_all_results_project(
    #     out_c1 / filename_result_by_tile,
    #     out_c2 / filename_result_by_tile,
    #     out / filename_result_by_metric,
    #     out / filename_result,
    #     store,
    #     metrics_weights,
    #     project_name=f"{project_name}_merge",
    # )

    # project_merge.add_dependency(project_c1)
    # project_merge.add_dependency(project_c2)

    # return [project_c1, project_c2, project_merge]


def compare(
    c1: Path,
    c2: Path,
    ref: Path,
    out: Path,
    gpao_hostname: str,
    local_store_path: Path,
    runner_store_path: PurePosixPath,
    project_name: str,
    weights_file: Path = Path("./configs/metrics_weights.yaml"),
):
    """Main function to compare 2 classification (c1, c2) with respect to a reference
    classification (ref) and save it as json files in out.
    This function works on folders containing las files.
    It uses a GPAO setup to handle the amount of work : it generates it and sends it to a GPAO server

    Args:
        c1 (Path): path to the folder containing c1 classified point clouds
        c2 (Path): path to the folder containing c2 classified point clouds
        ref (Path): path to the folder containing the reference classified point clouds
        out (Path): output path for the json outputs
        gpao_hostname (str): Hostname of the GPAO server
        local_store_path (Path): path to a distant store on the local machine (the one on which the script is launched)
        runner_store_path (PurePosixPath): path to this distant store on the gpao clients (unix path)
        project_name (str): base project name for gpao projects
        weights_file (Path, optional): Yaml file containing the weight of each metric for each class.
        Defaults to Path("./configs/metrics_weights.yaml").
    """

    logging.debug(f"Create GPAO projects to Compare C1: {c1} to Ref: {ref} AND C2:{c2} to {ref} in out {out}.")
    logging.debug(f"Use GPAO server: {gpao_hostname}")
    store = Store(local_store_path, unix_runner_path=runner_store_path)
    logging.debug(f"Local store path ({local_store_path}) converted to client store path ({runner_store_path})")

    metrics_weights = read_metrics_weights(weights_file)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "metrics_weights.yaml", "w") as f:
        yaml.safe_dump(metrics_weights, f)

    projects = create_compare_projects(
        c1,
        c2,
        ref,
        out,
        store,
        project_name,
        metrics_weights,
    )

    builder = Builder(projects)
    logging.info(f"Send projects to gpao server: {gpao_hostname}")
    builder.send_project_to_api(f"http://{gpao_hostname}:8080")
    # Do not use builder.save_as_json because it resets projects/jobs ids.
    # cf https://github.com/ign-gpao/builder-python/issues/10
    save_projects_as_json(projects, out / "gpao_project.json")


if __name__ == "__main__":
    logging.basicConfig(level="INFO")

    args = parse_args()
    compare(
        args.c1,
        args.c2,
        args.ref,
        args.out,
        args.gpao_hostname,
        args.local_store_path,
        args.runner_store_path,
        args.project_name,
        args.weights_file,
    )
