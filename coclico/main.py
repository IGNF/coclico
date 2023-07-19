from pathlib import Path
import os
import logging


def compare_to_ref(ci: Path, ref: Path, out: Path):
    logging.debug(f"Compare Ci: {ci} to Ref: {ref} in out {out}")
    mpap0_out = out / "mpap0"
    mpap0_out.mkdir(parents=True, exist_ok=True)

    ref_files_stem = [f.stem for f in ref.iterdir() if f.suffix.lower() in (".las", ".laz")]

    for ref_file in ref_files_stem:
        json_file = mpap0_out / f"{ref_file}.json"
        os.system(f"touch {json_file}")


def compare(c1: Path, c2: Path, ref: Path, out: Path):
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

    c1_out = out / "c1_ref"
    compare_to_ref(c1, ref, c1_out)

    c2_out = out / "c2_ref"
    compare_to_ref(c2, ref, c2_out)
