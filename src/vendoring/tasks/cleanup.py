"""Logic for cleaning up already vendored files.
"""

from pathlib import Path
from typing import Iterable, List

from vendoring.configuration import Configuration
from vendoring.utils import remove_all


def determine_items_to_remove(
    destination: Path, *, files_to_skip: List[str]
) -> Iterable[Path]:
    if not destination.exists():
        # Folder does not exist, nothing to cleanup.
        return

    for item in destination.iterdir():
        if item.is_dir():
            # Directory
            yield item
        elif item.name not in files_to_skip:
            # File, not in files_to_skip
            yield item


def cleanup_existing_vendored(config: Configuration) -> None:
    """Cleans up existing vendored files in `destination` directory."""
    destination = config.destination
    items = determine_items_to_remove(destination, files_to_skip=config.protected_files)

    # TODO: log how many items were removed.
    remove_all(items)
