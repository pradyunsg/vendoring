import sys
from pathlib import Path
from typing import Callable, NamedTuple, Optional

import click

from vendoring.configuration import load_configuration
from vendoring.errors import VendoringError
from vendoring.sync import run_sync
from vendoring.tasks.update import update_requirements
from vendoring.ui import UI

_EntryPoint = Callable[..., None]
_Param = Callable[[_EntryPoint], _EntryPoint]


class _Template(NamedTuple):
    # Arguments
    location: _Param
    package: _Param
    # Options
    verbose: _Param


template = _Template(
    location=click.argument(
        "location",
        default=None,
        required=False,
        type=click.Path(exists=True, file_okay=False, resolve_path=True),
    ),
    package=click.argument("package", default=None, required=False, type=str),
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
        run_sync(config)
    except VendoringError as e:
        UI.show_error(e)
        sys.exit(1)


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
        sys.exit(1)
