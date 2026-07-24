"""Read-only integrity audit for source manifests and processed dataset roots."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
AUDIT_SCHEMA_VERSION = "text2ifc/dataset-audit/1.0"
_IFC_SCHEMA_PATTERN = re.compile(
    rb"FILE_SCHEMA\s*\(\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
_PROCESSED_CLASSIFICATIONS = {
    "ifc-repair": "retain",
    "agent-demo": "review_before_delete",
    "text2json": "retain",
    "phase6": "retain",
    "jsonfix": "regenerable",
    "bim-json-1.0": "regenerable",
    "bim-json-2.0": "regenerable",
}


class DatasetAuditError(ValueError):
    """Raised when a dataset manifest no longer matches local source bytes."""


def audit_dataset(root: Path | str = ROOT) -> dict[str, Any]:
    """Audit known manifests and inventory processed roots without mutation."""

    project_root = Path(root).resolve()
    manifest_root = project_root / "dataset" / "manifests"
    manifests = {
        "bimnet-ifc2x3": audit_file_manifest(
            manifest_root / "bimnet-ifc2x3.jsonl",
            root=project_root,
        ),
        "raw-files": audit_file_manifest(
            manifest_root / "raw-files.jsonl",
            root=project_root,
        ),
        "external-corpora": audit_external_corpora(
            manifest_root / "external-corpora.json",
            root=project_root,
        ),
    }
    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "valid": all(item["valid"] for item in manifests.values()),
        "manifests": manifests,
        "processed_inventory": inventory_processed_roots(project_root),
    }


def audit_file_manifest(
    manifest_path: Path | str,
    *,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    """Validate one JSONL source manifest against the referenced local files."""

    project_root = Path(root).resolve()
    path = Path(manifest_path).resolve()
    records = _read_jsonl(path)
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    schemas: Counter[str] = Counter()
    total_bytes = 0
    for line_number, record in enumerate(records, start=1):
        record_id = _required_string(record, "id", line_number)
        local_path = _required_string(record, "local_path", line_number)
        declared_schema = _required_string(record, "declared_schema", line_number)
        expected_sha256 = _required_sha256(record, "sha256", line_number)
        if record_id in seen_ids:
            raise DatasetAuditError(f"DUPLICATE_ID:{record_id}")
        if local_path in seen_paths:
            raise DatasetAuditError(f"DUPLICATE_PATH:{local_path}")
        seen_ids.add(record_id)
        seen_paths.add(local_path)
        source = _resolve_inside(project_root, local_path)
        if not source.is_file():
            raise DatasetAuditError(f"MISSING_FILE:{local_path}")
        actual_sha256 = _sha256(source)
        if actual_sha256 != expected_sha256:
            raise DatasetAuditError(f"HASH_MISMATCH:{local_path}")
        actual_schema = _read_ifc_schema(source)
        if not _schema_matches(declared_schema, actual_schema):
            raise DatasetAuditError(
                f"SCHEMA_MISMATCH:{local_path}:{declared_schema}:{actual_schema}"
            )
        schemas[actual_schema] += 1
        total_bytes += source.stat().st_size
    return {
        "valid": True,
        "path": _display_path(path, project_root),
        "record_count": len(records),
        "total_size_bytes": total_bytes,
        "schemas": dict(sorted(schemas.items())),
    }


def audit_external_corpora(
    manifest_path: Path | str,
    *,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    """Validate linked-corpus working-tree counts without traversing `.git`."""

    project_root = Path(root).resolve()
    path = Path(manifest_path).resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DatasetAuditError(f"INVALID_JSON:{_display_path(path, project_root)}") from error
    corpora = payload.get("corpora")
    if not isinstance(corpora, list):
        raise DatasetAuditError("EXTERNAL_CORPORA_MISSING")
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for record in corpora:
        if not isinstance(record, Mapping):
            raise DatasetAuditError("EXTERNAL_CORPUS_RECORD_INVALID")
        corpus_id = str(record.get("corpus_id", ""))
        if not corpus_id or corpus_id in seen_ids:
            raise DatasetAuditError(f"EXTERNAL_CORPUS_ID_INVALID:{corpus_id}")
        seen_ids.add(corpus_id)
        corpus_path = _resolve_inside(
            project_root,
            _required_string(record, "path", corpus_id),
        )
        file_count, size_bytes, unreadable = _tree_stats(corpus_path)
        if file_count != record.get("file_count"):
            raise DatasetAuditError(f"CORPUS_FILE_COUNT_MISMATCH:{corpus_id}")
        if size_bytes != record.get("size_bytes"):
            raise DatasetAuditError(f"CORPUS_SIZE_MISMATCH:{corpus_id}")
        if unreadable:
            raise DatasetAuditError(f"CORPUS_UNREADABLE:{corpus_id}")
        results.append(
            {
                "corpus_id": corpus_id,
                "file_count": file_count,
                "size_bytes": size_bytes,
                "source_revision": record.get("source_revision"),
                "status": record.get("status"),
            }
        )
    return {
        "valid": True,
        "path": _display_path(path, project_root),
        "record_count": len(results),
        "corpora": results,
    }


def inventory_processed_roots(root: Path | str = ROOT) -> dict[str, Any]:
    """Classify current processed roots; never move, delete, or rewrite them."""

    project_root = Path(root).resolve()
    processed = project_root / "dataset" / "processed"
    roots: list[dict[str, Any]] = []
    if processed.is_dir():
        for item in sorted(processed.iterdir(), key=lambda value: value.name.casefold()):
            if not item.is_dir():
                continue
            file_count, size_bytes, unreadable = _tree_stats(item)
            roots.append(
                {
                    "path": _display_path(item, project_root),
                    "classification": _PROCESSED_CLASSIFICATIONS.get(
                        item.name,
                        "review_before_delete",
                    ),
                    "file_count": file_count,
                    "size_bytes": size_bytes,
                    "unreadable_directory_count": unreadable,
                }
            )
    return {
        "mutation_policy": "read_only",
        "classification_meaning": {
            "retain": "contains source-bound evidence or split authority",
            "regenerable": "derived output that can be rebuilt from checked-in inputs",
            "review_before_delete": "mixed or unclassified content; requires explicit review",
        },
        "roots": roots,
    }


def render_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise DatasetAuditError(f"MISSING_MANIFEST:{path.as_posix()}") from error
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise DatasetAuditError(f"INVALID_JSONL:{line_number}") from error
        if not isinstance(record, dict):
            raise DatasetAuditError(f"INVALID_RECORD:{line_number}")
        records.append(record)
    if not records:
        raise DatasetAuditError("EMPTY_MANIFEST")
    return records


def _tree_stats(root: Path) -> tuple[int, int, int]:
    if not root.is_dir():
        raise DatasetAuditError(f"MISSING_DIRECTORY:{root.as_posix()}")
    file_count = 0
    size_bytes = 0
    unreadable = 0

    def on_error(_: OSError) -> None:
        nonlocal unreadable
        unreadable += 1

    for directory, directory_names, file_names in os.walk(root, onerror=on_error):
        directory_names[:] = sorted(
            name for name in directory_names if name != ".git"
        )
        for name in sorted(file_names):
            try:
                size_bytes += (Path(directory) / name).stat().st_size
                file_count += 1
            except OSError:
                unreadable += 1
    return file_count, size_bytes, unreadable


def _read_ifc_schema(path: Path) -> str:
    with path.open("rb") as stream:
        header = stream.read(1024 * 1024)
    match = _IFC_SCHEMA_PATTERN.search(header)
    if match is None:
        raise DatasetAuditError(f"IFC_SCHEMA_NOT_FOUND:{path.as_posix()}")
    return match.group(1).decode("ascii", errors="strict").upper()


def _schema_matches(declared: str, actual: str) -> bool:
    declared = declared.upper()
    actual = actual.upper()
    if declared == "IFC4X3":
        return actual.startswith("IFC4X3")
    return declared == actual


def _required_string(
    record: Mapping[str, Any],
    field: str,
    label: int | str,
) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise DatasetAuditError(f"MISSING_FIELD:{label}:{field}")
    return value


def _required_sha256(
    record: Mapping[str, Any],
    field: str,
    label: int | str,
) -> str:
    value = _required_string(record, field, label)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise DatasetAuditError(f"INVALID_SHA256:{label}:{field}")
    return value


def _resolve_inside(root: Path, local_path: str) -> Path:
    resolved = (root / local_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise DatasetAuditError(f"PATH_OUTSIDE_ROOT:{local_path}") from error
    return resolved


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

