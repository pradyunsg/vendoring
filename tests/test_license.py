import os
from pathlib import Path
from unittest import mock

from vendoring.tasks.license import fetch_licenses


@mock.patch("appdirs.user_cache_dir")
def test_user_cache_dir(mock_user_cache_dir, tmpdir):
    cache_dir = tmpdir / "cache"
    mock_user_cache_dir.return_value = str(cache_dir)
    destination_dir = tmpdir / "destination"
    destination_dir.mkdir()
    requirements = tmpdir / "requirements.txt"
    requirements.write_text("wheel==0.36.2\n", encoding="utf-8")

    config = mock.Mock()
    config.destination = Path(destination_dir)
    config.requirements = Path(requirements)
    config.license_directories = {}
    fetch_licenses(config)

    cached = os.listdir(cache_dir)
    assert cached == ["wheel-0.36.2.tar.gz"]
