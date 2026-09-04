"""Core logic of the sync task."""

from vendoring.configuration import Configuration
from vendoring.tasks.cleanup import cleanup_existing_vendored
from vendoring.tasks.license import fetch_licenses
from vendoring.tasks.stubs import generate_stubs
from vendoring.tasks.vendor import vendor_libraries
from vendoring.ui import UI


def run_sync(config: Configuration, ignore_space_change: bool = False) -> None:
    with UI.task("Clean existing libraries"):
        cleanup_existing_vendored(config)
    with UI.task("Add vendored libraries"):
        libraries = vendor_libraries(config, ignore_space_change=ignore_space_change)
    with UI.task("Fetch licenses"):
        fetch_licenses(config)
    with UI.task("Generate static-typing stubs"):
        generate_stubs(config, libraries)
