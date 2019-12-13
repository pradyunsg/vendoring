from pathlib import Path

import click

from vendoring.configuration import load_configuration
from vendoring.errors import VendoringError
from vendoring.tasks.cleanup import cleanup_existing_vendored
from vendoring.tasks.license import fetch_licenses
from vendoring.tasks.stubs import generate_stubs
from vendoring.tasks.vendor import vendor_libraries
from vendoring.ui import UI


@click.group()
def main() -> None:
    pass


@main.command()
@click.option("-v", "--verbose", is_flag=True)
@click.argument(
    "location",
    default=".",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
)
def sync(verbose: bool, location: Path) -> None:
    UI.verbose = verbose

    location = Path(location)
    try:
        with UI.task("Load configuration"):
            config = load_configuration(location)

        with UI.task("Clean existing libraries"):
            cleanup_existing_vendored(config)

        with UI.task("Add vendored libraries"):
            libraries = vendor_libraries(config)

        if config.include_licenses:
            with UI.task("Fetch licenses"):
                fetch_licenses(config)

        if config.include_stubs:
            with UI.task("Generate static-typing stubs"):
                generate_stubs(config, libraries)
    except VendoringError as e:
        UI.show_error(e)
