import socket
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from client import worker

from coclico.config import csv_separator


def csv_num_rows(f: Path):
    assert f.exists()
    df = pd.read_csv(f, sep=csv_separator)
    return df.shape[0]


def csv_num_col(f: Path):
    assert f.exists()
    df = pd.read_csv(f, sep=csv_separator)
    return df.shape[1]


def basic_check_on_df(f: Path) -> pd.DataFrame:
    """Check if a file exists, open it as a pandas dataframe to check that it has meaningful data :
        - no null value
        - not only zeros
    Returns the dataframe for potential further investigation

    Args:
        f (Path): path to input csv file

    Returns:
        pd.DataFrame: read dataframe
    """
    assert (f).is_file()
    df = pd.read_csv(f, dtype={"class": str}, sep=csv_separator)
    assert not df.isnull().values.any()
    assert np.count_nonzero(df)  # To check that not all values == 0
    return df


def hostname():
    return socket.gethostname()


def execute_gpao_client(tags: str = "docker", num_thread: int = 1):
    """Execute a GPAO client on this host"""
    parameters = {
        "url_api": worker.GPAO_API_URL,
        "hostname": hostname(),
        "tags": tags,
        "autostart": "2",
        "mode_exec_and_quit": True,
        "suffix": "",
    }
    worker.exec_multiprocess(num_thread, parameters)


def delete_projects_starting_with(project_name: str):
    """Delete all projects that have this name"""
    response = worker.send_request(worker.GPAO_API_URL + "projects", "GET")
    id_list = []
    if response and response.json():
        for proj in response.json():
            if proj["project_name"].startswith(project_name):
                proj_id = proj["project_id"]
                id_list.append(proj_id)
    json_ids = {"ids": id_list}
    response = requests.delete(worker.GPAO_API_URL + "projects/delete", json=json_ids)
