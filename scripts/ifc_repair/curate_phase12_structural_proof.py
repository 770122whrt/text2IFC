"""Strictly validate and curate Phase 12 offline structural Proof cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Mapping

import ifcopenshell

try:
    from scripts.ifc_repair.validate_success_cases import (
        validate_success_case_collection,
    )
except ModuleNotFoundError:  # Direct execution from scripts/ifc_repair.
    from validate_success_cases import validate_success_case_collection


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "dataset/processed/ifc-repair/phase12-offline"
DEFAULT_COLLECTION = ROOT / "dataset/processed/proof/ifc-repair-success-cases"
EVIDENCE_MODE = "offline_bound_deterministic"
EVIDENCE_SCOPE = "cross_scene_same_family_bimnet"
SCOPE_SENTENCE = (
    "Cross-scene, same-family BIMNet evidence only; "
    "not cross-dataset generalization."
)
SUCCESS_CASE_IDS = frozenset(
    {
        "phase12-d7n-beam-loadbearing",
        "phase12-d7n-column-loadbearing",
        "phase12-d7n-beam-column-atomic",
        "phase12-vvo-beam-material-present",
        "phase12-vvo-column-material-absent",
        "phase12-vvo-door-window-beam-column-atomic",
    }
)
FAILURE_CASE_IDS = frozenset(
    {
        "phase12-d7n-beam-column-rollback",
        "phase12-vvo-door-window-beam-column-rollback",
    }
)
FAILURE_INPUT_CONTRACTS = {
    "phase12-d7n-beam-column-rollback": {
        "damaged_path": "attempt/damaged.ifc",
        "sha256": (
            "sha256:43b6756b88874f9525f6a511d7dc718844dac59b638a11e3fbc36b321e0ab8b7"
        ),
        "bytes": 3_293_724,
        "blocking_code": "STRUCTURAL_SAME_AXIS_OVERLAP",
    },
    "phase12-vvo-door-window-beam-column-rollback": {
        "damaged_path": "damaged.ifc",
        "sha256": (
            "sha256:6824086b4171cce034acaa23ad51c3020d87ed44c0aead62979a4b4ad17c4db3"
        ),
        "bytes": 2_431_536,
        "blocking_code": "STRUCTURAL_SAME_AXIS_OVERLAP",
    },
}
REQUIRED_COVERAGE = frozenset(
    {
        "beam_only",
        "column_only",
        "beam_column_atomic",
        "beam_loadbearing",
        "column_loadbearing",
        "material_present",
        "material_absent",
        "rollback",
        "door_window_beam_column_atomic",
        "door_window_beam_column_rollback",
    }
)

FAMILY_BY_OPERATION = {
    "add_beam": "beam",
    "add_column": "column",
    "add_window_with_opening_to_wall": "window",
    "fill_existing_opening_with_door": "door",
}
ROLE_BY_BASENAME = {
    "original.ifc": "original_ground_truth",
    "damaged.ifc": "repair_input_ifc",
    "repaired.ifc": "published_repair_output",
    "request.txt": "user_request",
    "repair-intent.json": "stage1_repair_intent",
    "target-resolution.json": "deterministic_target_resolution",
    "semantic-manifest.json": "semantic_manifest",
    "semantic-manifests.json": "semantic_manifests",
    "changeset.json": "bound_changeset",
    "application.json": "application_result",
    "evaluation.json": "production_evaluation",
    "comparison.json": "ifc_comparison",
    "production-boundary.json": "production_input_boundary",
    "mutation_manifest.private.json": "mutation_manifest_private",
    "private-evaluation.json": "private_ground_truth_evaluation",
    "three-way-audit.json": "three_way_l0_l1_l2_audit",
    "release-decision.json": "l0_l1_l2_release_decision",
    "AUDIT-REPORT.md": "human_readable_three_way_audit",
}
REQUIRED_SOURCE_BASENAMES = frozenset(
    {
        "original.ifc",
        "damaged.ifc",
        "repaired.ifc",
        "request.txt",
        "repair-intent.json",
        "target-resolution.json",
        "changeset.json",
        "application.json",
        "evaluation.json",
        "comparison.json",
        "production-boundary.json",
        "mutation_manifest.private.json",
    }
)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        value
        if isinstance(value, str)
        else json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    )
    path.write_text(payload.rstrip() + "\n", encoding="utf-8")


def _write_atomic(path: Path, value: Any) -> None:
    payload = (
        value
        if isinstance(value, str)
        else json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.phase12.tmp")
    try:
        temporary.write_text(payload.rstrip() + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _safe_relative(raw: Any) -> Path:
    text = str(raw).replace("\\", "/")
    path = Path(text)
    if not text or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"SOURCE_ARTIFACT_PATH_UNSAFE:{text}")
    return path


def _safe_case_id(raw: Any) -> str:
    case_id = str(raw or "")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", case_id):
        raise ValueError(f"SOURCE_CASE_ID_UNSAFE:{case_id}")
    return case_id


def _artifact_records(
    manifest: Mapping[str, Any],
) -> list[tuple[str, Path, Mapping[str, Any]]]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping) or not artifacts:
        raise ValueError("SOURCE_MANIFEST_ARTIFACTS_REQUIRED")
    records: list[tuple[str, Path, Mapping[str, Any]]] = []
    seen_paths: set[str] = set()
    for raw_name, raw_entry in artifacts.items():
        if not isinstance(raw_entry, Mapping):
            raise ValueError(f"SOURCE_ARTIFACT_RECORD_REQUIRED:{raw_name}")
        relative = _safe_relative(raw_entry.get("path") or raw_name)
        normalized = relative.as_posix()
        if normalized in seen_paths:
            raise ValueError(f"SOURCE_ARTIFACT_PATH_DUPLICATE:{normalized}")
        seen_paths.add(normalized)
        records.append((str(raw_name), relative, raw_entry))
    return records


def _validate_source_case(
    case_dir: Path,
    *,
    summary_record: Mapping[str, Any],
) -> tuple[dict[str, Any], list[tuple[str, Path, Mapping[str, Any]]]]:
    if summary_record.get("status") != "passed":
        raise ValueError("SOURCE_SUMMARY_CASE_NOT_PASSED")
    manifest = _read(case_dir / "manifest.json")
    case_id = _safe_case_id(summary_record.get("case_id"))
    if manifest.get("case_id") != case_id:
        raise ValueError("SOURCE_CASE_ID_MISMATCH")
    if manifest.get("status") != "passed":
        raise ValueError("SOURCE_CASE_NOT_PASSED")
    if manifest.get("schema_version") != "text2ifc/phase12-offline-case/0.1":
        raise ValueError("SOURCE_PHASE12_SCHEMA_MISMATCH")
    if manifest.get("evidence_scope") != EVIDENCE_SCOPE:
        raise ValueError("SOURCE_CASE_SCOPE_MISMATCH")
    if manifest.get("provider_evidence_mode") != EVIDENCE_MODE:
        raise ValueError("SOURCE_PROVIDER_EVIDENCE_MODE_MISMATCH")
    if manifest.get("synthetic_fallback_used") is not False:
        raise ValueError("SOURCE_SYNTHETIC_FALLBACK_NOT_FALSE")
    source = manifest.get("source")
    if not isinstance(source, Mapping) or source.get("schema") != "IFC2X3":
        raise ValueError("SOURCE_SCHEMA_NOT_IFC2X3")

    records = _artifact_records(manifest)
    basenames = {relative.name for _, relative, _ in records}
    reserved = sorted(basenames & {"FILES.json", "REPORT.md", "manifest.json"})
    if reserved:
        raise ValueError("SOURCE_ARTIFACT_PATH_RESERVED:" + ",".join(reserved))
    missing = sorted(REQUIRED_SOURCE_BASENAMES - basenames)
    if missing:
        raise ValueError("SOURCE_REQUIRED_ARTIFACTS_MISSING:" + ",".join(missing))
    semantic_basenames = basenames & {
        "semantic-manifest.json",
        "semantic-manifests.json",
    }
    if len(semantic_basenames) != 1:
        raise ValueError("SOURCE_SEMANTIC_MANIFEST_CARDINALITY")
    for name, relative, entry in records:
        artifact = case_dir / relative
        if not artifact.is_file():
            raise FileNotFoundError(f"SOURCE_ARTIFACT_MISSING:{relative.as_posix()}")
        if artifact.stat().st_size != int(entry.get("bytes", -1)):
            raise ValueError(f"SOURCE_ARTIFACT_SIZE_MISMATCH:{name}")
        if _sha256(artifact) != str(entry.get("sha256")):
            raise ValueError(f"SOURCE_ARTIFACT_HASH_MISMATCH:{name}")
    indexed_paths = {relative.as_posix() for _, relative, _ in records}
    actual_paths = {
        path.relative_to(case_dir).as_posix()
        for path in case_dir.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    if actual_paths != indexed_paths:
        raise ValueError("SOURCE_MANIFEST_ARTIFACT_COVERAGE_MISMATCH")

    by_basename = {relative.name: case_dir / relative for _, relative, _ in records}
    for name in ("original.ifc", "damaged.ifc", "repaired.ifc"):
        if ifcopenshell.open(str(by_basename[name])).schema != "IFC2X3":
            raise ValueError(f"SOURCE_IFC_SCHEMA_MISMATCH:{name}")

    changeset = _read(by_basename["changeset.json"])
    if changeset.get("semantic_manifest_ref") != next(iter(semantic_basenames)):
        raise ValueError("SOURCE_SEMANTIC_MANIFEST_REF_MISMATCH")
    operation_count = int(manifest.get("operation_count", -1))
    operations = changeset.get("operations")
    if not isinstance(operations, list) or len(operations) != operation_count:
        raise ValueError("SOURCE_CHANGESET_OPERATION_COUNT_MISMATCH")
    if int(summary_record.get("operation_count", -1)) != operation_count:
        raise ValueError("SOURCE_SUMMARY_OPERATION_COUNT_MISMATCH")
    operation_types = sorted({str(item.get("operation_type")) for item in operations})
    if summary_record.get("operation_types") != operation_types:
        raise ValueError("SOURCE_SUMMARY_OPERATION_TYPES_MISMATCH")
    if changeset.get("base_model_fingerprint") != _sha256(
        by_basename["damaged.ifc"]
    ):
        raise ValueError("SOURCE_CHANGESET_FINGERPRINT_MISMATCH")

    application = _read(by_basename["application.json"])
    if (
        application.get("valid") is not True
        or application.get("published") is not True
        or len(application.get("operations", ())) != operation_count
    ):
        raise ValueError("SOURCE_APPLICATION_NOT_PUBLISHED")
    evaluation = _read(by_basename["evaluation.json"])
    if (
        evaluation.get("status") != "passed"
        or evaluation.get("complete_repair_success") is not True
        or evaluation.get("successful_artifact_publishable") is not True
        or len(evaluation.get("operations", ())) != operation_count
    ):
        raise ValueError("SOURCE_EVALUATION_NOT_PUBLISHABLE")
    for operation in evaluation["operations"]:
        levels = {
            str(item.get("level")): item.get("status")
            for item in operation.get("levels", ())
            if isinstance(item, Mapping)
        }
        if levels.get("L1") != "passed" or levels.get("L2") != "passed":
            raise ValueError(
                f"SOURCE_OPERATION_GATE_FAILED:{operation.get('operation_id')}"
            )
    comparison = _read(by_basename["comparison.json"])
    if comparison.get("complete_preservation_success") is not True:
        raise ValueError("SOURCE_COMPARISON_NOT_PRESERVED")
    boundary = _read(by_basename["production-boundary.json"])
    if any(
        boundary.get(key) is not False
        for key in (
            "original_ifc_supplied",
            "mutation_manifest_supplied",
            "deleted_object_ids_supplied",
            "private_comparator_available_during_repair",
        )
    ):
        raise ValueError("SOURCE_PRODUCTION_BOUNDARY_NOT_ISOLATED")
    return manifest, records


def _validate_failure_matrix(
    source_root: Path,
    records: Any,
) -> None:
    if not isinstance(records, list) or any(
        not isinstance(item, Mapping) for item in records
    ):
        raise ValueError("PHASE12_FAILURE_RECORDS_REQUIRED")
    by_id = {_safe_case_id(item.get("case_id")): item for item in records}
    if set(by_id) != FAILURE_CASE_IDS or len(by_id) != len(records):
        raise ValueError("PHASE12_FAILURE_MATRIX_MISMATCH")
    for case_id, record in by_id.items():
        contract = FAILURE_INPUT_CONTRACTS[case_id]
        case_root = source_root / "failed" / case_id
        failure_path = case_root / "failure.json"
        if not failure_path.is_file() or _read(failure_path) != dict(record):
            raise ValueError(f"PHASE12_FAILURE_ARTIFACT_MISMATCH:{case_id}")
        damaged_path = case_root / str(contract["damaged_path"])
        artifact_root = damaged_path.parent
        application_path = artifact_root / "application.json"
        application = _read(application_path)
        issues = application.get("issues")
        blocking = (
            str(issues[0].get("code") or "")
            if isinstance(issues, list) and issues
            else ""
        )
        if (
            blocking != contract["blocking_code"]
            or record.get("blocking_code") != contract["blocking_code"]
        ):
            raise ValueError(f"PHASE12_FAILURE_CAUSE_MISMATCH:{case_id}")
        changeset_path = artifact_root / "changeset.json"
        if not damaged_path.is_file() or not changeset_path.is_file():
            raise ValueError(f"PHASE12_FAILURE_INPUT_MISSING:{case_id}")
        damaged_hash = _sha256(damaged_path)
        damaged_bytes = damaged_path.stat().st_size
        changeset_fingerprint = str(
            _read(changeset_path).get("base_model_fingerprint") or ""
        )
        if (
            damaged_hash != contract["sha256"]
            or damaged_bytes != contract["bytes"]
            or record.get("damaged_ifc_sha256") != damaged_hash
            or record.get("damaged_ifc_bytes") != damaged_bytes
            or record.get("changeset_base_model_fingerprint")
            != damaged_hash
            or changeset_fingerprint != damaged_hash
        ):
            raise ValueError(
                f"PHASE12_FAILURE_INPUT_FINGERPRINT_MISMATCH:{case_id}"
            )
        if ifcopenshell.open(str(damaged_path)).schema != "IFC2X3":
            raise ValueError(f"PHASE12_FAILURE_INPUT_SCHEMA_MISMATCH:{case_id}")
        if (
            record.get("status") != "failed_expected"
            or record.get("valid") is not False
            or record.get("published") is not False
            or record.get("source_unchanged") is not True
            or application.get("valid") is not False
            or application.get("published") is not False
            or list(case_root.rglob("repaired.ifc"))
        ):
            raise ValueError(f"PHASE12_FAILURE_NOT_FAIL_CLOSED:{case_id}")


def _classification(
    changeset: Mapping[str, Any],
) -> tuple[str, str, str, list[str]]:
    operations = changeset.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValueError("SOURCE_CHANGESET_OPERATIONS_REQUIRED")
    operation_types = sorted({str(item["operation_type"]) for item in operations})
    try:
        families = {FAMILY_BY_OPERATION[item] for item in operation_types}
    except KeyError as error:
        raise ValueError(f"UNSUPPORTED_PHASE12_OPERATION:{error.args[0]}") from error
    operation_count = len(operations)
    if families <= {"beam", "column"}:
        kind = "single" if operation_count == 1 else "batch"
        return "structural", kind, f"structural/{kind}", operation_types
    if families == {"beam", "column", "door", "window"}:
        return (
            "mixed",
            "mixed",
            "mixed/door-window-beam-column",
            operation_types,
        )
    raise ValueError("UNSUPPORTED_PHASE12_FAMILY_SET:" + ",".join(sorted(families)))


def _role(relative: Path, used_roles: set[str]) -> str:
    role = ROLE_BY_BASENAME.get(relative.name)
    if role is None:
        stem = "".join(
            character if character.isalnum() else "_"
            for character in relative.as_posix().casefold()
        ).strip("_")
        role = f"source_artifact_{stem}"
    if role in used_roles:
        raise ValueError(f"SOURCE_ARTIFACT_ROLE_DUPLICATE:{role}")
    used_roles.add(role)
    return role


def _stage_case(
    *,
    source_case: Path,
    stage_root: Path,
    summary_record: Mapping[str, Any],
) -> dict[str, Any]:
    source_manifest, records = _validate_source_case(
        source_case,
        summary_record=summary_record,
    )
    changeset_path = next(
        source_case / relative
        for _, relative, _ in records
        if relative.name == "changeset.json"
    )
    changeset = _read(changeset_path)
    operation_family, case_kind, bucket, operation_types = _classification(changeset)
    case_id = str(source_manifest["case_id"])
    relative_case = f"{bucket}/{case_id}"
    destination = stage_root / relative_case
    destination.mkdir(parents=True, exist_ok=False)

    used_roles: set[str] = set()
    file_entries: list[dict[str, Any]] = []
    for _, relative, _ in records:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_case / relative, target)
        file_entries.append(
            {
                "path": relative.as_posix(),
                "role": _role(relative, used_roles),
                "size_bytes": target.stat().st_size,
                "sha256": _sha256(target),
            }
        )

    source_manifest_target = destination / "manifest.json"
    shutil.copy2(source_case / "manifest.json", source_manifest_target)
    if "source_run_manifest" in used_roles:
        raise ValueError("SOURCE_ARTIFACT_ROLE_DUPLICATE:source_run_manifest")
    used_roles.add("source_run_manifest")
    file_entries.append(
        {
            "path": "manifest.json",
            "role": "source_run_manifest",
            "size_bytes": source_manifest_target.stat().st_size,
            "sha256": _sha256(source_manifest_target),
        }
    )

    files = {
        "schema_version": "text2ifc/ifc-repair-proof-files/0.2",
        "case_id": case_id,
        "files": sorted(file_entries, key=lambda item: item["path"]),
    }
    _write(destination / "FILES.json", files)
    report = (
        f"# {case_id}\n\n"
        "Phase 12 offline Beam/Column operation Proof. The source manifest, "
        "every declared artifact hash and size, all three IFC2X3 files, L1/L2 "
        "publication gates, preservation, and production-input isolation were "
        "rechecked before curation.\n\n"
        f"- Operations: {', '.join(operation_types)}\n"
        f"- Operation count: {source_manifest['operation_count']}\n"
        f"- Provider evidence mode: `{EVIDENCE_MODE}`\n"
        "- Synthetic fallback: `false`\n"
        f"- Evidence scope: {SCOPE_SENTENCE}\n"
    )
    _write(destination / "REPORT.md", report)

    by_basename = {relative.name: relative for _, relative, _ in records}
    entry: dict[str, Any] = {
        "case_id": case_id,
        "phase": "12",
        "operation_family": operation_family,
        "case_kind": case_kind,
        "operation_types": operation_types,
        "operation_count": int(source_manifest["operation_count"]),
        "provider": str(source_manifest.get("provider") or "offline-deterministic"),
        "model": str(source_manifest.get("model") or "phase12-bound-fixture"),
        "provider_evidence_mode": EVIDENCE_MODE,
        "evidence_scope": EVIDENCE_SCOPE,
        "status": "accepted",
        "report": f"{relative_case}/REPORT.md",
        "files": f"{relative_case}/FILES.json",
        "original_ifc": f"{relative_case}/{by_basename['original.ifc'].as_posix()}",
        "damaged_ifc": f"{relative_case}/{by_basename['damaged.ifc'].as_posix()}",
        "repaired_ifc": f"{relative_case}/{by_basename['repaired.ifc'].as_posix()}",
    }
    if len(operation_types) == 1:
        entry["operation_type"] = operation_types[0]
    return entry


def _candidate_manifest(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/ifc-repair-success-collection/0.1",
        "collection_id": "ifc-repair-success-cases-phase12-candidate",
        "case_count": len(entries),
        "cases": entries,
        "evidence_scope": EVIDENCE_SCOPE,
    }


def _install_cases(
    *,
    stage_root: Path,
    collection_root: Path,
    entries: list[dict[str, Any]],
) -> list[tuple[Path, Path | None]]:
    backup_root = stage_root / ".replaced"
    installed: list[tuple[Path, Path | None]] = []
    try:
        for entry in entries:
            relative_case = Path(str(entry["files"])).parent
            staged = stage_root / relative_case
            destination = collection_root / relative_case
            destination.parent.mkdir(parents=True, exist_ok=True)
            backup: Path | None = None
            if destination.exists():
                backup = backup_root / relative_case
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(destination, backup)
            installed.append((destination, backup))
            shutil.copytree(staged, destination)
            shutil.rmtree(staged)
    except Exception:
        _rollback_installed_cases(installed)
        raise
    return installed


def _rollback_installed_cases(
    installed: list[tuple[Path, Path | None]],
) -> None:
    for destination, backup in reversed(installed):
        if destination.exists():
            shutil.rmtree(destination)
        if backup is not None and backup.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            os.replace(backup, destination)


def curate(
    source_root: Path = DEFAULT_SOURCE,
    collection_root: Path = DEFAULT_COLLECTION,
) -> dict[str, Any]:
    source_root = Path(source_root).resolve()
    collection_root = Path(collection_root).resolve()
    summary = _read(source_root / "run-summary.json")
    if summary.get("status") != "passed" or summary.get("matrix_complete") is not True:
        raise ValueError("PHASE12_SOURCE_RUN_NOT_PASSED")
    if summary.get("evidence_scope") != EVIDENCE_SCOPE:
        raise ValueError("PHASE12_SOURCE_SCOPE_MISMATCH")
    accepted = summary.get("accepted_cases")
    if not isinstance(accepted, list) or not accepted:
        raise ValueError("PHASE12_ACCEPTED_CASES_REQUIRED")
    if any(not isinstance(item, Mapping) for item in accepted):
        raise ValueError("PHASE12_ACCEPTED_CASE_RECORD_INVALID")
    case_ids = [_safe_case_id(item.get("case_id")) for item in accepted]
    if set(case_ids) != SUCCESS_CASE_IDS or len(case_ids) != len(SUCCESS_CASE_IDS):
        raise ValueError("PHASE12_ACCEPTED_CASE_IDS_INVALID")
    coverage = summary.get("coverage")
    if (
        not isinstance(coverage, Mapping)
        or set(coverage) != REQUIRED_COVERAGE
        or any(coverage[key] is not True for key in REQUIRED_COVERAGE)
    ):
        raise ValueError("PHASE12_FIXED_COVERAGE_INCOMPLETE")
    _validate_failure_matrix(source_root, summary.get("failed_cases"))

    collection_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".phase12-curation-",
        dir=collection_root.parent,
    ) as temporary:
        stage_root = Path(temporary)
        entries: list[dict[str, Any]] = []
        for record in accepted:
            relative = _safe_relative(record.get("relative_path"))
            if not relative.parts or relative.parts[0] != "accepted":
                raise ValueError("PHASE12_ACCEPTED_CASE_PATH_INVALID")
            entries.append(
                _stage_case(
                    source_case=source_root / relative,
                    stage_root=stage_root,
                    summary_record=record,
                )
            )

        _write(stage_root / "manifest.json", _candidate_manifest(entries))
        validation = validate_success_case_collection(stage_root)
        if validation.status != "passed":
            raise ValueError(
                "PHASE12_CANDIDATE_VALIDATION_FAILED:"
                + " | ".join(validation.errors)
            )
        if validation.independently_recomputed_case_count != len(entries):
            raise ValueError("PHASE12_CANDIDATE_NOT_FULLY_RECOMPUTED")

        collection_manifest_path = collection_root / "manifest.json"
        original_manifest = collection_manifest_path.read_bytes()
        collection = _read(collection_manifest_path)
        curated_ids = {entry["case_id"] for entry in entries}
        existing_cases = collection.get("cases")
        if not isinstance(existing_cases, list):
            raise ValueError("COLLECTION_CASES_REQUIRED")
        replaceable_paths: set[Path] = set()
        for item in existing_cases:
            if item.get("case_id") not in curated_ids:
                continue
            if (
                item.get("phase") != "12"
                or item.get("provider_evidence_mode") != EVIDENCE_MODE
            ):
                raise ValueError(f"COLLECTION_CASE_ID_CONFLICT:{item.get('case_id')}")
            replaceable_paths.add(Path(str(item["files"])).parent)
        for entry in entries:
            relative_case = Path(str(entry["files"])).parent
            destination = collection_root / relative_case
            if destination.exists() and relative_case not in replaceable_paths:
                raise ValueError(f"COLLECTION_CASE_PATH_CONFLICT:{relative_case}")
        retained = [
            item
            for item in existing_cases
            if not (
                item.get("phase") == "12"
                and item.get("case_id") in curated_ids
                and item.get("provider_evidence_mode") == EVIDENCE_MODE
            )
        ]
        collection["cases"] = [*retained, *entries]
        collection["case_count"] = len(collection["cases"])
        collection["operation_families"] = sorted(
            {str(item["operation_family"]) for item in collection["cases"]}
        )
        collection["evidence_scope"] = EVIDENCE_SCOPE
        collection["generated_at"] = date.today().isoformat()
        collection["future_operation_families"] = [
            item
            for item in collection.get("future_operation_families", ())
            if item not in {"beam", "column"}
        ]

        readme_path = collection_root / "README.md"
        original_readme = readme_path.read_bytes()
        readme = readme_path.read_text(encoding="utf-8")
        if SCOPE_SENTENCE not in readme:
            readme = readme.rstrip() + "\n\n" + SCOPE_SENTENCE + "\n"

        installed = _install_cases(
            stage_root=stage_root,
            collection_root=collection_root,
            entries=entries,
        )
        try:
            _write_atomic(collection_manifest_path, collection)
            _write_atomic(readme_path, readme)
            final_validation = validate_success_case_collection(collection_root)
            if final_validation.status != "passed":
                raise ValueError(
                    "PHASE12_FINAL_COLLECTION_VALIDATION_FAILED:"
                    + " | ".join(final_validation.errors)
                )
            validated_by_id = {
                item["case_id"]: item for item in final_validation.cases
            }
            if any(
                validated_by_id.get(entry["case_id"], {}).get(
                    "structural_audit_coverage"
                )
                != "strict_structural_recomputed"
                for entry in entries
            ):
                raise ValueError("PHASE12_FINAL_CASE_NOT_STRICTLY_RECOMPUTED")
        except Exception:
            _rollback_installed_cases(installed)
            collection_manifest_path.write_bytes(original_manifest)
            readme_path.write_bytes(original_readme)
            raise

    return {
        "schema_version": "text2ifc/phase12-proof-curation/0.1",
        "status": "passed",
        "case_count": len(entries),
        "operation_count": sum(int(item["operation_count"]) for item in entries),
        "cases": [item["case_id"] for item in entries],
        "evidence_scope": EVIDENCE_SCOPE,
        "independently_recomputed_case_count": len(entries),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--collection-root", type=Path, default=DEFAULT_COLLECTION)
    args = parser.parse_args(argv)
    result = curate(args.source_root, args.collection_root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
