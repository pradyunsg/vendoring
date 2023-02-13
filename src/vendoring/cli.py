import sys
from pathlib import Path
from typing import Callable, NamedTuple, Optional

import click

from vendoring.configuration import load_configuration
from vendoring.errors import VendoringError
from vendoring.interactive import interactive_updates
from vendoring.sync import run_sync
from vendoring.tasks.update import update_requirements
from vendoring.ui import UI

_EntryPoint = Callable[..., None]
_Param = Callable[[_EntryPoint], _EntryPoint]


class _Template(NamedTuple):
    # Arguments
    package: _Param
    # Options
    verbose: _Param


template = _Template(
    package=click.argument("package", default=None, required=False, type=str),
    verbose=click.option("-v", "--verbose", is_flag=True),
)


@click.group()
def main() -> None:
    pass


@main.command()
@template.verbose
def sync(verbose: bool) -> None:
    """Vendor libraries as described in lockfile"""
    UI.verbose = verbose
    project_path = Path()

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
@template.package
def update(verbose: bool, package: Optional[str]) -> None:
    """Update a single package version"""
    UI.verbose = verbose
    project_path = Path()

    try:
        with UI.task("Load configuration"):
            config = load_configuration(project_path)
        with UI.task("Updating requirements"):
            update_requirements(config, package)
    except VendoringError as e:
        UI.show_error(e)
        sys.exit(1)


@main.command("update-interactive")
@click.option("--skip", help="Skip named packages", multiple=True)
@click.option("--only", help="Only update named packages", multiple=True)
@click.option(
    "--from-start",
    help="Start from the beginning, ignoring existing markers",
    is_flag=True,
)
@template.verbose
def update_interactive(
    verbose: bool, skip: list[str], only: list[str], from_start: bool
) -> None:
    """Update all package versions, interactively"""
    UI.verbose = verbose
    project_path = Path()

    try:
        with UI.task("Load configuration"):
            config = load_configuration(project_path)
        interactive_updates(config, skip=skip, only=only, from_start=from_start)
    except VendoringError as e:
        UI.show_error(e)
        sys.exit(1)
