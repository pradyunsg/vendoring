import os
from unittest import mock
from pathlib import Path

from vendoring.tasks.license import fetch_licenses


def test_fetch_licesnes_multiple_times_different_packages(tmpdir):
    tmpdir = Path(str(tmpdir))

    packages = [
        ("wheel==0.36.2", "wheel.LICENSE.txt"),
        ("black==20.8b1", "black.LICENSE"),
    ]
    for i, (package, license) in enumerate(packages):
        package_tmpdir = tmpdir / str(i)

        destination_dir = package_tmpdir / "destination"
        destination_dir.mkdir(parents=True)
        requirements = package_tmpdir / "requirements.txt"
        requirements.write_text(package)

        config = mock.Mock()
        config.destination = destination_dir
        config.requirements = requirements
        config.license_directories = {}
        fetch_licenses(config)

        assert os.listdir(destination_dir) == [license]
