import logging
from typing import Dict

import yaml

from coclico.metrics.listing import METRICS


def read_config_file(config_file: str) -> Dict:
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
        logging.info(f"Loaded weights from {config_file}:")

    # basic check for potential malformations of the weights file
    if not set(config.keys()).issubset(set(METRICS.keys())):
        raise ValueError(
            f"Metrics in {config_file}: {list(config.keys())} do not match expected metrics: {list(METRICS.keys())}"
        )
    expected_metric_keys = {"notes", "weights"}
    for metric_name, metric_dict in config.items():
        if not set(metric_dict.keys()) == expected_metric_keys:
            raise ValueError(
                f" in {config_file}: keys for metric {metric_name} ({list(metric_dict.keys())}) do not match "
                f"expected keys: {list(expected_metric_keys)}"
            )

    return config
