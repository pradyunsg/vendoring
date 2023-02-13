"""Interactive mode, for updating all packages.
"""

from __future__ import annotations

import subprocess
from typing import Literal

import click as _click
from packaging.version import Version

from vendoring.configuration import Configuration
from vendoring.errors import VendoringError
from vendoring.sync import run_sync
from vendoring.tasks.update import (
    PinnedPackageInfo,
    determine_latest_release,
    parse_pinned_packages,
)
from vendoring.ui import UI

Action = Literal["skip", "incomplete", "done"]


class InteractionState:
    """Manages the state of the interactive session.

    This handles the following:
    - Reading the requirements file
    - Writing the requirements file
    - Reading the "state" file
    - Keeping track of the current package, in memory and in the "state" file
    - Writing the "state" file
    - Cleaning up the "state" file
    """

    def __init__(self, config: Configuration) -> None:
        self._requirements = config.requirements
        self._state_file = (
            config.base_directory
            / ".vendoring_cache"
            / "do-not-commit.interactive.current-package"
        )

        packages = parse_pinned_packages(self._requirements)
        self._packages = {p.name: p for p in packages}
        self._package_order = [p.name for p in packages]

        self._current_package: str | None = None
        if self._state_file.exists():
            self._current_package = self._state_file.read_text()

    @property
    def packages(self) -> tuple[tuple[str, str], ...]:
        """Return the list of packages."""
        return tuple((p.name, p.version) for p in self._packages.values())

    @property
    def resuming_from(self) -> PinnedPackageInfo | None:
        """Return the package we are resuming from."""
        if self._current_package is None:
            return None

        if self._current_package not in self._packages:
            raise VendoringError(
                "The package to 'resume from' is not in requirements file\n"
                f"package_name: {self._current_package}\n"
                f"packages: {list(self._packages)}\n"
                "Please run with `--from-start` to reset the state."
            )
        return self._packages[self._current_package]

    def get_info(self, package: list[str]) -> list[PinnedPackageInfo]:
        return [self._packages[p] for p in package]

    def update(self, package_name: str, version: str) -> None:
        """Update the state of the session."""
        self._packages[package_name].version = version
        with self._requirements.open("w", encoding="utf-8") as f:
            f.writelines(f"{self._packages[p]}\n" for p in self._package_order)

        self._current_package = package_name
        if not self._state_file.parent.exists():
            self._state_file.parent.mkdir()
        self._state_file.write_text(package_name)

    def cleanup(self) -> None:
        if not self._state_file.exists():
            return

        self._state_file.unlink()
        self._state_file.parent.rmdir()


def git(*args: str) -> None:
    """Run a git command."""
    cmd = ["git", *args]

    UI.log(" ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def do_one_update(config: Configuration, *, name: str, version: str) -> None:
    """Perform the update of a single package."""
    run_sync(config)

    # Determine the correct message
    message = f"Upgrade {name} to {version}"
    # Write our news fragment
    news_file = config.base_directory / "news" / (name + ".vendor.rst")
    news_file.write_text(message + "\n")  # "\n" appeases end-of-line-fixer

    # Commit the changes
    git("add", str(news_file))
    git("commit", "-m", message)


def determine_packages(
    packages: tuple[tuple[str, str], ...],
    *,
    resuming_from: PinnedPackageInfo | None,
    skip: list[str],
    only: list[str],
) -> list[str]:
    """Determine the packages to update."""
    if resuming_from is not None:
        if resuming_from.name in skip:
            raise VendoringError(
                f"Cannot resume from {resuming_from!r} as it is in the skip list"
            )
        if only and resuming_from.name not in only:
            raise VendoringError(
                f"Cannot resume from {resuming_from!r} as it is not in the only list"
            )

    if only:
        known = {package[0] for package in packages}
        for name in only:
            if name not in known:
                raise VendoringError(
                    f"Package {name!r} is not in the requirements file"
                )
        return only

    if skip:
        return [package[0] for package in packages if package[0] not in skip]

    return [package[0] for package in packages]


def interactive_updates(
    config: Configuration, *, skip: list[str], only: list[str], from_start: bool
) -> None:
    """Interactive mode, for updating all packages."""
    with UI.task("Read incoming requirements"):
        state = InteractionState(config)

    if from_start:
        state.cleanup()

    resuming_from = state.resuming_from
    package_names = determine_packages(
        state.packages, resuming_from=resuming_from, skip=skip, only=only
    )

    def _present(package_info: PinnedPackageInfo, *, prefix: str | None = None) -> None:
        real_prefix = f"{prefix} " if prefix else ""
        UI.log(
            f"{real_prefix}"
            f"{_click.style(package_info.name, fg='green')} "
            f"{_click.style('==', fg='blue')} "
            f"{_click.style(package_info.version, fg='magenta')}"
        )

    if resuming_from is not None:
        _present(resuming_from, prefix="Resuming from")
        with UI.indent():
            do_one_update(
                config, name=resuming_from.name, version=resuming_from.version
            )
        UI.log(f"Processing remaining {len(package_names)} package(s)")
    else:
        UI.log(f"Processing {len(package_names)} package(s)")

    with UI.indent():
        for package_info in state.get_info(package_names):
            _present(package_info)
            with UI.indent():
                latest_version = determine_latest_release(package_info.name)
                if Version(latest_version) <= Version(package_info.version):
                    UI.log("Already up-to-date")
                    continue

                state.update(package_info.name, latest_version)
                do_one_update(config, name=package_info.name, version=latest_version)

    UI.log("All done, removing marker file")
    state.cleanup()
