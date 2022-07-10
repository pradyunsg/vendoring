"""Development automation
"""

import re
import subprocess
from glob import glob
from pathlib import Path
from time import time

import nox

nox.options.sessions = ["lint", "test"]


@nox.session(python="3.8")
def lint(session):
    session.install("pre-commit")

    if session.posargs:
        args = session.posargs + ["--all-files"]
    else:
        args = ["--all-files", "--show-diff-on-failure"]

    session.run("pre-commit", "run", *args)


@nox.session(python="3.8")
def test(session):
    session.install("flit")
    session.run(
        "flit", "install", "-s", "--deps", "production", "--extra", "test", silent=True
    )

    session.run("pytest", *session.posargs)


def get_version_from_arguments(arguments):
    """Checks the arguments passed to `nox -s release`.

    If there is only 1 argument that looks like a version, returns the argument.
    Otherwise, returns None.
    """
    if len(arguments) != 1:
        return None

    version = arguments[0]

    parts = version.split(".")
    if len(parts) != 3:
        # Not of the form: MAJOR.MINOR.PATCH
        return None

    if not all(part.isdigit() for part in parts):
        # Not all segments are integers.
        return None

    # All is good.
    return version


def perform_git_checks(session, version_tag):
    # Ensure we're on master branch for cutting a release.
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        encoding="utf-8",
    )
    if result.stdout != "master\n":
        session.error(f"Not on master branch: {result.stdout!r}")

    # Ensure there are no uncommitted changes.
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, encoding="utf-8"
    )
    if result.stdout:
        print(result.stdout)
        session.error("The working tree has uncommitted changes")

    # Ensure this tag doesn't exist already.
    result = subprocess.run(
        ["git", "rev-parse", version_tag], capture_output=True, encoding="utf-8"
    )
    if not result.returncode:
        session.error(f"Tag already exists! {version_tag} -- {result.stdout!r}")

    # Back up the current git reference, in a tag that's easy to clean up.
    _release_backup_tag = "auto/release-start-" + str(int(time()))
    session.run("git", "tag", _release_backup_tag, external=True)


def bump(session, *, version, file, kind):
    session.log(f"Bump version to {version!r}")
    contents = file.read_text()
    new_contents = re.sub(
        '__version__ = "(.+)"', f'__version__ = "{version}"', contents
    )
    file.write_text(new_contents)

    session.log("git commit")
    subprocess.run(["git", "add", str(file)])
    subprocess.run(["git", "commit", "-m", f"Bump for {kind}"])


@nox.session
def release(session):
    package_name = "vendoring"
    release_version = get_version_from_arguments(session.posargs)
    if not release_version:
        session.error("Usage: nox -s release -- MAJOR.MINOR.PATCH")

    # Do sanity check about the state of the git repository
    perform_git_checks(session, release_version)

    # Install release dependencies
    session.install("twine", "flit")
    version_file = Path(f"src/{package_name}/__init__.py")

    # Bump for release
    bump(session, version=release_version, file=version_file, kind="release")

    # Tag the release commit
    session.run("git", "tag", "-s", release_version, external=True)

    # Bump for development
    major, minor, patch = map(int, release_version.split("."))
    next_version = f"{major}.{minor}.{patch + 1}.dev0"

    bump(session, version=next_version, file=version_file, kind="development")

    # Checkout the git tag
    session.run("git", "checkout", "-q", release_version, external=True)

    # Build the distribution
    session.run("flit", "build")
    files = glob(f"dist/{package_name}-{release_version}*")
    assert len(files) == 2

    # Get back out into master
    session.run("git", "checkout", "-q", "master", external=True)

    # Check and upload distribution files
    session.run("twine", "check", *files)

    # Upload the distribution
    session.run("twine", "upload", *files)

    # Push the commits and tag
    session.run("git", "push", "origin", "master", release_version, external=True)
