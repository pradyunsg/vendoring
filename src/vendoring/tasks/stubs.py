"""Logic for adding static typing related stubs.

We autogenerate `.pyi` stub files for the vendored modules. The stub files
are merely `from ... import *`, but that seems to be enough for mypy to find
the correct declarations.
"""

import os
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from vendoring.configuration import Configuration


def determine_stub_files(
    lib: str, typing_stubs: Dict[str, List[str]]
) -> Iterable[Tuple[str, str]]:
    # There's no special handling needed -- a <libname>.pyi file is good enough
    if lib not in typing_stubs:
        yield lib + ".pyi", lib
        return

    # Need to generate the given stubs, with the correct import names
    for import_name in typing_stubs[lib]:
        rel_location = import_name.replace(".", os.sep) + ".pyi"

        # Writing an __init__.pyi file -> don't import from `pkg.__init__`
        if import_name.endswith(".__init__"):
            import_name = import_name[:-9]

        yield rel_location, import_name


def write_stub(stub_location: Path, import_name: str) -> None:
    # Create the parent directories if needed.
    if not stub_location.parent.exists():
        stub_location.parent.mkdir()

    # Write `from ... import *` in the stub file.
    stub_location.write_text("from %s import *" % import_name)


def generate_stubs(config: Configuration, libraries: List[str]) -> None:
    destination = config.destination
    typing_stubs = config.typing_stubs

    for lib in libraries:
        for rel_location, import_name in determine_stub_files(lib, typing_stubs):
            stub_location = destination / rel_location
            write_stub(stub_location, import_name)
