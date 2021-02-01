"""Test the various bits of functionality, through sample projects."""

import linecache
import shutil
import traceback
from pathlib import Path

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
    assert sorted(vendored.iterdir()) == [
        vendored / "packaging",
        vendored / "packaging.pyi",
    ]

    packaging = vendored / "packaging"
    assert packaging.exists()
    assert sorted(packaging.iterdir()) == [
        packaging / "LICENSE",
        packaging / "LICENSE.APACHE",
        packaging / "LICENSE.BSD",
        packaging / "__about__.py",
        packaging / "__init__.py",
        packaging / "_compat.py",
        packaging / "_structures.py",
        packaging / "_typing.py",
        packaging / "markers.py",
        packaging / "py.typed",
        packaging / "requirements.py",
        packaging / "specifiers.py",
        packaging / "tags.py",
        packaging / "utils.py",
        packaging / "version.py",
    ]


def test_import_rewriting(tmp_path, monkeypatch):
    shutil.copytree(SAMPLE_PROJECTS / "import_rewriting", tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)

    result = run_vendoring_sync()
    assert result.exit_code == 0

    vendored = tmp_path / "vendored"
    assert vendored.exists()
    assert sorted(vendored.iterdir()) == [
        vendored / "retrying.LICENSE",
        vendored / "retrying.py",
        vendored / "retrying.pyi",
        vendored / "six.LICENSE",
        vendored / "six.py",
        vendored / "six.pyi",
    ]


def test_licenses(tmp_path, monkeypatch):
    shutil.copytree(SAMPLE_PROJECTS / "licenses", tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)

    result = run_vendoring_sync()
    assert result.exit_code == 0

    vendored = tmp_path / "vendored"
    assert vendored.exists()
    assert sorted(vendored.iterdir()) == [
        vendored / "appdirs.LICENSE.txt",
        vendored / "appdirs.py",
        vendored / "appdirs.pyi",
        vendored / "msgpack",
        vendored / "msgpack.pyi",
        vendored / "six.LICENSE",
        vendored / "six.py",
        vendored / "six.pyi",
        vendored / "webencodings",
        vendored / "webencodings.pyi",
    ]

    assert (vendored / "msgpack" / "COPYING").exists()
    assert (vendored / "webencodings" / "LICENSE").exists()


def test_patches(tmp_path, monkeypatch):
    shutil.copytree(SAMPLE_PROJECTS / "patches", tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)

    result = run_vendoring_sync()
    assert result.exit_code == 0

    vendored = tmp_path / "vendored"
    assert vendored.exists()
    assert sorted(vendored.iterdir()) == [
        vendored / "appdirs.LICENSE.txt",
        vendored / "appdirs.py",
        vendored / "appdirs.pyi",
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
    assert sorted(vendored.iterdir()) == [
        vendored / "README.md",
        vendored / "packaging",
        vendored / "packaging.pyi",
    ]


def test_transformations(tmp_path, monkeypatch):
    shutil.copytree(SAMPLE_PROJECTS / "transformations", tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)

    result = run_vendoring_sync()
    assert result.exit_code == 0

    vendored = tmp_path / "vendored"
    assert vendored.exists()
    assert sorted(vendored.iterdir()) == [
        vendored / "pkg_resources",
        vendored / "pkg_resources.pyi",
        vendored / "setuptools.LICENSE",
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
    assert sorted(vendored.iterdir()) == [
        vendored / "appdirs.LICENSE.txt",
        vendored / "appdirs.py",
        vendored / "contextlib2.LICENSE.txt",
        vendored / "contextlib2.py",
        vendored / "six",
        vendored / "six.LICENSE",
        vendored / "six.py",
    ]

    six = vendored / "six"
    assert sorted(six.iterdir()) == [
        six / "__init__.pyi",
        six / "moves",
    ]
    assert (six / "moves" / "__init__.pyi").exists()
