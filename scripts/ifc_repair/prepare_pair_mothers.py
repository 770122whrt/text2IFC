"""Prepare the fixed forty private mothers for new pair enumeration.

The first twenty reference bytes are bound to their original formal tasks.
The remaining twenty are the existing external collection's selected sources,
in sources.json order. Renumbering preserves source/review provenance; it does
not confer human acceptance. This module never discovers replacement sources,
parses geometry, runs native validation, or creates damage derivatives.

The dataset_pairs runner builds these specs internally. This CLI is a separate
preparation entry: writing its default output creates the collection root, so
subsequent generation must use another new root or --sources with a temporary
manifest. Importing/calling build_mother_specs never creates that root.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

# Reuse only the byte/HEADER and confined-path intake helpers. Source discovery
# and its external-register scan are deliberately not invoked.
from scripts.ifc_repair.dataset_batch.sources import _fingerprint, _safe_path

FORMAL_ROOT = Path("dataset/processed/ifc-repair/repair-comparison/formal")
EXTERNAL_COLLECTION = Path("dataset/processed/ifc-repair/external-20-pilot-40-20261010")
DEFAULT_OUTPUT = Path("dataset/processed/ifc-repair/formal-40-pairs-25-20261010/private/production/mother-sources.json")
SCHEMA_VERSION = "text2ifc/ifc-repair-pair-mothers/1.0"
_PILOT_FIELDS = ("pilot_cases", "pilot_families")


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required: {path.name}")
    return value


def _sha(path: Path) -> str:
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError(f"evidence_changed_during_read: {path.name}")
    return digest.hexdigest()


def _evidence(root: Path, path: Path, role: str, *, expected: str | None = None) -> dict:
    path = _safe_path(root, path.relative_to(root).as_posix())
    if not path.is_file():
        raise ValueError(f"missing_evidence: {path.relative_to(root).as_posix()}")
    digest = _sha(path)
    if expected is not None and digest != expected:
        raise ValueError(f"license_evidence_hash_mismatch: {path.relative_to(root).as_posix()}")
    return {"path": path.relative_to(root).as_posix(), "sha256": digest,
            "size_bytes": path.stat().st_size, "role": role}


def _clean_spec(value: dict) -> dict:
    copied = deepcopy(value)
    for field in _PILOT_FIELDS:
        copied.pop(field, None)
    return copied


def _bind_source(fingerprint: dict, expected: str, *records: dict) -> None:
    if not expected or expected != fingerprint["source_sha256"]:
        raise ValueError("hash_mismatch: required mother binding")
    for record in records:
        for field in ("source_sha256", "sha256"):
            if record.get(field) is not None and record[field] != fingerprint["source_sha256"]:
                raise ValueError(f"hash_mismatch: {field}")
        for field in ("size_bytes", "source_bytes"):
            if record.get(field) is not None and record[field] != fingerprint["size_bytes"]:
                raise ValueError(f"size_mismatch: {field}")


def _family(*records: tuple[str, dict]) -> tuple[str | None, str]:
    for prefix, record in records:
        for field in ("scene_family", "building_group", "source_family"):
            if record.get(field):
                return deepcopy(record[field]), f"{prefix}.{field}"
    return None, "not_recorded"


def _referenced_evidence(root: Path, evidence: list[dict], **records: dict) -> list[dict]:
    """Snapshot exactly named prior evidence; do not scan candidate directories.

    Historical files that are no longer present stay explicit missing records.
    This does not upgrade their old review or admission to a current result.
    Original IFC paths/hashes remain in source records; only the selected forty
    reference IFCs receive the actual mother byte/HEADER checks.
    """
    known = {item["path"] for item in evidence}
    unavailable = []

    def visit(value, field):
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, f"{field}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{field}[{index}]")
        elif isinstance(value, str):
            relative = value.replace("\\", "/")
            if (not relative.startswith(("dataset/", ".tmp/", "docs/", "scripts/", "tests/"))
                    or Path(relative).suffix.lower() not in {".json", ".jsonl", ".md", ".txt", ".log", ".csv", ".html"}):
                return
            path = _safe_path(root, relative)
            normalized = path.relative_to(root).as_posix()
            if normalized in known:
                return
            known.add(normalized)
            if path.is_file():
                item = _evidence(root, path, "referenced_prior_source_evidence")
                item["declared_by"] = field
                evidence.append(item)
            else:
                unavailable.append({"path": normalized, "declared_by": field})

    for field, record in records.items():
        visit(record, field)
    return unavailable


def _formal_spec(root: Path, number: int) -> dict:
    case_id = f"formal-{number:03d}"
    folder = root / FORMAL_ROOT / case_id
    private = folder / "private"
    task_path = private / "task.json"
    task = _json(task_path)
    if task.get("case_id", case_id) != case_id:
        raise ValueError("formal_task_id_mismatch")
    source = task.get("source")
    if not isinstance(source, dict):
        raise ValueError("formal_source_metadata_missing")
    record_path = private / "source-record.json"
    source_record = _json(record_path) if record_path.is_file() else {}
    reference = _safe_path(root, (FORMAL_ROOT / case_id / "private/reference.ifc").as_posix())
    fingerprint = _fingerprint(reference)
    _bind_source(fingerprint, task.get("source_sha256"), source, source_record)
    family, family_basis = _family(("task.source", source), ("source_record", source_record))
    evidence = [_evidence(root, task_path, "legacy_formal_task"),
                _evidence(root, private / "SOURCE-LICENSE.md", "legacy_source_license")]
    if source_record:
        evidence.append(_evidence(root, record_path, "legacy_source_record"))
    reviews = {}
    if "review" in task:
        reviews["task_review"] = deepcopy(task["review"])
    for path in sorted(private.glob("*.json")):
        if any(term in path.stem for term in ("review", "inspection", "checks", "validation", "readiness")):
            reviews[path.stem.replace("-", "_")] = _json(path)
            evidence.append(_evidence(root, path, "legacy_review_record"))
    for path in sorted((private / "attribution").rglob("*")):
        if path.is_file():
            evidence.append(_evidence(root, path, "legacy_source_attribution"))
    for name in ("REVIEW.md", "IFC-VALIDATION.md", "PIPELINE-CHECK.md", "VIEW.html"):
        if (folder / name).is_file():
            evidence.append(_evidence(root, folder / name, "legacy_review_view"))
    unavailable = _referenced_evidence(root, evidence, source=source, source_record=source_record)
    spec = {"source_id": case_id, "legacy_source_id": case_id, "kind": "formal", "legacy_kind": "formal",
            "input_path": reference.relative_to(root).as_posix(), **fingerprint,
            "source": _clean_spec(source), "license": deepcopy(source.get("license", source_record.get("license"))),
            "scene_family": family, "review_records": reviews,
            "provenance": {"evidence_files": evidence, "scene_family_basis": family_basis,
                           "unavailable_referenced_evidence": unavailable,
                           "reference_role": "original formal task-bound reference bytes; private planning/evaluation only"}}
    if source_record:
        spec["source_record"] = deepcopy(source_record)
    for field in ("source_url", "rights_source_url", "building_group", "source_family", "rights_conditions", "rights_policy"):
        if field in source:
            spec[field] = deepcopy(source[field])
        elif field in source_record:
            spec[field] = deepcopy(source_record[field])
    if "review" in task:
        spec["review"] = deepcopy(task["review"])
        if isinstance(task["review"], dict) and "human_viewed" in task["review"]:
            spec["human_viewed"] = deepcopy(task["review"]["human_viewed"])
    return spec


def _external_specs(root: Path) -> list[dict]:
    collection = root / EXTERNAL_COLLECTION
    selection_path, summary_path = collection / "sources.json", collection / "summary.json"
    selection, summary = _json(selection_path), _json(summary_path)
    chosen = selection.get("sources")
    if not isinstance(chosen, list) or len(chosen) != 20 or selection.get("source_count", 20) != 20:
        raise ValueError("selected_count_must_be_twenty")
    ids = [s.get("source_id") for s in chosen]
    if any(not isinstance(s, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", s) for s in ids):
        raise ValueError("unsafe_selected_source_id")
    if len(set(ids)) != 20:
        raise ValueError("duplicate_selected_source_id")
    if summary.get("status") != "complete":
        raise ValueError("collection_not_complete")
    rows = summary.get("sources", [])
    if (not isinstance(rows, list) or len(rows) != 20 or summary.get("source_models", 20) != 20
            or {s.get("source_id") for s in rows} != set(ids)):
        raise ValueError("selected_summary_source_mismatch")
    by_id = {s["source_id"]: s for s in rows}
    shared_evidence = [_evidence(root, selection_path, "frozen_selected_sources"),
                       _evidence(root, summary_path, "frozen_collection_summary")]
    # The collection-level license report is metadata, not a new rights lookup.
    license_review = selection.get("license_review")
    if isinstance(license_review, str):
        shared_evidence.append(_evidence(root, _safe_path(collection, license_review), "frozen_collection_license_review"))
    specs = []
    for index, selected in enumerate(chosen):
        legacy_id, row = selected["source_id"], by_id[selected["source_id"]]
        folder = collection / "sources" / legacy_id
        if row.get("status") != "complete" or row.get("source_unchanged") is not True:
            raise ValueError(f"{legacy_id}: source_not_frozen_complete")
        source_path = folder / "private/source.json"
        frozen = _json(source_path)
        summary_source = row.get("source")
        if not isinstance(summary_source, dict) or frozen.get("source_id") != legacy_id:
            raise ValueError(f"{legacy_id}: frozen_source_metadata_missing")
        # Validate the declared original path, but consume the sealed reference.
        _safe_path(root, selected.get("input_path"))
        reference = _safe_path(root, (EXTERNAL_COLLECTION / "sources" / legacy_id / "private/reference.ifc").as_posix())
        fingerprint = _fingerprint(reference)
        _bind_source(fingerprint, selected.get("source_sha256"), selected, frozen, summary_source, row)
        family, family_basis = _family(("selected_spec", selected), ("frozen_source", frozen))
        evidence = deepcopy(shared_evidence) + [_evidence(root, source_path, "frozen_source_specification")]
        for notice in selected.get("model_license_evidence", []):
            if not isinstance(notice, dict) or not notice.get("sha256"):
                raise ValueError(f"{legacy_id}: model_license_evidence_binding_missing")
            evidence.append(_evidence(root, _safe_path(collection, notice.get("path")), "sealed_model_license_evidence", expected=notice["sha256"]))
        records = {}
        for name in ("private/source-validation.json", "result.json"):
            path = folder / name
            if path.is_file():
                records[Path(name).stem.replace("-", "_")] = _json(path)
                evidence.append(_evidence(root, path, "prior_collection_machine_record"))
        if (folder / "SOURCE.md").is_file():
            evidence.append(_evidence(root, folder / "SOURCE.md", "prior_collection_source_view"))
        unavailable = _referenced_evidence(root, evidence, selected_spec=selected, frozen_source=frozen)
        spec = _clean_spec(frozen)
        spec.update({k: deepcopy(v) for k, v in _clean_spec(selected).items()})
        legacy_kind = frozen.get("kind", "external")
        spec.update({"source_id": f"formal-{index + 21:03d}", "legacy_source_id": legacy_id,
                     "kind": legacy_kind, "legacy_kind": legacy_kind,
                     "source": _clean_spec(frozen), "selection_record": _clean_spec(selected),
                     "input_path": reference.relative_to(root).as_posix(), **fingerprint,
                     "scene_family": family, "review_records": records,
                     "provenance": {"evidence_files": evidence, "selected_source_index": index,
                                    "scene_family_basis": family_basis,
                                    "unavailable_referenced_evidence": unavailable,
                                    "prior_source_native_passed": row.get("source_native_passed"),
                                    "reference_role": "sealed selected mother reference bytes; private planning/evaluation only"}})
        specs.append(spec)
    return specs


def build_mother_specs(repository_root: Path) -> list[dict]:
    """Return the fixed forty specs without writing or changing any admission."""
    root = Path(repository_root).resolve()
    specs = []
    hashes = set()
    for number in range(1, 21):
        case_id = f"formal-{number:03d}"
        try:
            specs.append(_formal_spec(root, number))
        except (OSError, ValueError) as exc:
            raise ValueError(f"{case_id}: {exc}") from exc
    specs.extend(_external_specs(root))
    for spec in specs:
        if spec["source_sha256"] in hashes:
            raise ValueError(f"{spec['source_id']}: duplicate_content")
        hashes.add(spec["source_sha256"])
    return specs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="New private JSON file; existing files are never overwritten")
    args = parser.parse_args(argv)
    root = args.repository_root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    specs = build_mother_specs(root)
    manifest = {"schema_version": SCHEMA_VERSION, "private_manifest": True,
                "scope": "Fixed mother planning/evaluation provenance; never Provider input; no new native/mesh validation",
                "source_count": len(specs), "sources": specs}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(output), "source_count": len(specs),
                      "unique_source_hashes": len({s["source_sha256"] for s in specs}),
                      "schemas": sorted({s["schema"] for s in specs}),
                      "largest_source_bytes": max(s["size_bytes"] for s in specs)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
