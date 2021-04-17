"""Logic for updating a vendoring-related requirements.txt file.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import requests
from packaging.version import VERSION_PATTERN, Version

from vendoring.configuration import Configuration
from vendoring.errors import RequirementsError, VendoringError
from vendoring.ui import UI

_PATTERN = r"""
^
    (?P<prefix>\s*)
    (?P<name>[A-Z][A-Z0-9\-._]*)
    \s*==\s*
    (?P<version>
        version regex here
    )
    (?P<suffix>.*)
$
""".replace(
    "version regex here", VERSION_PATTERN
)

_REGEX = re.compile(_PATTERN, re.VERBOSE | re.IGNORECASE)


@dataclass
class PinnedPackageInfo:
    name: str
    version: str
    # Preserve formatting!
    prefix: str
    suffix: str

    def __str__(self) -> str:
        return f"{self.prefix}{self.name}=={self.version}{self.suffix}"


def parse_pinned_packages(requirements: Path) -> List[PinnedPackageInfo]:
    failed = []
    retval = []
    all_lines = requirements.read_text().splitlines()
    for i, line in enumerate(all_lines):
        match = _REGEX.match(line)
        if match is None:
            failed.append((i + 1, line))
            continue

        values = match.group("name", "version", "prefix", "suffix")
        retval.append(PinnedPackageInfo(*values))

    if failed:
        raise RequirementsError(failed)

    return retval


def determine_latest_release(name: str) -> str:
    UI.log(f"Determining latest version for {name}...")

    try:
        r = requests.get(f"https://pypi.org/pypi/{name}/json")
        retval = str(r.json()["info"]["version"])
    except Exception as e:
        raise VendoringError(f"Could not determine latest version for {name}: {e!r}")

    UI.log(f"Got {retval}")
    return retval


def update_requirements(config: Configuration, package: Optional[str]) -> None:
    requirements = config.base_directory / config.requirements

    packages = parse_pinned_packages(requirements)
    for pkg in packages:
        if package is None or pkg.name == package:
            latest = determine_latest_release(pkg.name)
            if Version(latest) != Version(pkg.version):
                pkg.version = latest

    UI.log(f"Rewriting {requirements}")
    with requirements.open("w", encoding="utf-8") as f:
        f.writelines(f"{p}\n" for p in packages)
