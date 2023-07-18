import os
from pathlib import Path


def compare(c1: str, c2: str, ref: str, out: str):
    print(f"Compare C1: {c1} to Ref: {ref} AND C2:{c2} to {ref} in out {out}")
    mpap0_out = os.path.join(out, "C1_Ref/MPAP0")

    os.makedirs(mpap0_out, exist_ok=True)
    ref_files_stem = [Path(f).stem for f in os.listdir(ref) if f.lower().endswith(("las", "laz"))]

    for ref_file in ref_files_stem:
        json_file = os.path.join(mpap0_out, ref_file + ".json")
        os.system("touch " + json_file)
