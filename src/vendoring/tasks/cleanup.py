"""Logic for cleaning up already vendored files.
"""

import shutil


def remove_all(items_to_cleanup):
    for item in items_to_cleanup:
        if item.is_dir():
            shutil.rmtree(str(item))
        else:
            item.unlink()


def determine_items_to_remove(target_dir, *, files_to_skip):
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


def cleanup_existing_vendored(config):
    """Cleans up existing vendored files in `target_dir` directory.
    """
    target_dir = config.target_dir
    items = determine_items_to_remove(target_dir, files_to_skip=config.ignore_files)

    # TODO: log how many items were removed.
    remove_all(items)
