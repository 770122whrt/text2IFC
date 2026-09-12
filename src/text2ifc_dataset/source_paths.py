"""Resolve archived dataset references without rewriting frozen metadata.

This is a local dataset/evaluation helper, not a Provider source discovery API.
Only explicit migration records may substitute a missing historical path.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _inside(root: Path, reference: str) -> Path:
    relative = Path(reference)
    if relative.is_absolute() or relative.drive or ".." in relative.parts:
        raise ValueError(f"Source reference must be repository-relative: {reference}")
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(f"Source reference escapes repository: {reference}")
    return candidate


def _verify(path: Path, digest: str | None) -> Path:
    if not path.is_file():
        raise FileNotFoundError(path)
    if digest is not None:
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != digest:
            raise ValueError(f"Source SHA-256 mismatch: {path}")
    return path


def resolve_source_path(
    root: Path, reference: str, *, expected_sha256: str | None = None
) -> Path:
    """Resolve a direct or explicitly migrated source, checking frozen hashes.

    Existing legacy files are checked too: an unexpected local file must never
    be hidden by a successful canonical fallback. No basename search is used.
    """
    root = root.resolve()
    original = _inside(root, reference)
    manifest = root / "dataset/manifests/bimnet-migration-map.json"
    records = json.loads(manifest.read_text(encoding="utf-8"))["records"] if manifest.is_file() else []
    normalized = Path(reference).as_posix()
    matches = [item for item in records if item["old_path"] == normalized]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous source migration: {reference}")
    if not matches:
        return _verify(original, expected_sha256)
    record = matches[0]
    digest = record["sha256"]
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError(f"Invalid migration SHA-256: {reference}")
    if expected_sha256 is not None and expected_sha256 != digest:
        raise ValueError(f"Frozen and migration SHA-256 disagree: {reference}")
    canonical = _inside(root, record["new_path"])
    if original.exists():
        _verify(original, digest)
    return _verify(canonical, digest)
