import argparse
from coclico.gpao_utils import save_projects_as_json
from gpao.builder import Builder
from gpao.project import Project
from gpao_utils.utils_store import Store
import logging
from pathlib import Path, PurePosixPath
from typing import Dict, List
import yaml

from coclico.mpap0.mpap0 import MPAP0
from gpao.job import Job

METRICS = {"mpap0": MPAP0, "mpap0_test": MPAP0}


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

    final_relative_jobs = []

    for metric_name, metric_class in METRICS.items():
        if metric_name in metrics_weights.keys():
            out_c1_metric = out_c1 / metric_name / "intrinsic"
            out_c1_metric.mkdir(parents=True, exist_ok=True)

            out_c2_metric = out_c2 / metric_name / "intrinsic"
            out_c2_metric.mkdir(parents=True, exist_ok=True)

            out_ref_metric = out_ref / metric_name / "intrinsic"
            out_ref_metric.mkdir(parents=True, exist_ok=True)

            metric = metric_class()
            ref_jobs = metric.create_metric_intrinsic_jobs("ref", tile_names, ref, out_ref_metric)
            c1_jobs = metric.create_metric_intrinsic_jobs("c1", tile_names, c1, out_c1_metric)
            c2_jobs = metric.create_metric_intrinsic_jobs("c2", tile_names, c2, out_c2_metric)

            out_c1_to_ref_metric = out_c1 / metric_name / "to_ref"
            out_c1_to_ref_metric.mkdir(parents=True, exist_ok=True)

            out_c2_to_ref_metric = out_c2 / metric_name / "to_ref"
            out_c2_to_ref_metric.mkdir(parents=True, exist_ok=True)

            c1_to_ref_jobs = metric.create_metric_relative_to_ref_jobs(
                "c1", out_c1_metric, out_ref_metric, out_c1_to_ref_metric, c1_jobs, ref_jobs
            )
            c2_to_ref_jobs = metric.create_metric_relative_to_ref_jobs(
                "c2", out_c2_metric, out_ref_metric, out_c2_to_ref_metric, c2_jobs, ref_jobs
            )

            final_relative_jobs.append(c1_to_ref_jobs[-1])
            final_relative_jobs.append(c2_to_ref_jobs[-1])

            jobs.extend(c1_jobs)
            jobs.extend(c2_jobs)
            jobs.extend(ref_jobs)
            jobs.extend(c1_to_ref_jobs)
            jobs.extend(c2_to_ref_jobs)

    final_job = Job("compute_score", "echo compute all score", final_relative_jobs)
    jobs.append(final_job)
    # final_job should do this :
    # coclico.csv_manipulation.results_by_tile.create_job_merge_tile_results
    # coclico.csv_manipulation.merge_result.create_merge_all_results_project

    return [Project(project_name, jobs)]


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
