"""Versioned benchmark admission records for IFC repair experiments."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import ifcopenshell

from text2ifc_ifc_repair.sample import inspect_sample_capabilities


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_SCHEMA_VERSION = "text2ifc/ifc-repair-benchmark/1.0"


class BenchmarkManifestError(ValueError):
    """Raised when a checked-in benchmark record drifts from its source IFC."""


def build_benchmark_record(
    *,
    root: Path | str = ROOT,
    benchmark_id: str,
    local_path: str,
    execution_role: str,
    suitability: str,
) -> dict[str, Any]:
    project_root = Path(root).resolve()
    source = _resolve_inside(project_root, local_path)
    model = ifcopenshell.open(str(source))
    capabilities = inspect_sample_capabilities(source)
    source_identity = _source_identity(project_root, local_path)
    return {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "benchmark_id": benchmark_id,
        "local_path": local_path,
        "source_manifest_id": source_identity.get("id"),
        "source_corpus_id": source_identity.get("corpus_id"),
        "source_revision": source_identity.get("source_revision"),
        "source_sha256": _sha256(source),
        "ifc_schema": model.schema,
        "size_bytes": source.stat().st_size,
        "entity_count": sum(1 for _ in model),
        "window_count": len(model.by_type("IfcWindow")),
        "valid_window_opening_wall_chain_count": capabilities[
            "valid_window_opening_wall_chain_count"
        ],
        "straight_wall_count": capabilities["straight_wall_count"],
        "unsupported_wall_count": capabilities["unsupported_wall_count"],
        "scene_family": source_identity.get("scene_family"),
        "project_split": _project_split(
            project_root,
            source_identity.get("id"),
        ),
        "execution_role": execution_role,
        "suitability": suitability,
    }


def load_and_validate_benchmark_manifest(
    path: Path | str,
    *,
    root: Path | str = ROOT,
) -> list[dict[str, Any]]:
    project_root = Path(root).resolve()
    manifest_path = Path(path)
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(
        manifest_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise BenchmarkManifestError(f"INVALID_JSONL:{line_number}") from error
        _validate_record(record, line_number=line_number)
        benchmark_id = record["benchmark_id"]
        if benchmark_id in seen_ids:
            raise BenchmarkManifestError(f"DUPLICATE_BENCHMARK_ID:{benchmark_id}")
        seen_ids.add(benchmark_id)
        source = _resolve_inside(project_root, record["local_path"])
        if not source.is_file():
            raise BenchmarkManifestError(f"MISSING_IFC:{record['local_path']}")
        if source.stat().st_size != record["size_bytes"]:
            raise BenchmarkManifestError(f"SIZE_MISMATCH:{record['local_path']}")
        if _sha256(source) != record["source_sha256"]:
            raise BenchmarkManifestError(f"HASH_MISMATCH:{record['local_path']}")
        records.append(record)
    if not records:
        raise BenchmarkManifestError("EMPTY_BENCHMARK_MANIFEST")
    return records


def render_jsonl(records: list[Mapping[str, Any]]) -> str:
    return "".join(
        json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
        for record in records
    )


def _validate_record(record: Any, *, line_number: int) -> None:
    if not isinstance(record, dict):
        raise BenchmarkManifestError(f"INVALID_RECORD:{line_number}")
    required_strings = (
        "schema_version",
        "benchmark_id",
        "local_path",
        "source_sha256",
        "ifc_schema",
        "execution_role",
        "suitability",
    )
    for field in required_strings:
        if not isinstance(record.get(field), str) or not record[field]:
            raise BenchmarkManifestError(f"MISSING_FIELD:{line_number}:{field}")
    if record["schema_version"] != BENCHMARK_SCHEMA_VERSION:
        raise BenchmarkManifestError(f"SCHEMA_VERSION_MISMATCH:{line_number}")
    if record["ifc_schema"] != "IFC2X3":
        raise BenchmarkManifestError(f"UNSUPPORTED_IFC_SCHEMA:{line_number}")
    if len(record["source_sha256"]) != 64:
        raise BenchmarkManifestError(f"INVALID_SHA256:{line_number}")
    for field in (
        "size_bytes",
        "entity_count",
        "window_count",
        "valid_window_opening_wall_chain_count",
        "straight_wall_count",
        "unsupported_wall_count",
    ):
        value = record.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise BenchmarkManifestError(f"INVALID_COUNT:{line_number}:{field}")


def _source_identity(root: Path, local_path: str) -> dict[str, Any]:
    for manifest_name in ("bimnet-ifc2x3.jsonl", "raw-files.jsonl"):
        manifest = root / "dataset" / "manifests" / manifest_name
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("local_path") == local_path:
                return dict(record)
    external = json.loads(
        (root / "dataset" / "manifests" / "external-corpora.json").read_text(
            encoding="utf-8"
        )
    )
    for corpus in external["corpora"]:
        corpus_path = str(corpus["path"]).rstrip("/") + "/"
        if local_path.startswith(corpus_path):
            return {
                "corpus_id": corpus["corpus_id"],
                "source_revision": corpus["source_revision"],
            }
    raise BenchmarkManifestError(f"SOURCE_IDENTITY_NOT_FOUND:{local_path}")


def _project_split(root: Path, source_id: Any) -> str | None:
    if not isinstance(source_id, str):
        return None
    payload = json.loads(
        (root / "dataset" / "splits" / "bimnet-scene-splits.json").read_text(
            encoding="utf-8"
        )
    )
    for split, families in payload["splits"].items():
        for family in families:
            if source_id in family["file_ids"]:
                return str(split)
    return None


def _resolve_inside(root: Path, local_path: str) -> Path:
    resolved = (root / local_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise BenchmarkManifestError(f"PATH_OUTSIDE_ROOT:{local_path}") from error
    return resolved


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

