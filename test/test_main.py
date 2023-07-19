import os
import requests
from coclico import main
from pathlib import Path

remote_url = "https://github.com/IGNF/coclico-data/blob/main/"
local_path = "./data/"

files = [
    "test0/ref/Semis_2021_0919_6424_LA93_IGN69.laz",
    "test0/niv1/Semis_2021_0919_6424_LA93_IGN69.laz",
    "test0/niv2/Semis_2021_0919_6424_LA93_IGN69.laz",
    "test0/niv3/Semis_2021_0919_6424_LA93_IGN69.laz",
    "test0/niv4/Semis_2021_0919_6424_LA93_IGN69.laz",
]


def download(remote_file, local_file):
    response = requests.get(remote_file, verify=True, allow_redirects=True)
    with open(local_file, "wb") as fout:
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


def test_compare_to_ref_test0():
    c1 = Path("./data/test0/niv1/")
    ref = Path("./data/test0/ref/")
    out = Path("./tmp/test0/compare_to_ref")

    main.compare_to_ref(c1, ref, out)

    ref_files_stem = [f.stem for f in ref.iterdir() if f.suffix.lower() in (".las", ".laz")]
    for ref_file in ref_files_stem:
        c1_ref_mpapO_json = out / "mpap0" / f"{ref_file}.json"
        assert c1_ref_mpapO_json.is_file()


def test_compare_test0():
    c1 = Path("./data/test0/niv1/")
    c2 = Path("./data/test0/niv4/")
    ref = Path("./data/test0/ref/")
    out = Path("./tmp/test0/compare")

    main.compare(c1, c2, ref, out)

    ref_files_stem = [f.stem for f in ref.iterdir() if f.suffix.lower() in (".las", ".laz")]
    for ref_file in ref_files_stem:
        c1_ref_mpapO_json = out / "c1_ref" / "mpap0" / f"{ref_file}.json"
        assert c1_ref_mpapO_json.is_file()
        c2_ref_mpapO_json = out / "c2_ref" / "mpap0" / f"{ref_file}.json"
        assert c2_ref_mpapO_json.is_file()
