import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional

from vendoring.ui import UI


def remove_all(items_to_cleanup: Iterable[Path]) -> None:
    for item in items_to_cleanup:
        if not item.exists():
            continue
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(str(item))
        else:
            item.unlink()


def run(command: List[str], *, working_directory: Optional[Path]) -> None:
    UI.log("Running {}".format(" ".join(map(shlex.quote, command))))
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        cwd=working_directory,
    )
    while True:
        retcode = p.poll()
        line = p.stdout.readline().rstrip()

        if line:
            with UI.indent():
                UI.log(line)

        if retcode is not None:
            break
