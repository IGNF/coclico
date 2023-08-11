from coclico._version import __version__
import docker
from gpao.project import Project
import logging
from pathlib import Path
import pytest
import requests


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


@pytest.fixture(scope="session")
def use_gpao_server():
    client = docker.from_env()  # show running containers
    containers_tags = [cl.image.attrs["RepoTags"] for cl in client.containers.list()]
    containers_tags_flat = [item for sublist in containers_tags for item in sublist]

    logging.info("Check that a gpao server is started on localhost for tests that leverage GPAO")
    images_names = [val.split(":")[0] for val in containers_tags_flat]
    if not set(["gpao/monitor-gpao", "gpao/api-gpao", "gpao/database"]).issubset(images_names):
        raise Exception(
            "Tests with GPAO require a gpao server to run in docker images on the local machine"
            + " None has been found. Aborting."
        )

    # Check that there is a docker image with the same version as the current one
    logging.info("Check that there is a docker image with the same version as the current one")
    images_list = [im.attrs["RepoTags"] for im in client.images.list()]
    images_list_flat = [item for sublist in images_list for item in sublist]

    coclico_image = f"lidar_hd/coclico:{__version__}"
    if not coclico_image in images_list_flat:
        logging.info(f"Docker images are: {images_list_flat}")
        raise Exception(f"Could not find image {coclico_image} on computer. Aborting")
    yield


@pytest.fixture(autouse=True)
def reset_gpao_project(tmpdir):
    """Fixture to execute before each test is run"""
    Project.reset()

    yield  # this is where the testing happens
