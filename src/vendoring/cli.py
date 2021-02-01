from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import click

from vendoring.configuration import load_configuration
from vendoring.errors import VendoringError
from vendoring.tasks.cleanup import cleanup_existing_vendored
from vendoring.tasks.license import fetch_licenses
from vendoring.tasks.stubs import generate_stubs
from vendoring.tasks.update import update_requirements
from vendoring.tasks.vendor import vendor_libraries
from vendoring.ui import UI

template = SimpleNamespace(
    # Arguments
    location=click.argument(
        "location",
        default=None,
        required=False,
        type=click.Path(exists=True, file_okay=False, resolve_path=True),
    ),
    package=click.argument("package", default=None, required=False, type=str),
    # Options
    verbose=click.option("-v", "--verbose", is_flag=True),
)


@click.group()
def main() -> None:
    pass


@main.command()
@template.verbose
@template.location
def sync(verbose: bool, location: Optional[str]) -> None:
    UI.verbose = verbose
    if location is None:
        project_path = Path()
    else:
        project_path = Path(location)

    print(f"Working in {project_path}")

    try:
        with UI.task("Load configuration"):
            config = load_configuration(project_path)

        with UI.task("Clean existing libraries"):
            cleanup_existing_vendored(config)

        with UI.task("Add vendored libraries"):
            libraries = vendor_libraries(config)

        with UI.task("Fetch licenses"):
            fetch_licenses(config)

        with UI.task("Generate static-typing stubs"):
            generate_stubs(config, libraries)
    except VendoringError as e:
        UI.show_error(e)


@main.command()
@template.verbose
@template.location
@template.package
def update(verbose: bool, location: Path, package: Optional[str]) -> None:
    UI.verbose = verbose
    location = Path(location)

    try:
        with UI.task("Load configuration"):
            config = load_configuration(location)
        with UI.task("Updating requirements"):
            update_requirements(config, package)
    except VendoringError as e:
        UI.show_error(e)
