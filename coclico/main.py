from pathlib import Path
import logging
import pandas as pd
from typing import Dict
import yaml
import argparse

from coclico.metrics.mpap0 import compare_one_tile_mpap0
import coclico.tools.results_merging as merge


METRICS = {"mpap0": compare_one_tile_mpap0, "mpap0_test": compare_one_tile_mpap0}


def parse_args():
    parser = argparse.ArgumentParser(description="COmparaison de CLassIfication par rapport à une référence COmmune")
    parser.add_argument("--c1", type=Path, help="Dossier C1 contenant une des classifications à comparer")
    parser.add_argument("--c2", type=Path, help="Dossier C2 contenant l'autre classification à comparer")
    parser.add_argument("--ref", type=Path, help="Dossier contenant la classification de référence")
    parser.add_argument("--out", type=Path, help="Dossier de sortie de la comparaison")
    parser.add_argument(
        "--weights_file",
        type=Path,
        default=Path("./configs/metrics_weights.yaml"),
        help="(Optionel) Fichier yaml contenant les poids pour chaque classe/métrique "
        + "si on veut utiliser d'autres valeurs que le défaut",
    )

    return parser.parse_args()


def compare_to_ref(ci: Path, ref: Path, out: Path, metric_weights: Dict):
    logging.debug(f"Compare Ci: {ci} to Ref: {ref} in out {out}")
    out_dir = out.parent
    tiles_filenames = [f.name for f in ref.iterdir() if f.name.lower().endswith(("las", "laz"))]
    merged_df = pd.DataFrame(columns=["tile", "class"])
    for metric_name, metric_fn in METRICS.items():
        if metric_name in metric_weights.keys():
            metric_out = out_dir / metric_name
            # exist_ok = false in order to force working from clean directory
            # to make sure that the concatenation is done only on the expected csv files
            metric_out.mkdir(parents=True, exist_ok=False)

            for tile_fn in tiles_filenames:
                metric_fn(
                    ci, ref, metric_out, tile_fn, class_weights=metric_weights[metric_name], metric_name=metric_name
                )

            metric_df = pd.concat([pd.read_csv(f) for f in metric_out.iterdir() if f.name.endswith("csv")])
            merged_df = merged_df.merge(metric_df, on=["tile", "class"], how="right")

    merged_df.to_csv(out, index=False)


def read_metrics_weights(weights_file: str) -> Dict:
    with open(weights_file, "r") as f:
        weights = yaml.safe_load(f)

    # basic check for potential malformations of the weights file
    if not set(weights.keys()).issubset(set(METRICS.keys())):
        raise ValueError(
            f"Metrics in {weights_file}: {list(weights.keys())} do not match expected metrics: {list(METRICS.keys())}"
        )

    return weights


def compare(c1: Path, c2: Path, ref: Path, out: Path, weights_file: Path = Path("./configs/metrics_weights.yaml")):
    """Main function to compare 2 classification (c1, c2) with respect to a reference
    classification (ref) and save it as json files in out.
    This funcion works on folders containing las files.

    Args:
        c1 (Path): path to the folder containing c1 classified point clouds
        c2 (Path): path to the folder containing c2 classified point clouds
        ref (Path): path to the folder containing the reference classified point clouds
        out (Path): output path for the json outputs
    """
    logging.debug(f"Compare C1: {c1} to Ref: {ref} AND C2:{c2} to {ref} in out {out}")
    result_by_tile_c1_file = out / "c1" / "result_by_tile.csv"
    result_by_tile_c2_file = out / "c2" / "result_by_tile.csv"
    result_by_metric_file = out / "result_by_metric.csv"
    result_file = out / "result.csv"
    metrics_weights = read_metrics_weights(weights_file)
    out.mkdir(parents=True, exist_ok=True)

    compare_to_ref(c1, ref, result_by_tile_c1_file, metrics_weights)
    stats_c1 = merge.compute_stats(result_by_tile_c1_file)
    result_c1 = merge.compute_weighted_result(stats_c1, metrics_weights)

    compare_to_ref(c2, ref, result_by_tile_c2_file, metrics_weights)
    stats_c2 = merge.compute_stats(result_by_tile_c2_file)
    result_c2 = merge.compute_weighted_result(stats_c2, metrics_weights)

    merge.merge_stats([stats_c1, stats_c2], result_by_metric_file)
    merge.merge_weighted_results([result_c1, result_c2], result_file)


if __name__ == "__main__":
    args = parse_args()
    compare(args.c1, args.c2, args.ref, args.out, args.weights_file)
