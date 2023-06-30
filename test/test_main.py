import pytest
import os
import requests

from coclico import main

remote_url = "https://github.com/IGNF/coclico-data/blob/main/"
local_path = "./data/"

files = [
    "test0/ref/Semis_2021_0919_6424_LA93_IGN69.laz",
    "test0/niv1/Semis_2021_0919_6424_LA93_IGN69.laz",
    "test0/niv2/Semis_2021_0919_6424_LA93_IGN69.laz",
    "test0/niv3/Semis_2021_0919_6424_LA93_IGN69.laz",
    "test0/niv4/Semis_2021_0919_6424_LA93_IGN69.laz"
]

def download(remote_file, local_file):
    response = requests.get(remote_file,verify=True, allow_redirects=True)
    with open(local_file,'wb') as fout:
        fout.write(response.content)


def setup_module():

    os.makedirs("./data/test0/ref/", exist_ok=True)
    os.makedirs("./data/test0/niv1/", exist_ok=True)
    os.makedirs("./data/test0/niv2/", exist_ok=True)
    os.makedirs("./data/test0/niv3/", exist_ok=True)
    os.makedirs("./data/test0/niv4/", exist_ok=True)

    for file in files:
        local_file = os.path.join(local_path, file)
        if not os.path.exists(local_file):
            download(os.path.join(remote_url, file), local_file)

def test_compare_test0():

    c1 = "./data/test0/C1/"
    c2 = "./data/test0/C2/"
    ref = "./data/test0/Ref/"

    main.compare(c1, c2, ref)
