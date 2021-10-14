import shutil
import tarfile
import tempfile
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple, Union

import requests

from vendoring.configuration import Configuration
from vendoring.ui import UI
from vendoring.utils import run

Archive = Union[tarfile.TarFile, zipfile.ZipFile]
ArchiveMember = Union[tarfile.TarInfo, zipfile.ZipInfo]
ArchiveMembers = Union[List[tarfile.TarInfo], List[zipfile.ZipInfo]]


def _get_filename_from_archive_member(member: ArchiveMember) -> str:
    if isinstance(member, tarfile.TarInfo):
        return member.name
    return member.filename


@contextmanager
def _open_archive(artifact: Path) -> Iterator[Tuple[Archive, ArchiveMembers]]:
    if artifact.suffix in [".zip", ".whl"]:
        with zipfile.ZipFile(artifact) as zip_archive:
            yield zip_archive, zip_archive.infolist()
    elif artifact.suffix == ".gz":
        assert artifact.suffixes[-2:] == [".tar", ".gz"]
        with tarfile.open(artifact) as tarball:
            yield tarball, tarball.getmembers()
    else:
        raise Exception(f"Unknown archive extension: {artifact.name}")


def _get_library_name_from_artifact_name(artifact_name: str) -> str:
    """Reconstruct the library name, from the name of an artifact containing it."""
    parts = []
    for part in artifact_name.split("-"):
        if part[0].isdigit():
            break
        parts.append(part)
    return "-".join(parts)


@dataclass
class LicenseExtractor:
    destination: Path
    license_directories: Dict[str, str]
    license_fallback_urls: Dict[str, str]

    @staticmethod
    def download_from_url(url: str, dest: Path) -> None:
        UI.log(f"Downloading {url}")
        r = requests.get(url, allow_redirects=True)
        r.raise_for_status()
        dest.write_bytes(r.content)

    @staticmethod
    def find_licenses(members: ArchiveMembers) -> Iterator[ArchiveMember]:
        for member in members:
            name = _get_filename_from_archive_member(member)

            if "LICENSE" in name or "COPYING" in name:
                if "/test" in name:  # some testing licenses in html5lib and distlib
                    UI.log(f"Ignoring {name}")
                    continue
                yield member

    def get_license_destination(self, library: str, filename: str) -> Path:
        """Given the (reconstructed) library name, find appropriate destination"""
        assert "/" not in filename, filename
        if (normal := self.destination / library).is_dir():
            return normal / filename
        if (lowercase := self.destination / library.lower()).is_dir():
            return lowercase / filename
        if library in self.license_directories:
            return self.destination / self.license_directories[library] / filename

        # fallback to library.LICENSE (used for non-import-package libraries)
        return self.destination / f"{library}.{filename}"

    def extract_license_member(
        self, artifact: Path, archive: Archive, member: ArchiveMember
    ) -> None:

        library_name = _get_library_name_from_artifact_name(artifact.name)
        license_filename = Path(_get_filename_from_archive_member(member)).name
        dest = self.get_license_destination(library_name, license_filename)

        UI.log(
            f"Extracting {license_filename} into {dest.relative_to(self.destination)}"
        )

        # Oh, the joys of mypy.
        if isinstance(archive, zipfile.ZipFile):
            assert isinstance(member, zipfile.ZipInfo)
            dest.write_bytes(archive.read(member))
        else:
            assert isinstance(archive, tarfile.TarFile)
            assert isinstance(member, tarfile.TarInfo)

            file = archive.extractfile(member)
            assert file

            dest.write_bytes(file.read())

    def use_license_fallback(self, artifact_name: str) -> None:
        library_name = _get_library_name_from_artifact_name(artifact_name)
        if library_name not in self.license_fallback_urls:
            raise ValueError(f"No hardcoded license URL for {library_name}")

        url = self.license_fallback_urls[library_name]
        _, _, license_filename = url.rpartition("/")

        dest = self.get_license_destination(library_name, license_filename)
        self.download_from_url(url, dest)

    def extract_license_from_artifact(self, artifact: Path) -> None:
        with _open_archive(artifact) as archive_info:
            archive, files = archive_info

            licenses = list(self.find_licenses(files))
            for found in licenses:
                self.extract_license_member(artifact, archive, found)

        if not licenses:
            UI.log(f"No license found in {artifact.name}, using fallback.")
            self.use_license_fallback(artifact.name)


def download_distributions(location: Path, requirements: Path) -> None:
    cmd = [
        "pip",
        "download",
        "-r",
        str(requirements),
        "--no-deps",
        "--dest",
        str(location),
    ]
    run(cmd, working_directory=None)


def fetch_licenses(config: Configuration) -> None:
    destination = config.destination
    license_directories = config.license_directories
    license_fallback_urls = config.license_fallback_urls
    requirements = config.requirements

    tmp_dir = Path(tempfile.gettempdir(), "vendoring-downloads")
    try:
        download_distributions(tmp_dir, requirements)

        license_extractor = LicenseExtractor(
            destination=destination,
            license_directories=license_directories,
            license_fallback_urls=license_fallback_urls,
        )
        for artifact in tmp_dir.iterdir():
            license_extractor.extract_license_from_artifact(artifact)
    finally:
        shutil.rmtree(tmp_dir)
