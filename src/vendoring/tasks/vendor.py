"""Logic for adding/vendoring the relevant libraries.
"""

import re

from vendoring.utils import run
from vendoring.tasks.cleanup import remove_all as _remove_all
from vendoring.ui import UI


def download_libraries(requirements_path, target_dir):
    command = [
        "pip",
        "install",
        "-t",
        str(target_dir),
        "-r",
        str(requirements_path),
        "--no-compile",
        # We use --no-deps because we want to ensure that dependencies are provided.
        # This includes all dependencies recursively up the chain.
        "--no-deps",
    ]
    run(command, working_directory=None)


def remove_unnecessary_items(target_dir, drop_paths):
    # Cleanup any metadata directories created.
    _remove_all(target_dir.glob("*.dist-info"))
    _remove_all(target_dir.glob("*.egg-info"))

    for location in drop_paths:
        if "*" in location:
            _remove_all(target_dir.glob(location))
        else:
            _remove_all([target_dir / location])


def rewrite_file_imports(
    item, target_namespace, vendored_libs, additional_import_substitutions
):
    """Rewrite 'import xxx' and 'from xxx import' for vendored_libs.
    """

    text = item.read_text(encoding="utf-8")

    # Configurable rewriting of lines.
    for pattern, substitution in additional_import_substitutions:
        text = re.sub(pattern, substitution, text)

    for lib in vendored_libs:
        text = re.sub(
            r"(\n\s*|^)import %s(\n\s*)" % lib,
            rf"\1from {target_namespace} import %s\2" % lib,
            text,
        )
        text = re.sub(
            r"(\n\s*|^)from %s(\.|\s+)" % lib,
            rf"\1from {target_namespace}.%s\2" % lib,
            text,
        )

    item.write_text(text, encoding="utf-8")


def rewrite_imports(
    target_dir, vendored_libs, target_namespace, additional_import_substitutions
):
    for item in target_dir.iterdir():
        if item.is_dir():
            rewrite_imports(
                item, target_namespace, vendored_libs, additional_import_substitutions
            )
        elif item.name.endswith(".py"):
            rewrite_file_imports(
                item, target_namespace, vendored_libs, additional_import_substitutions
            )


def detect_vendored_libs(target_dir, files_to_skip):
    retval = []
    for item in target_dir.iterdir():
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


def _apply_patch(patch_file_path, working_directory):
    run(
        ["git", "apply", "--verbose", str(patch_file_path)],
        working_directory=working_directory,
    )


def apply_patches(patch_dir, working_directory):
    for patch in patch_dir.glob("*.patch"):
        _apply_patch(patch_dir / patch, working_directory)


def vendor_libraries(config):
    target_dir = config.target_dir

    # Download the relevant libraries.
    download_libraries(config.requirements_path, target_dir)

    # Cleanup unnecessary directories/files created.
    remove_unnecessary_items(target_dir, config.drop_paths)

    # Detect what got downloaded.
    vendored_libs = detect_vendored_libs(target_dir, config.ignore_files)

    # Rewrite the imports we want changed.
    rewrite_imports(
        target_dir,
        vendored_libs,
        config.target_namespace,
        config.additional_import_substitutions,
    )

    # Apply user provided patches.
    apply_patches(config.patches_dir, working_directory=config.base_directory)

    return vendored_libs
