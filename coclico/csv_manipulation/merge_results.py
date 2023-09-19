import argparse
from coclico._version import __version__
from gpao.job import Job
from gpao_utils.utils_store import Store
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List


def compute_weighted_result(input: Path, weights: Dict) -> Dict:
    """Compute weighted sum of notes for all metrics using the weights stored in a dictionary like:
        weights = {
            "metric1": {
                "class0": 1,
                "class1": 2
            },
            "metric2": {
                "class0": 0,
                "class1": 3
            }
        }

    Args:
        input (Path): path to a CSV containing note for metrics for a classification
        weights (Dict): weights to apply to the different metrics to generate the aggregated result

    Returns:
        score (Dict): score for this classification, and score for the metrics, in a dict like that
        result = {
            "classification": 'c1',
            "score": 7.0,
            "mpap0": 4.6,
            "mpap0_test": 2.4
        }
    """
    df = pd.read_csv(input)
    classif_name = input.parent.name
    logging.debug("Score for %s", classif_name)
    total_score = 0
    result = {
        "classification": input.parent.name,
        "score": 0
    }
    for metric in weights.keys():
        res_metric = 0
        logging.debug("- Metric %s", metric)
        for i, row in df.iterrows():
            i_class = row["class"]
            weight_metric = weights[metric]
            if i_class in weight_metric:
                val = row[metric]
                weight_metric_class = weights[metric][i_class]
                res_local = val * weight_metric_class
                logging.debug("-- Class %s: note %s  * weight %s = %s", i_class, val, weight_metric_class, res_local)
                res_metric += res_local
        logging.debug("-> Metric %s = %s", metric, res_metric)
        result[metric] = res_metric
        total_score += res_metric
    logging.debug("=> Score %s = %s\n", classif_name, total_score)
    result["score"] = total_score
    return result

def create_merge_all_results_job(
    result_ci: List[Path], output: Path, store: Store, metrics_weights: Dict, deps: List[Job] = None
) -> Job:
    volumes = [f" -v {store.to_unix(f.parent)}:/{f.parent.name}\n" for f in result_ci]
    inputs = [f" /{f.parent.name}/{f.name}" for f in result_ci]
    command = f"""
    docker run -t --rm --userns=host --shm-size=2gb
    {' '.join(volumes)}
    -v {store.to_unix(output.parent)}:/out
    ignimagelidar/coclico:{__version__}
    python -m coclico.csv_manipulation.merge_results
    -i {' '.join(inputs)}
    --output /out/{output.name}
    --metric_weights '{json.dumps(metrics_weights)}'
    """
    return Job("merge_all_results", command, tags=["docker"], deps=deps)


def merge_all_results(
    input_ci: List[Path],
    output: Path,
    metrics_weights: Dict,
):
    output.parent.mkdir(parents=True, exist_ok=True)

    data = [
        compute_weighted_result(input, metrics_weights)
        for input in input_ci
    ]

    df_by_metric = pd.DataFrame(data)
    output_by_metric = output.parent / (output.stem + "_by_metric.csv")
    df_by_metric.to_csv(output_by_metric, index=False)

    df = df_by_metric.iloc[:, 0:2]
    df.to_csv(output, index=False)

def parse_args():
    parser = argparse.ArgumentParser("Run merge results")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        nargs="+",
        help="Path to the CSV files containing all metrics results for one classification (separated by a whitespace)",
    )
    parser.add_argument("-o", "--output", type=Path, help="Path to the file to save the global weighted result")
    parser.add_argument("--metric_weights", type=json.loads, help="Dictionary of the metrics weights")

    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    args = parse_args()
    print(args.input)
    merge_all_results(
        args.input,
        args.output,
        args.metric_weights,
    )
