import json
from pathlib import Path
from typing import List

from gpao.builder import handler
from gpao.project import Job, Project


def save_projects_as_json(projects: List[Project], dest: Path):
    """Save GPAO projects as json
    without reorganizing dependencies (as it was already done by 'builder.send_to_api`)
    cf. https://github.com/ign-gpao/builder-python/issues/10

    Args:
        projects (List[Project]): gpao projects to save
        dest (Path): Path to the output json file
    """
    json_gpao = {"projects": projects}
    with open(dest, "w", encoding="utf-8") as fjson:
        json.dump(json_gpao, fjson, default=handler, ensure_ascii=False, indent=4)


def add_dependency_to_jobs(jobs: List[Job], dependency: Job | None) -> None:
    if dependency is not None:
        for job in jobs:
            job.add_dependency(dependency)
