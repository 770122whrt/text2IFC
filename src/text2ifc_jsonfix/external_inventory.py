"""Read-only schema inventory for local external IFC evidence corpora."""

from __future__ import annotations

import configparser
import hashlib
from pathlib import Path
from typing import Any, Iterable

import ifcopenshell

from .ifc_artifact import parse_step_schema


INVENTORY_SCHEMA_VERSION = "text2ifc/external-ifc-inventory-v1"


def _relative(path: Path, repository_root: Path) -> str:
    try:
        return path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _license_files(root: Path, repository_root: Path) -> list[dict[str, Any]]:
    candidates = sorted(
        path
        for path in root.iterdir()
        if path.is_file()
        and path.name.upper().startswith(
            ("LICENSE", "COPYING", "NOTICE")
        )
    )
    return [
        {
            "path": _relative(path, repository_root),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in candidates
    ]


def _remote_url(root: Path) -> str | None:
    config_path = root / ".git" / "config"
    if not config_path.is_file():
        return None
    parser = configparser.ConfigParser()
    try:
        parser.read(config_path, encoding="utf-8")
        return parser.get('remote "origin"', "url", fallback=None)
    except (configparser.Error, OSError):
        return None


def _ifc_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.casefold() == ".ifc"
    )


def inventory_external_ifc(
    roots: Iterable[Path],
    *,
    repository_root: Path,
    max_selected_ifc2x3: int = 3,
) -> dict[str, Any]:
    corpora: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []

    for root_value in roots:
        root = Path(root_value)
        available = root.is_dir()
        corpus = {
            "corpus_id": root.name,
            "root": _relative(root, repository_root),
            "available": available,
            "source_remote_url": _remote_url(root) if available else None,
            "license_files": (
                _license_files(root, repository_root) if available else []
            ),
        }
        corpora.append(corpus)
        if not available:
            continue

        for path in _ifc_files(root):
            try:
                evidence = parse_step_schema(path)
                declared = (
                    evidence.identifiers[0]
                    if evidence.declaration_count == 1
                    and len(evidence.identifiers) == 1
                    else None
                )
            except OSError:
                evidence = None
                declared = None
            reopened_schema = None
            reopen_status = "ok"
            reopen_error = None
            try:
                model = ifcopenshell.open(str(path))
                reopened_schema = str(model.schema).upper()
            except Exception as exc:
                reopen_status = "error"
                reopen_error = type(exc).__name__
            files.append(
                {
                    "corpus_id": root.name,
                    "path": _relative(path, repository_root),
                    "size_bytes": path.stat().st_size,
                    "file_schema_declaration_count": (
                        evidence.declaration_count if evidence else 0
                    ),
                    "declared_schema_identifiers": (
                        list(evidence.identifiers) if evidence else []
                    ),
                    "declared_file_schema": declared,
                    "reopen_status": reopen_status,
                    "reopened_schema": reopened_schema,
                    "reopen_error_type": reopen_error,
                    "eligible_ifc2x3": (
                        declared == "IFC2X3"
                        and reopen_status == "ok"
                        and reopened_schema == "IFC2X3"
                    ),
                }
            )

    eligible = sorted(
        item["path"] for item in files if item["eligible_ifc2x3"]
    )
    selected = eligible[: max(0, max_selected_ifc2x3)]
    return {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "corpora": corpora,
        "files": sorted(files, key=lambda item: item["path"]),
        "selected_ifc2x3": selected,
        "summary": {
            "corpus_count": len(corpora),
            "file_count": len(files),
            "eligible_ifc2x3_count": len(eligible),
            "selected_ifc2x3_count": len(selected),
        },
    }
