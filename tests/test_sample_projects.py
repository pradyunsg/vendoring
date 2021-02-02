"""Test the various bits of functionality, through sample projects."""

import linecache
import os
import shutil
import sys
import traceback
from pathlib import Path

import pytest
from click.testing import CliRunner

from vendoring.cli import main

SAMPLE_PROJECTS = Path(__file__).parent / "sample-projects"


def run_vendoring_sync():
    runner = CliRunner()
    result = runner.invoke(main, ["sync"])

    # Print information to stdout, so that failures are easier to diagnose.
    print(result.output)
    if result.exc_info:
        traceback.print_exception(*result.exc_info)

    return result


def test_basic(tmp_path, monkeypatch):
    shutil.copytree(SAMPLE_PROJECTS / "basic", tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)

    result = run_vendoring_sync()
    assert result.exit_code == 0

    vendored = tmp_path / "vendored"
    assert vendored.exists()
    assert sorted(os.listdir(vendored)) == [
        "packaging",
        "packaging.pyi",
    ]

    packaging = vendored / "packaging"
    assert packaging.exists()
    assert sorted(os.listdir(packaging)) == [
        "LICENSE",
        "LICENSE.APACHE",
        "LICENSE.BSD",
        "__about__.py",
        "__init__.py",
        "_compat.py",
        "_structures.py",
        "_typing.py",
        "markers.py",
        "py.typed",
        "requirements.py",
        "specifiers.py",
        "tags.py",
        "utils.py",
        "version.py",
    ]


def test_import_rewriting(tmp_path, monkeypatch):
    shutil.copytree(SAMPLE_PROJECTS / "import_rewriting", tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)

    result = run_vendoring_sync()
    assert result.exit_code == 0

    vendored = tmp_path / "vendored"
    assert vendored.exists()
    assert sorted(os.listdir(vendored)) == [
        "retrying.LICENSE",
        "retrying.py",
        "retrying.pyi",
        "six.LICENSE",
        "six.py",
        "six.pyi",
    ]


def test_licenses(tmp_path, monkeypatch):
    shutil.copytree(SAMPLE_PROJECTS / "licenses", tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)

    result = run_vendoring_sync()
    assert result.exit_code == 0

    vendored = tmp_path / "vendored"
    assert vendored.exists()
    assert sorted(os.listdir(vendored)) == [
        "appdirs.LICENSE.txt",
        "appdirs.py",
        "appdirs.pyi",
        "msgpack",
        "msgpack.pyi",
        "six.LICENSE",
        "six.py",
        "six.pyi",
        "webencodings",
        "webencodings.pyi",
    ]

    assert (vendored / "msgpack" / "COPYING").exists()
    assert (vendored / "webencodings" / "LICENSE").exists()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Fails with 'error: corrupt patch at line 6' on `git apply` (needs fixing)",
)
def test_patches(tmp_path, monkeypatch):
    shutil.copytree(SAMPLE_PROJECTS / "patches", tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)

    result = run_vendoring_sync()
    assert result.exit_code == 0

    vendored = tmp_path / "vendored"
    assert vendored.exists()
    assert sorted(os.listdir(vendored)) == [
        "appdirs.LICENSE.txt",
        "appdirs.py",
        "appdirs.pyi",
    ]

    # Just check a single patched line
    line = linecache.getline(str(vendored / "appdirs.py"), 560)
    assert line == "        from ctypes import windll\n"


def test_protected_files(tmp_path, monkeypatch):
    shutil.copytree(SAMPLE_PROJECTS / "protected_files", tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)

    result = run_vendoring_sync()
    assert result.exit_code == 0

    vendored = tmp_path / "vendored"
    assert vendored.exists()
    assert sorted(os.listdir(vendored)) == [
        "README.md",
        "packaging",
        "packaging.pyi",
    ]


def test_transformations(tmp_path, monkeypatch):
    shutil.copytree(SAMPLE_PROJECTS / "transformations", tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)

    result = run_vendoring_sync()
    assert result.exit_code == 0

    vendored = tmp_path / "vendored"
    assert vendored.exists()
    assert sorted(os.listdir(vendored)) == [
        "pkg_resources",
        "pkg_resources.pyi",
        "setuptools.LICENSE",
    ]

    line = linecache.getline(str(vendored / "pkg_resources" / "__init__.py"), 57)
    assert line == "from transformations.vendored import six\n"

    line = linecache.getline(str(vendored / "pkg_resources" / "__init__.py"), 81)
    assert line == "__import__('transformations.vendored.packaging.version')\n"


def test_typing_fun(tmp_path, monkeypatch):
    shutil.copytree(SAMPLE_PROJECTS / "typing_fun", tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)

    result = run_vendoring_sync()
    assert result.exit_code == 0

    vendored = tmp_path / "vendored"
    assert vendored.exists()
    assert sorted(os.listdir(vendored)) == [
        "appdirs.LICENSE.txt",
        "appdirs.py",
        "contextlib2.LICENSE.txt",
        "contextlib2.py",
        "six",
        "six.LICENSE",
        "six.py",
    ]

    six = vendored / "six"
    assert sorted(os.listdir(six)) == [
        "__init__.pyi",
        "moves",
    ]
    assert (six / "moves" / "__init__.pyi").exists()
