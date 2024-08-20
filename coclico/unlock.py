from pathlib import Path
from typing import List

from gpao.project import Job
from gpao_utils.store import Store

from coclico.version import __version__


def create_unlock_job(name: str, tile_names: List[str], input_path: Path, store: Store) -> Job:
    job_name = f"{name}_unlock"
    command = f"""
docker run -t --rm --userns=host --shm-size=2gb
-v {store.to_unix(input_path)}:/input
ghcr.io/ignf/coclico:{__version__}
python -c "from pdaltools.unlock_file import unlock_file
for tile in {tile_names}: unlock_file('/input/' + tile)"
"""

    job = Job(job_name, command, tags=["docker"])

    return job
