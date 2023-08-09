import pytest
import requests
from pathlib import Path
import logging


remote_url = "https://raw.githubusercontent.com/IGNF/coclico-data/main/"
local_path = Path("./data/")


files = [
    "test1/niv1/tile_splitted_2818_32247.laz",
    "test1/niv1/tile_splitted_2818_32248.laz",
    "test1/niv1/tile_splitted_2819_32247.laz",
    "test1/niv1/tile_splitted_2819_32248.laz",
    "test1/niv2/tile_splitted_2818_32247.laz",
    "test1/niv2/tile_splitted_2818_32248.laz",
    "test1/niv2/tile_splitted_2819_32247.laz",
    "test1/niv2/tile_splitted_2819_32248.laz",
    "test1/niv3/tile_splitted_2818_32247.laz",
    "test1/niv3/tile_splitted_2818_32248.laz",
    "test1/niv3/tile_splitted_2819_32247.laz",
    "test1/niv3/tile_splitted_2819_32248.laz",
    "test1/niv4/tile_splitted_2818_32247.laz",
    "test1/niv4/tile_splitted_2818_32248.laz",
    "test1/niv4/tile_splitted_2819_32247.laz",
    "test1/niv4/tile_splitted_2819_32248.laz",
    "test1/ref/tile_splitted_2818_32247.laz",
    "test1/ref/tile_splitted_2818_32248.laz",
    "test1/ref/tile_splitted_2819_32247.laz",
    "test1/ref/tile_splitted_2819_32248.laz",
]


def download_file(remote_file: Path, local_file: Path):
    response = requests.get(str(remote_file), verify=True, allow_redirects=True)
    with open(local_file, "wb") as fout:
        fout.write(response.content)


def download_test1_data():
    test1 = Path("./data/test1")
    [(test1 / sub_dir).mkdir(parents=True, exist_ok=True) for sub_dir in ["ref", "niv1", "niv2", "niv3", "niv4"]]

    for file in files:
        local_file = local_path / file
        if not local_file.exists():
            download_file(remote_url + file, local_file)


@pytest.fixture(scope="session")
def ensure_test1_data():
    logging.info("Check that test1 data exist and download them if needed")
    if not (Path("./data/test1").is_dir()):
        download_test1_data()

    yield
