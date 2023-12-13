import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
from gpao.job import Job
from gpao_utils.store import Store

from coclico.config import csv_separator
from coclico.version import __version__
import coclico.io as io


def filter_out_rows(df, col, values):
    return df[~df[col].isin(values)]

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
        input (Path): input CSV file, containing notes for metrics for a classification
        weights (Dict): weights to apply to the different metrics to generate the aggregated result

    Returns:
        score (Dict): score for this classification, and score for the metrics, in a dict like that
        result = {
            "classification": "c1",
            "score": 7.0,
            "mpap0": 4.6,
            "mpla0": 2.4
        }
    """
    df = pd.read_csv(input, sep=csv_separator)
    classif_name = input.parent.name
    logging.debug("Score for %s", classif_name)
    total_score = 0
    result = {"classification": input.parent.name, "score": 0}
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
    result_ci: List[Path], output: Path, store: Store, config_file: Path, deps: List[Job] = None
) -> Job:
    """Create GPAO job, that compute the score and merge all results in CSV files.

    Args:
        result_ci (List[Path]): List of CSV input files, containing all metrics results for one classification
        output (Path): output CSV file to create (ex: result.csv). Another file with postfix '_by_metric.csv' will be
        created
        store (Store): store
        metrics_weights (Dict): weights to apply to the different metrics to generate the aggregated result
        deps (List[Job], optional): job dependencies. Defaults to None.

    Returns:
        Job: GPAO Job representing the merge job
    """
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
    --config-file /out/{config_file}'
    """
    return Job("merge_all_results", command, tags=["docker"], deps=deps)


def merge_all_results(
    input_ci: List[Path],
    output: Path,
    config_file: Path,
):
    """Merge the result of all classifications. Create two CSV files
     - one with the score for all classification
     - another containing also the score for each metric

    Args:
        input_ci (List[Path]): input CSV files, one file for each classification.
        output (Path): ouput CSV file to create (ex: result.csv). Another file with postfix '_by_metric.csv' will be
        created.

        metrics_weights (Dict): weights to apply to the different metrics to generate the aggregated result
    """
    config_dict = io.read_metrics_weights(config_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    data = [compute_weighted_result(input, config_dict) for input in input_ci]

    df = pd.DataFrame(data)
    output_by_metric = output.parent / (output.stem + "_by_metric.csv")
    if output_by_metric.exists():
        existing_df = pd.read_csv(output_by_metric, sep=csv_separator)
        existing_classif = existing_df["classification"].to_list()
        incoming_classif = df["classification"].to_list()
        to_remove_classif = list(set(existing_classif) & set(incoming_classif))
        if len(to_remove_classif) > 0:
            logging.info("Replace existing classification(s): %s in the score file" % to_remove_classif)
            existing_df = filter_out_rows(existing_df, "classification", to_remove_classif)
        df = pd.concat([existing_df, df])

    df.to_csv(output_by_metric, index=False, sep=csv_separator)

    df_summary = df.iloc[:, 0:2]
    df_summary.to_csv(output, index=False, sep=csv_separator)


def parse_args():
    parser = argparse.ArgumentParser("Run merge results")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        nargs="+",
        help="input CSV files, one file contains all metrics results for one classification",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="""Path to the file to save the global weighted result, for all all classifications.
Another CSV file with the same name and postfix '_by_metric.csv' will be created""",
    )
    parser.add_argument("--config-file", type=Path, help="Dictionary of the metrics weights")

    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    args = parse_args()
    print(args.input)
    merge_all_results(
        args.input,
        args.output,
        args.config_file,
    )
