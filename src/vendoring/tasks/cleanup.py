"""Logic for cleaning up already vendored files.
"""

from pathlib import Path
from typing import Iterable, List

from vendoring.configuration import Configuration
from vendoring.utils import remove_all


def determine_items_to_remove(
    target_dir: Path, *, files_to_skip: List[str]
) -> Iterable[Path]:
    if not target_dir.exists():
        # Folder does not exist, nothing to cleanup.
        return

    for item in target_dir.iterdir():
        if item.is_dir():
            # Directory
            yield item
        elif item.name not in files_to_skip:
            # File, not in files_to_skip
            yield item


def cleanup_existing_vendored(config: Configuration) -> None:
    """Cleans up existing vendored files in `target_dir` directory.
    """
    target_dir = config.target_dir
    items = determine_items_to_remove(target_dir, files_to_skip=config.ignore_files)

    # TODO: log how many items were removed.
    remove_all(items)
