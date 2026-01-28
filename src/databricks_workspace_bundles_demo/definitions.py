from pathlib import Path

from dagster import Definitions, definitions, load_from_defs_folder

from .orchestration import orchestration_defs


@definitions
def defs():
    # Load component definitions from YAML
    component_defs = load_from_defs_folder(path_within_project=Path(__file__).parent)

    # Merge with orchestration (jobs, schedules, sensors)
    return Definitions.merge(component_defs, orchestration_defs)
