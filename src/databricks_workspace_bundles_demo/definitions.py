from pathlib import Path

from dagster import definitions, load_from_defs_folder


@definitions
def defs():
    # Load all definitions from defs folder (YAML components + Python modules)
    return load_from_defs_folder(path_within_project=Path(__file__).parent)
