from coclico.metrics.listing import METRICS


import yaml


import logging
from typing import Dict


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