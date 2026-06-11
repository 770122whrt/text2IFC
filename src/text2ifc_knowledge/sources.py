"""Official-source verification API skeleton for the RED phase."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpec:
    id: str
    role: str
    url: str
    sha256: str
    cache_path: str | None = None
    local_path: str | None = None
    required_for_generation: bool = False


class SourceManifestError(ValueError):
    pass


class SourceIntegrityError(ValueError):
    pass


class ArchiveSafetyError(ValueError):
    pass


def load_source_manifest(path):
    raise NotImplementedError("source manifest loading is not implemented")


def verify_source_file(path, source):
    raise NotImplementedError("source verification is not implemented")


def inspect_zip_archive(path, *, max_entries=5000, max_uncompressed_bytes=128 * 1024 * 1024):
    raise NotImplementedError("archive inspection is not implemented")


def download_source(source, project_root, *, opener=None, max_bytes=128 * 1024 * 1024):
    raise NotImplementedError("bounded source download is not implemented")
