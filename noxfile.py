"""Development automation
"""

from glob import glob

import nox

nox.options.sessions = ["lint", "test"]


@nox.session(python="3.8")
def lint(session):
    session.install("pre-commit")

    if session.posargs:
        args = session.posargs + ["--all-files"]
    else:
        args = ["--all-files", "--show-diff-on-failure"]

    session.run("pre-commit", "run", "--all-files", *args)


@nox.session(python="3.8")
def test(session):
    session.install("pytest", "pytest-xdist")
    session.install(".")

    session.run("pytest", "-n", "auto", *session.posargs)


@nox.session
def release(session):
    session.install("twine", "flit")

    session.run("flit", "build")
    session.run("twine", "check", *glob("dist/*"))
    session.run("flit", "publish")
