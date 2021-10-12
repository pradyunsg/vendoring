import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Iterable

import requests

from vendoring.configuration import Configuration
from vendoring.ui import UI
from vendoring.utils import run


def download_wheels(location: Path, requirements: Path) -> None:
    cmd = [
        "pip",
        "download",
        "-r",
        str(requirements),
        "--only-binary",
        ":all:",
        "--no-deps",
        "--dest",
        str(location),
    ]
    run(cmd, working_directory=None)


def get_library_name_from_directory(dirname: str) -> str:
    """Reconstruct the library name without it's version"""
    parts = []
    for part in dirname.split("-"):
        if part[0].isdigit():
            break
        parts.append(part)
    return "-".join(parts)


def extract_license_member(
    destination: Path,
    wheel: zipfile.ZipFile,
    member: zipfile.ZipInfo,
    name: str,
    license_directories: Dict[str, str],
) -> None:
    mpath = Path(name)  # relative path inside the wheel

    dirname = list(mpath.parents)[-2].name  # -1 is .
    libname = get_library_name_from_directory(dirname)

    dest = get_license_destination(
        destination, libname, mpath.name, license_directories
    )

    UI.log("Extracting {} into {}".format(name, dest.relative_to(destination)))
    dest.write_bytes(wheel.read(member))


def find_and_extract_license(
    destination: Path,
    tar: zipfile.ZipFile,
    members: Iterable[zipfile.ZipInfo],
    license_directories: Dict[str, str],
) -> bool:
    found = False
    for member in members:
        name = member.filename
        if "LICENSE" in name or "COPYING" in name:
            if "/test" in name:
                # some testing licenses in html5lib and distlib
                UI.log("Ignoring {}".format(name))
                continue
            found = True
            extract_license_member(destination, tar, member, name, license_directories)
    return found


def get_license_destination(
    destination: Path, libname: str, filename: str, license_directories: Dict[str, str]
) -> Path:
    """Given the (reconstructed) library name, find appropriate destination"""
    normal = destination / libname
    if normal.is_dir():
        return normal / filename
    lowercase = destination / libname.lower()
    if lowercase.is_dir():
        return lowercase / filename
    if libname in license_directories:
        return destination / license_directories[libname] / filename
    # fallback to libname.LICENSE (used for nondirs)
    return destination / "{}.{}".format(libname, filename)


def download_from_url(url: str, dest: Path) -> None:
    UI.log("Downloading {}".format(url))
    r = requests.get(url, allow_redirects=True)
    r.raise_for_status()
    dest.write_bytes(r.content)


def get_license_fallback(
    destination: Path,
    wheel_name: str,
    license_directories: Dict[str, str],
    license_fallback_urls: Dict[str, str],
) -> None:
    """Hardcoded license URLs. Check when updating if those are still needed"""
    libname = get_library_name_from_directory(wheel_name)
    if libname not in license_fallback_urls:
        raise ValueError("No hardcoded URL for {} license".format(libname))

    url = license_fallback_urls[libname]
    _, _, name = url.rpartition("/")
    dest = get_license_destination(destination, libname, name, license_directories)

    download_from_url(url, dest)


def extract_license_from_wheel(
    destination: Path,
    wheel: Path,
    license_directories: Dict[str, str],
    license_fallback_urls: Dict[str, str],
) -> None:
    assert wheel.suffix == ".whl"

    with zipfile.ZipFile(wheel) as zip:
        found = find_and_extract_license(
            destination, zip, zip.infolist(), license_directories
        )

    if found:
        return

    UI.log("License not found in {}".format(wheel.name))
    get_license_fallback(
        destination, wheel.name, license_directories, license_fallback_urls
    )


def fetch_licenses(config: Configuration) -> None:
    destination = config.destination
    license_directories = config.license_directories
    license_fallback_urls = config.license_fallback_urls
    requirements = config.requirements

    tmp_dir = Path(tempfile.gettempdir(), "vendoring-downloads")
    download_wheels(tmp_dir, requirements)

    for wheel in tmp_dir.iterdir():
        extract_license_from_wheel(
            destination, wheel, license_directories, license_fallback_urls
        )

    shutil.rmtree(tmp_dir)
