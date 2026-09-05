"""Composite strict reopen verification (L0/L1/L2 recompute).

Same contract as ``run_phase12_live_uat._strict_reopen_verification`` but
parameterized by the frozen composite model path and hash instead of the
phase12 frozen source, so it can verify the composite cases' sources.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import ifcopenshell

from scripts.ifc_repair.run_phase12_live_uat import (
    _path_sha256,
    _read_json,
    _safe_artifact_path,
)
from scripts.ifc_repair.validate_success_cases import audit_repaired_operations

PROOF_VALIDATION_PENDING = "pending_composite_curation"


def strict_reopen_verification(
    *,
    runtime: Path,
    final: Mapping[str, Any],
    source_path: Path,
    expected_source_sha256: str,
) -> dict[str, Any]:
    if not final.get("successful_artifact_publishable"):
        return {
            "status": "not_applicable",
            "l0_pass": None,
            "l1_pass": None,
            "l2_pass": None,
            "preservation_status": PROOF_VALIDATION_PENDING,
            "ground_truth_isolation_status": PROOF_VALIDATION_PENDING,
            "proof_validation_status": PROOF_VALIDATION_PENDING,
        }
    try:
        runs_root = (runtime / "runs").resolve()
        run_root = (runs_root / str(final["run_id"])).resolve()
        run_root.relative_to(runs_root)
        artifacts = final.get("artifacts")
        if not isinstance(artifacts, Mapping):
            raise ValueError("LIVE_RESULT_ARTIFACTS_MISSING")
        manifest_path = _safe_artifact_path(run_root, str(artifacts["manifest"]))
        evaluation_path = _safe_artifact_path(
            run_root, str(artifacts["evaluation"])
        )
        repaired_path = _safe_artifact_path(
            run_root, str(artifacts["successful_ifc"])
        )
        manifest = _read_json(manifest_path)
        entries = manifest.get("artifacts")
        if not isinstance(entries, list) or not entries:
            raise ValueError("LIVE_MANIFEST_EMPTY")
        for entry in entries:
            path = _safe_artifact_path(run_root, str(entry["path"]))
            if (
                path.stat().st_size != int(entry["size_bytes"])
                or _path_sha256(path).removeprefix("sha256:")
                != str(entry["sha256"]).removeprefix("sha256:")
            ):
                raise ValueError("LIVE_MANIFEST_HASH_MISMATCH")
        state = _read_json(run_root / "state.json")
        source = state.get("source")
        if not isinstance(source, Mapping):
            raise ValueError("LIVE_SOURCE_BINDING_MISSING")
        resolved_source = Path(str(source["reference"])).resolve()
        if resolved_source != source_path.resolve():
            raise ValueError("LIVE_SOURCE_PATH_MISMATCH")
        if not resolved_source.is_file():
            raise ValueError("LIVE_SOURCE_MISSING")
        if (
            _path_sha256(resolved_source) != expected_source_sha256
            or str(source.get("sha256")) != expected_source_sha256
        ):
            raise ValueError("LIVE_SOURCE_HASH_MISMATCH")
        damaged = ifcopenshell.open(str(resolved_source))
        repaired = ifcopenshell.open(str(repaired_path))
        if str(repaired.schema) != "IFC2X3":
            raise ValueError("LIVE_REPAIRED_SCHEMA_INVALID")
        changeset_path = run_root / "changeset" / "bound-changeset.json"
        if not changeset_path.is_file():
            changeset_path = run_root / "changeset.json"
        changeset = _read_json(changeset_path)
        evidence_path = manifest_path.parent / "terminal" / "evidence.json"
        evidence = _read_json(evidence_path).get("evidence")
        if not isinstance(evidence, Mapping):
            raise ValueError("LIVE_APPLICATION_EVIDENCE_MISSING")
        application = evidence.get("application")
        if not isinstance(application, Mapping):
            raise ValueError("LIVE_APPLICATION_EVIDENCE_MISSING")
        evaluation = _read_json(evaluation_path)
        operations = changeset.get("operations")
        if not isinstance(operations, list) or not operations:
            raise ValueError("LIVE_CHANGESET_OPERATIONS_MISSING")
        l0 = (
            changeset.get("binding_status") == "bound"
            and changeset.get("base_model_fingerprint") == source.get("sha256")
            and application.get("valid") is True
            and application.get("published") is True
            and evaluation.get("status") == "passed"
            and evaluation.get("complete_repair_success") is True
            and evaluation.get("successful_artifact_publishable") is True
            and len(application.get("operations", ())) == len(operations)
        )
        if not l0:
            raise ValueError("LIVE_L0_RECOMPUTE_FAILED")
        recomputed = audit_repaired_operations(
            changeset=changeset,
            application=application,
            damaged_model=damaged,
            repaired_model=repaired,
        )
        l1 = recomputed["l1_operation_count"] == len(operations)
        l2 = recomputed["l2_operation_count"] == len(operations)
        if not l1 or not l2:
            raise ValueError("LIVE_L1_L2_RECOMPUTE_FAILED")
        return {
            "status": "passed",
            "l0_pass": True,
            "l1_pass": l1,
            "l2_pass": l2,
            "preservation_status": PROOF_VALIDATION_PENDING,
            "ground_truth_isolation_status": PROOF_VALIDATION_PENDING,
            "proof_validation_status": PROOF_VALIDATION_PENDING,
            "operation_count": len(operations),
            "reopened_schema": str(repaired.schema),
            "successful_ifc_sha256": _path_sha256(repaired_path),
            "changeset_sha256": _path_sha256(changeset_path),
            "evaluation_sha256": _path_sha256(evaluation_path),
        }
    except Exception as error:
        return {
            "status": "failed",
            "l0_pass": False,
            "l1_pass": False,
            "l2_pass": False,
            "preservation_status": PROOF_VALIDATION_PENDING,
            "ground_truth_isolation_status": PROOF_VALIDATION_PENDING,
            "proof_validation_status": PROOF_VALIDATION_PENDING,
            "reason_code": str(error).split(":", 1)[0][:128],
            "reason_detail": str(error)[:512],
        }


__all__ = ["strict_reopen_verification"]
