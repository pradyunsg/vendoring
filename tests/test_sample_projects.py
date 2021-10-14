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
    result = runner.invoke(main, ["sync"], catch_exceptions=False)

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
    assert sorted(os.listdir(vendored)) == ["packaging"]

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
        "packaging",
        "six.LICENSE",
        "six.py",
        "six.pyi",
    ]

    interesting_file = vendored / "packaging" / "requirements.py"
    interesting_lineno = 12
    with interesting_file.open() as f:
        iterable = iter(f)
        for _ in range(interesting_lineno - 1):
            next(iterable)
        interesting_line = next(iterable)

    expected_line = (
        "from import_rewriting.vendored.six.moves.urllib import parse as urlparse\n"
    )
    assert interesting_line == expected_line


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
        "six.LICENSE",
        "six.py",
        "six.pyi",
        "tomli",
        "webencodings",
        "webencodings.pyi",
    ]

    assert (vendored / "tomli" / "LICENSE").exists()
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
    assert sorted(os.listdir(vendored)) == ["README.md", "packaging"]


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
        "setuptools",
        "setuptools.pyi",
    ]

    assert sorted(os.listdir(vendored / "setuptools")) == [
        "LICENSE",
        "archive_util.py",
        "build_meta.py",
        "command",
        "config.py",
        "dep_util.py",
        "depends.py",
        "dist.py",
        "distutils_patch.py",
        "errors.py",
        "extension.py",
        "extern",
        "glob.py",
        "installer.py",
        "launch.py",
        "lib2to3_ex.py",
        "monkey.py",
        "msvc.py",
        "namespaces.py",
        "package_index.py",
        "sandbox.py",
        "ssl_support.py",
        "unicode_utils.py",
        "version.py",
        "windows_support.py",
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
