"""Verified acquisition helpers for official IFC source artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OFFICIAL_HOST = "standards.buildingsmart.org"
_CACHE_PREFIX = (".cache", "ifc2x3")
_READ_SIZE = 1024 * 1024


@dataclass(frozen=True)
class SourceSpec:
    id: str
    role: str
    url: str
    sha256: str
    cache_path: str | None = None
    local_path: str | None = None
    required_for_generation: bool = False


@dataclass(frozen=True)
class SourceManifest:
    schema: str
    release: str
    retrieved_at: str
    sources: tuple[SourceSpec, ...]

    def source(self, source_id: str) -> SourceSpec:
        for source in self.sources:
            if source.id == source_id:
                return source
        raise KeyError(source_id)


@dataclass(frozen=True)
class ArchiveMember:
    name: str
    size: int


class SourceManifestError(ValueError):
    pass


class SourceIntegrityError(ValueError):
    pass


class ArchiveSafetyError(ValueError):
    pass


def _validate_official_url(url: str) -> None:
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != _OFFICIAL_HOST
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise SourceManifestError(f"untrusted official source URL: {url!r}")


def _validate_relative_path(value: str, *, field: str) -> None:
    path = PurePosixPath(value.replace("\\", "/"))
    if not value or path.is_absolute() or ".." in path.parts or ":" in value:
        raise SourceManifestError(f"unsafe {field}: {value!r}")


def load_source_manifest(path: str | Path) -> SourceManifest:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceManifestError(f"cannot read source manifest: {exc}") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise SourceManifestError("manifest must contain a sources array")

    sources: list[SourceSpec] = []
    seen: set[str] = set()
    for raw in payload["sources"]:
        if not isinstance(raw, dict):
            raise SourceManifestError("each source must be an object")
        try:
            source = SourceSpec(
                id=raw["id"],
                role=raw["role"],
                url=raw["url"],
                sha256=raw["sha256"].lower(),
                cache_path=raw.get("cache_path"),
                local_path=raw.get("local_path"),
                required_for_generation=bool(raw.get("required_for_generation", False)),
            )
        except (KeyError, AttributeError, TypeError) as exc:
            raise SourceManifestError(f"invalid source record: {raw!r}") from exc

        if not source.id or source.id in seen:
            raise SourceManifestError(f"missing or duplicate source id: {source.id!r}")
        if not source.role:
            raise SourceManifestError(f"source {source.id!r} has no role")
        _validate_official_url(source.url)
        if not _SHA256_RE.fullmatch(source.sha256):
            raise SourceManifestError(f"source {source.id!r} has invalid SHA-256")
        if bool(source.cache_path) == bool(source.local_path):
            raise SourceManifestError(
                f"source {source.id!r} must define exactly one local or cache path"
            )
        if source.cache_path:
            _validate_relative_path(source.cache_path, field="cache_path")
            parts = PurePosixPath(source.cache_path).parts
            if parts[:2] != _CACHE_PREFIX:
                raise SourceManifestError(
                    f"source {source.id!r} cache must be under .cache/ifc2x3"
                )
        if source.local_path:
            _validate_relative_path(source.local_path, field="local_path")
        sources.append(source)
        seen.add(source.id)

    return SourceManifest(
        schema=str(payload.get("schema", "")),
        release=str(payload.get("release", "")),
        retrieved_at=str(payload.get("retrieved_at", "")),
        sources=tuple(sources),
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(_READ_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source_file(path: str | Path, source: SourceSpec) -> str:
    source_path = Path(path)
    try:
        digest = _sha256_file(source_path)
    except OSError as exc:
        raise SourceIntegrityError(f"cannot read source {source.id!r}: {exc}") from exc
    if digest != source.sha256:
        raise SourceIntegrityError(
            f"SHA-256 mismatch for {source.id!r}: expected {source.sha256}, got {digest}"
        )
    return digest


def _safe_archive_name(name: str) -> PurePosixPath:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or path.is_absolute()
        or ".." in path.parts
        or any(":" in part for part in path.parts)
        or (path.parts and re.fullmatch(r"[A-Za-z]:", path.parts[0]))
    ):
        raise ArchiveSafetyError(f"unsafe archive member path: {name!r}")
    return path


def inspect_zip_archive(
    path: str | Path,
    *,
    max_entries: int = 5000,
    max_uncompressed_bytes: int = 128 * 1024 * 1024,
) -> tuple[ArchiveMember, ...]:
    if max_entries < 1 or max_uncompressed_bytes < 1:
        raise ArchiveSafetyError("archive limits must be positive")
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > max_entries:
                raise ArchiveSafetyError(
                    f"archive has {len(infos)} entries, limit is {max_entries}"
                )
            expanded = 0
            members: list[ArchiveMember] = []
            for info in infos:
                _safe_archive_name(info.filename)
                unix_mode = (info.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(unix_mode):
                    raise ArchiveSafetyError(
                        f"archive member is a symlink: {info.filename!r}"
                    )
                expanded += info.file_size
                if expanded > max_uncompressed_bytes:
                    raise ArchiveSafetyError(
                        "archive exceeds maximum uncompressed byte count"
                    )
                members.append(ArchiveMember(info.filename, info.file_size))
            return tuple(members)
    except ArchiveSafetyError:
        raise
    except (OSError, zipfile.BadZipFile) as exc:
        raise ArchiveSafetyError(f"invalid ZIP archive: {exc}") from exc


def download_source(
    source: SourceSpec,
    project_root: str | Path,
    *,
    opener=None,
    max_bytes: int = 128 * 1024 * 1024,
) -> Path:
    _validate_official_url(source.url)
    if not _SHA256_RE.fullmatch(source.sha256):
        raise SourceManifestError(f"source {source.id!r} has invalid SHA-256")
    if not source.cache_path:
        raise SourceManifestError(f"source {source.id!r} has no cache_path")
    _validate_relative_path(source.cache_path, field="cache_path")
    relative = PurePosixPath(source.cache_path)
    if relative.parts[:2] != _CACHE_PREFIX:
        raise SourceManifestError("downloads must stay under .cache/ifc2x3")
    if max_bytes < 1:
        raise SourceIntegrityError("download byte limit must be positive")

    root = Path(project_root).resolve()
    destination = root.joinpath(*relative.parts).resolve()
    cache_root = root.joinpath(*_CACHE_PREFIX).resolve()
    if cache_root != destination.parent and cache_root not in destination.parents:
        raise SourceManifestError("download destination escapes the IFC cache")
    destination.parent.mkdir(parents=True, exist_ok=True)

    open_url = opener or urllib.request.urlopen
    temporary: Path | None = None
    try:
        request = urllib.request.Request(
            source.url,
            headers={"User-Agent": "text2IFC-source-fetch/1"},
        )
        with open_url(request, timeout=30) as response:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f".{destination.name}.",
                suffix=".tmp",
                dir=destination.parent,
                delete=False,
            ) as output:
                temporary = Path(output.name)
                digest = hashlib.sha256()
                size = 0
                while True:
                    chunk = response.read(_READ_SIZE)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        raise SourceIntegrityError(
                            f"download for {source.id!r} exceeds {max_bytes} bytes"
                        )
                    digest.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())

        actual = digest.hexdigest()
        if actual != source.sha256:
            raise SourceIntegrityError(
                f"SHA-256 mismatch for {source.id!r}: "
                f"expected {source.sha256}, got {actual}"
            )
        os.replace(temporary, destination)
        temporary = None
        return destination
    except SourceIntegrityError:
        raise
    except OSError as exc:
        raise SourceIntegrityError(f"download failed for {source.id!r}: {exc}") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
