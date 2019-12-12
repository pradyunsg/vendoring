import shlex
import shutil
import subprocess

from vendoring.ui import UI


def remove_all(items_to_cleanup):
    for item in items_to_cleanup:
        if item.is_dir():
            shutil.rmtree(str(item))
        else:
            item.unlink()


def run(command, *, working_directory):
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
