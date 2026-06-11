from __future__ import annotations

import json
import hashlib
import io
from pathlib import Path

import pytest

from text2ifc_knowledge.sources import (
    ArchiveSafetyError,
    SourceIntegrityError,
    SourceManifestError,
    SourceSpec,
    download_source,
    inspect_zip_archive,
    load_source_manifest,
    verify_source_file,
)


class FakeResponse(io.BytesIO):
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def test_official_express_matches_manifest_hash(
    project_root: Path, source_manifest_path: Path
) -> None:
    manifest = load_source_manifest(source_manifest_path)
    source = manifest.source("ifc2x3-tc1-express")

    digest = verify_source_file(project_root / source.local_path, source)

    assert digest == source.sha256


@pytest.mark.parametrize(
    "mutation",
    [
        {"url": "https://example.com/IFC2X3_TC1.exp"},
        {"sha256": ""},
        {"sha256": "not-a-sha256"},
    ],
)
def test_manifest_rejects_untrusted_or_unhashed_sources(
    tmp_path: Path, source_manifest_path: Path, mutation: dict[str, str]
) -> None:
    payload = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    payload["sources"][0].update(mutation)
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SourceManifestError):
        load_source_manifest(path)


def test_changed_source_bytes_are_rejected(tmp_path: Path, source_manifest_path: Path) -> None:
    manifest = load_source_manifest(source_manifest_path)
    source = manifest.source("ifc2x3-tc1-express")
    changed = tmp_path / "changed.exp"
    changed.write_bytes(b"SCHEMA NOT_IFC; END_SCHEMA;")

    with pytest.raises(SourceIntegrityError):
        verify_source_file(changed, source)


@pytest.mark.parametrize(
    "entry",
    [
        "../escape.xml",
        "/absolute.xml",
        "C:/absolute.xml",
        "psd/../../escape.xml",
        "psd/file.xml:stream",
    ],
)
def test_archive_rejects_unsafe_member_paths(psd_zip_factory, entry: str) -> None:
    archive = psd_zip_factory({entry: "<PropertySetDef/>"})

    with pytest.raises(ArchiveSafetyError):
        inspect_zip_archive(archive)


def test_archive_rejects_symlinks(psd_zip_factory) -> None:
    archive = psd_zip_factory({}, symlink="psd/link.xml")

    with pytest.raises(ArchiveSafetyError):
        inspect_zip_archive(archive)


def test_archive_enforces_entry_and_expanded_size_limits(psd_zip_factory) -> None:
    archive = psd_zip_factory({"a.xml": "1234", "b.xml": "5678"})

    with pytest.raises(ArchiveSafetyError):
        inspect_zip_archive(archive, max_entries=1)
    with pytest.raises(ArchiveSafetyError):
        inspect_zip_archive(archive, max_uncompressed_bytes=7)


def test_download_verifies_hash_before_atomic_cache_replace(tmp_path: Path) -> None:
    payload = b"official-source-bytes"
    source = SourceSpec(
        id="fixture",
        role="test",
        url="https://standards.buildingsmart.org/fixture.bin",
        sha256=hashlib.sha256(payload).hexdigest(),
        cache_path=".cache/ifc2x3/fixture.bin",
    )

    destination = download_source(
        source,
        tmp_path,
        opener=lambda *args, **kwargs: FakeResponse(payload),
    )

    assert destination == tmp_path / ".cache" / "ifc2x3" / "fixture.bin"
    assert destination.read_bytes() == payload
    assert not list(destination.parent.glob("*.tmp"))


@pytest.mark.parametrize(
    ("payload", "max_bytes"),
    [(b"changed", 1024), (b"too-large", 3)],
)
def test_download_rejects_bad_hash_or_oversized_content(
    tmp_path: Path, payload: bytes, max_bytes: int
) -> None:
    source = SourceSpec(
        id="fixture",
        role="test",
        url="https://standards.buildingsmart.org/fixture.bin",
        sha256=hashlib.sha256(b"expected").hexdigest(),
        cache_path=".cache/ifc2x3/fixture.bin",
    )

    with pytest.raises(SourceIntegrityError):
        download_source(
            source,
            tmp_path,
            opener=lambda *args, **kwargs: FakeResponse(payload),
            max_bytes=max_bytes,
        )

    assert not (tmp_path / ".cache" / "ifc2x3" / "fixture.bin").exists()
