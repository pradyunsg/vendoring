"""Logic for adding/vendoring the relevant libraries.
"""

import re
from pathlib import Path
from typing import Dict, List

from vendoring.configuration import Configuration
from vendoring.ui import UI
from vendoring.utils import remove_all as _remove_all
from vendoring.utils import run


def download_libraries(requirements: Path, destination: Path) -> None:
    command = [
        "pip",
        "install",
        "-t",
        str(destination),
        "-r",
        str(requirements),
        "--no-compile",
        # We use --no-deps because we want to ensure that dependencies are provided.
        # This includes all dependencies recursively up the chain.
        "--no-deps",
    ]
    run(command, working_directory=None)


def remove_unnecessary_items(destination: Path, drop_paths: List[str]) -> None:
    # Cleanup any metadata directories created.
    _remove_all(destination.glob("*.dist-info"))
    _remove_all(destination.glob("*.egg-info"))

    for location in drop_paths:
        if "*" in location:
            _remove_all(destination.glob(location))
        else:
            _remove_all([destination / location])


def rewrite_file_imports(
    item: Path,
    namespace: str,
    vendored_libs: List[str],
    additional_substitutions: List[Dict[str, str]],
) -> None:
    """Rewrite 'import xxx' and 'from xxx import' for vendored_libs."""

    text = item.read_text(encoding="utf-8")

    # Configurable rewriting of lines.
    for di in additional_substitutions:
        pattern, substitution = di["match"], di["replace"]
        text = re.sub(pattern, substitution, text)

    # If an empty namespace is provided, we don't rewrite imports.
    if namespace != "":
        for lib in vendored_libs:
            text = re.sub(
                rf"^(\s*)import {lib}(\s|$)",
                rf"\1from {namespace} import {lib}\2",
                text,
                flags=re.MULTILINE,
            )
            text = re.sub(
                rf"^(\s*)import {lib}(\.\S+)(?=\s+as)",
                rf"\1import {namespace}.{lib}\2",
                text,
                flags=re.MULTILINE,
            )
            text = re.sub(
                rf"^(\s*)from {lib}(\.|\s)",
                rf"\1from {namespace}.{lib}\2",
                text,
                flags=re.MULTILINE,
            )

    item.write_text(text, encoding="utf-8")


def rewrite_imports(
    destination: Path,
    namespace: str,
    vendored_libs: List[str],
    additional_substitutions: List[Dict[str, str]],
) -> None:
    for item in destination.iterdir():
        if item.is_dir():
            rewrite_imports(item, namespace, vendored_libs, additional_substitutions)
        elif item.name.endswith(".py"):
            rewrite_file_imports(
                item, namespace, vendored_libs, additional_substitutions
            )


def detect_vendored_libs(destination: Path, files_to_skip: List[str]) -> List[str]:
    retval = []
    for item in destination.iterdir():
        if item.is_dir():
            retval.append(item.name)
        elif item.name.endswith(".pyi"):  # generated stubs
            continue
        elif item.name not in files_to_skip:
            if not item.name.endswith(".py"):
                UI.warn(f"Got unexpected non-Python file: {item}")
                continue
            retval.append(item.name[:-3])
    return retval


def _apply_patch(patch_file_path: Path, working_directory: Path) -> None:
    run(
        ["git", "apply", "--verbose", str(patch_file_path)],
        working_directory=working_directory,
    )


def apply_patches(patch_dir: Path, working_directory: Path) -> None:
    for patch in patch_dir.glob("*.patch"):
        _apply_patch(patch, working_directory)


def vendor_libraries(config: Configuration) -> List[str]:
    destination = config.destination

    # Download the relevant libraries.
    download_libraries(config.requirements, destination)

    # Cleanup unnecessary directories/files created.
    remove_unnecessary_items(destination, config.drop_paths)

    # Detect what got downloaded.
    vendored_libs = detect_vendored_libs(destination, config.protected_files)

    # Rewrite the imports we want changed.
    rewrite_imports(
        destination,
        config.namespace,
        vendored_libs,
        config.substitute,
    )

    # Apply user provided patches.
    if config.patches_dir:
        apply_patches(config.patches_dir, working_directory=config.base_directory)

    return vendored_libs
