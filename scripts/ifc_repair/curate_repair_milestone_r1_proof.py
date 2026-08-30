"""Curate Repair Milestone R1 Proof through frozen, profile-driven metadata.

This is the R1 successor path.  It deliberately leaves the historical Plan 07
curator and its hard-coded provenance untouched.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import hashlib
from pathlib import Path
from typing import Any, Mapping

try:
    from scripts.ifc_repair.validate_success_cases import (
        validate_proof_validation_document_v03,
        validate_r1_proof_collection,
    )
except ModuleNotFoundError:  # Direct script execution.
    from validate_success_cases import (
        validate_proof_validation_document_v03,
        validate_r1_proof_collection,
    )


PROVENANCE_NAMESPACE = "repair-milestone-r1"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def curate_r1_proof(
    *,
    source_root: Path | str,
    destination_root: Path | str,
    validation_document: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and atomically install one complete R1 Proof collection."""

    source = Path(source_root).resolve()
    destination = Path(destination_root).resolve()
    if source == destination or destination.exists():
        raise ValueError("R1_CURATOR_DESTINATION_NOT_EMPTY")
    manifest = _read_json(source / "manifest.json")
    if (
        manifest.get("schema_version")
        != "text2ifc/ifc-repair-proof-collection/0.2"
        or manifest.get("provenance_namespace") != PROVENANCE_NAMESPACE
    ):
        raise ValueError("R1_CURATOR_COLLECTION_CONTRACT")
    profile_path = (source / str(manifest.get("profile") or "")).resolve()
    try:
        profile_path.relative_to(source)
    except ValueError as error:
        raise ValueError("R1_CURATOR_PROFILE_PATH") from error
    profiles = _read_json(profile_path)
    if profiles.get("provenance_namespace") != PROVENANCE_NAMESPACE:
        raise ValueError("R1_CURATOR_PROFILE_NAMESPACE")
    freeze = profiles.get("freeze")
    if not isinstance(freeze, Mapping):
        raise ValueError("R1_CURATOR_FREEZE_CONTRACT")
    freeze_path = (profile_path.parent / str(freeze.get("path") or "")).resolve()
    try:
        freeze_path.relative_to(source)
    except ValueError as error:
        raise ValueError("R1_CURATOR_FREEZE_PATH") from error
    if (
        not freeze_path.is_file()
        or str(freeze.get("sha256") or "")
        != "sha256:" + hashlib.sha256(freeze_path.read_bytes()).hexdigest()
    ):
        raise ValueError("R1_CURATOR_FREEZE_HASH")
    profile_cases = {
        str(item.get("case_id")): item
        for item in profiles.get("cases", ())
        if isinstance(item, Mapping)
    }
    expected_ids = [str(value) for value in profiles.get("execution_order", ())]
    collection_cases = manifest.get("cases")
    if not isinstance(collection_cases, list):
        raise ValueError("R1_CURATOR_CASES")
    actual_ids = [str(item.get("case_id")) for item in collection_cases]
    if actual_ids != expected_ids or set(profile_cases) != set(expected_ids):
        raise ValueError("R1_CURATOR_PROFILE_CASE_SET")
    for item in collection_cases:
        case_id = str(item.get("case_id"))
        if item.get("terminal_class") != profile_cases[case_id].get("terminal_class"):
            raise ValueError(f"R1_CURATOR_TERMINAL_CLASS:{case_id}")

    document = (
        dict(validation_document)
        if validation_document is not None
        else validate_r1_proof_collection(source).to_dict()
    )
    validate_proof_validation_document_v03(document)
    if document.get("status") != "passed" or document.get("errors"):
        raise ValueError("R1_CURATOR_VALIDATION_FAILED")
    validated_cases = document.get("cases")
    if not isinstance(validated_cases, list):
        raise ValueError("R1_CURATOR_VALIDATION_CASES")
    validated_by_id = {
        str(item.get("case_id")): item
        for item in validated_cases
        if isinstance(item, Mapping)
    }
    if list(validated_by_id) != expected_ids:
        raise ValueError("R1_CURATOR_VALIDATED_CASE_SET")
    for case_id in expected_ids:
        validated = validated_by_id[case_id]
        if (
            validated.get("provenance_namespace") != PROVENANCE_NAMESPACE
            or validated.get("terminal_class")
            != profile_cases[case_id].get("terminal_class")
            or validated.get("status") != "passed"
        ):
            raise ValueError(f"R1_CURATOR_VALIDATED_CONTRACT:{case_id}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}-stage-", dir=destination.parent)
    )
    try:
        shutil.copytree(source, stage, dirs_exist_ok=True)
        curation = {
            "schema_version": "text2ifc/repair-milestone-r1-proof-curation/0.1",
            "status": "curated",
            "provenance_namespace": PROVENANCE_NAMESPACE,
            "case_ids": expected_ids,
            "proof_validation_schema": document["schema_version"],
            "profile_schema": profiles["schema_version"],
        }
        _write_json(stage / "CURATION.json", curation)
        stage.replace(destination)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return curation


def main() -> int:
    parser = argparse.ArgumentParser(description="Curate frozen R1 Proof evidence.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--destination-root", type=Path, required=True)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    result = curate_r1_proof(
        source_root=args.source_root,
        destination_root=args.destination_root,
    )
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']} cases={len(result['case_ids'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
