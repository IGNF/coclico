import argparse
from coclico.gpao_utils import save_projects_as_json
from gpao.builder import Builder
from gpao.project import Project
from gpao_utils.store import Store
import logging
from pathlib import Path, PurePosixPath
from typing import Dict, List
import yaml
from coclico.csv_manipulation import results_by_tile, merge_results
from coclico.mpap0.mpap0 import MPAP0, MPAP0_test


METRICS = {"mpap0": MPAP0, "mpap0_test": MPAP0_test}


def parse_args():
    parser = argparse.ArgumentParser(description="COmparaison de CLassIfication par rapport à une référence COmmune")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        nargs="+",
        required=True,
        help="Dossier(s) contenant une ou plusieurs classification(s) à comparer. ex: -i /chemin/c1 chemin/c2",
    )
    parser.add_argument("--ref", type=Path, required=True, help="Dossier contenant la classification de référence")
    parser.add_argument("--out", type=Path, required=True, help="Dossier de sortie de la comparaison")
    parser.add_argument(
        "--local_store_path",
        type=Path,
        required=True,
        help="Chemin vers un store commun sur le PC qui lance ce script",
    )
    parser.add_argument(
        "--runner_store_path",
        type=PurePosixPath,
        help="Chemin vers un store commun sur les clients GPAO (Unix path)",
        required=True,
    )
    parser.add_argument("--gpao_hostname", type=str, help="Hostname du serveur GPAO", default="localhost")
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


def check_pathes_ends_with_different_names(classifications: List[Path]):
    names_dict = dict([(ci.name, []) for ci in classifications])
    [names_dict[ci.name].append(str(ci)) for ci in classifications]
    for name in names_dict.keys():
        if len(names_dict[name]) > 1:
            raise (ValueError("Classifications input pathes ends with same name: " + " ; ".join(names_dict[name])))


def create_compare_project(
    classifications: List[Path],
    ref: Path,
    out: Path,
    store: Store,
    project_name: str,
    metrics_weights: Dict,
) -> List[Project]:
    """Main function to generate a GPAO project needed to compare classifications (c1, c2..) with respect to a
    reference classification (ref) and save it as json files in out.
    This function works on folders containing las files.

    Args:
        ci (List[Path]): list of path to the folder containing each classified point clouds (c1, c2..)
        ref (Path): path to the folder containing the reference classified point clouds
        out (Path): output path for the json outputs
        store (Store): store object to convert local paths to runner paths
        project_name (str): base project name for gpao projects
        metrics_weights (Dict): Dict containing the weight of each metric for each class.
    """

    check_pathes_ends_with_different_names(classifications)

    logging.debug(
        f"Create GPAO projects to compare {len(classifications)} classification(s): {classifications}"
        + " to Ref: {ref} in Out: {out}."
    )
    Project.reset()

    out_ref = out / "ref"
    out.mkdir(parents=True, exist_ok=True)

    # get filenames of tiles from the local machine
    tile_names = get_tile_names(ref)
    jobs = []
    final_relative_jobs = {k.name: [] for k in classifications}

    for metric_name, metric_class in METRICS.items():
        if metric_name in metrics_weights.keys():
            class_weights = metrics_weights[metric_name]
            metric = metric_class(store, class_weights)

            out_ref_metric = out_ref / metric_name / "intrinsic"
            out_ref_metric.mkdir(parents=True, exist_ok=True)

            ref_jobs = metric.create_metric_intrinsic_jobs("ref", tile_names, ref, out_ref_metric)
            jobs.extend(ref_jobs)

            for ci in classifications:
                out_c1 = out / ci.name
                out_c1_metric = out_c1 / metric_name / "intrinsic"
                out_c1_metric.mkdir(parents=True, exist_ok=True)

                c1_jobs = metric.create_metric_intrinsic_jobs(ci.name, tile_names, ci, out_c1_metric)

                out_c1_to_ref_metric = out_c1 / metric_name / "to_ref"
                out_c1_to_ref_metric.mkdir(parents=True, exist_ok=True)

                c1_to_ref_jobs = metric.create_metric_relative_to_ref_jobs(
                    ci.name, out_c1_metric, out_ref_metric, out_c1_to_ref_metric, c1_jobs, ref_jobs
                )

                final_relative_jobs[ci.name].append(c1_to_ref_jobs[-1])

                jobs.extend(c1_jobs)
                jobs.extend(c1_to_ref_jobs)

    score_deps = []
    score_results = []
    for ci in classifications:
        out_c1 = out / ci.name
        result1 = out_c1 / (str(ci.name) + "_result.csv")
        c1_final_relative_jobs = final_relative_jobs[ci.name]
        merge_c1_metrics = results_by_tile.create_job_merge_results(
            out_c1, result1, store, deps=c1_final_relative_jobs
        )

        score_deps.append(merge_c1_metrics)
        score_results.append(result1)
        jobs.append(merge_c1_metrics)

    score_job = merge_results.create_merge_all_results_job(
        score_results, out / "result.csv", store, metrics_weights, score_deps
    )

    jobs.append(score_job)

    return [Project(project_name, jobs)]


def compare(
    classifications: List[Path],
    ref: Path,
    out: Path,
    gpao_hostname: str,
    local_store_path: Path,
    runner_store_path: PurePosixPath,
    project_name: str,
    weights_file: Path = Path("./configs/metrics_weights.yaml"),
):
    """Main function to compare one or more classifications (c1, c2..) with respect to a reference
    classification (ref) and save it as json files in out.
    This function works on folders containing las files.
    It uses a GPAO setup to handle the amount of work : it generates it and sends it to a GPAO server

    Args:
        classifications (List[Path]): list of path to the folder containing each classified point clouds (c1, c2..)
        ref (Path): path to the folder containing the reference classified point clouds
        out (Path): output path for the json outputs
        gpao_hostname (str): Hostname of the GPAO server
        local_store_path (Path): path to a distant store on the local machine (the one on which the script is launched)
        runner_store_path (PurePosixPath): path to this distant store on the gpao clients (unix path)
        project_name (str): base project name for gpao projects
        weights_file (Path, optional): Yaml file containing the weight of each metric for each class.
        Defaults to Path("./configs/metrics_weights.yaml").
    """

    logging.debug(
        f"Create GPAO projects to compare {len(classifications)} classifications: {classifications}"
        + " to Ref: {ref} in Out {out}."
    )
    logging.debug(f"Use GPAO server: {gpao_hostname}")
    store = Store(local_store_path, unix_path=runner_store_path)
    logging.debug(f"Local store path ({local_store_path}) converted to client store path ({runner_store_path})")

    metrics_weights = read_metrics_weights(weights_file)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "metrics_weights.yaml", "w") as f:
        yaml.safe_dump(metrics_weights, f)

    projects = create_compare_project(
        classifications,
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
        args.input,
        args.ref,
        args.out,
        args.gpao_hostname,
        args.local_store_path,
        args.runner_store_path,
        args.project_name,
        args.weights_file,
    )
