"""Validate the human-facing surface of an IFC repair Proof collection.

This is intentionally not a curator. It checks only presentation failures that
can make an accepted case misleading or unusable to a reviewer.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import ifcopenshell


COLLECTION_SCHEMA = "text2ifc/human-proof-collection/0.1"
VALIDATION_SCHEMA = "text2ifc/human-proof-layout-validation/0.1"


def validate_human_proof_collection(root: Path | str) -> dict[str, Any]:
    collection_root = Path(root).resolve()
    errors: list[str] = []
    manifest_path = collection_root / "manifest.json"
    manifest = _read_json(manifest_path, errors)

    if manifest.get("schema_version") != COLLECTION_SCHEMA:
        errors.append(f"manifest schema_version must be {COLLECTION_SCHEMA}")

    for relative in ("README.md", "REPORT.md"):
        _required_file(collection_root, relative, errors)

    cases = manifest.get("cases")
    if not isinstance(cases, list):
        errors.append("manifest cases must be an array")
        cases = []

    seen: set[str] = set()
    repaired_case_count = 0
    no_output_case_count = 0
    ifc_reopen_count = 0
    for case in cases:
        if not isinstance(case, dict):
            errors.append("each case must be an object")
            continue
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            errors.append("each case requires a non-empty case_id")
            continue
        if case_id in seen:
            errors.append(f"duplicate case_id: {case_id}")
            continue
        seen.add(case_id)

        _required_path(
            collection_root, case.get("authority_path"), errors, case_id, "authority_path"
        )
        for role in ("report", "request", "damaged_ifc"):
            path = _required_file(collection_root, case.get(role), errors, case_id)
            if role == "damaged_ifc" and path is not None:
                ifc_reopen_count += _reopen_ifc(path, role, case_id, errors)

        original = case.get("original_ifc")
        if original is not None:
            original_role = case.get("original_role")
            if original_role not in {
                "private_ground_truth",
                "physical_fixture_non_private_audit",
            }:
                errors.append(
                    f"{case_id}: original_ifc requires an explicit original_role"
                )
            path = _required_file(collection_root, original, errors, case_id)
            if path is not None:
                ifc_reopen_count += _reopen_ifc(path, "original_ifc", case_id, errors)

        outcome = case.get("outcome")
        if outcome == "repaired":
            repaired_case_count += 1
            path = _required_file(
                collection_root, case.get("repaired_ifc"), errors, case_id
            )
            if path is not None:
                ifc_reopen_count += _reopen_ifc(
                    path, "repaired_ifc", case_id, errors
                )
        elif outcome == "no_output":
            no_output_case_count += 1
            conventional_repaired = (
                collection_root / "accepted-cases" / case_id / "repaired.ifc"
            )
            if case.get("repaired_ifc") is not None or conventional_repaired.exists():
                errors.append(
                    f"{case_id}: no-output case must not expose repaired.ifc"
                )
            _required_file(
                collection_root, case.get("no_repair_report"), errors, case_id
            )
        else:
            errors.append(f"{case_id}: outcome must be repaired or no_output")

    return {
        "schema_version": VALIDATION_SCHEMA,
        "status": "passed" if not errors else "failed",
        "collection_id": manifest.get("collection_id"),
        "case_count": len(cases),
        "repaired_case_count": repaired_case_count,
        "no_output_case_count": no_output_case_count,
        "ifc_reopen_count": ifc_reopen_count,
        "errors": errors,
    }


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read {path.name}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.name} must contain an object")
        return {}
    return value


def _required_path(
    root: Path,
    relative: object,
    errors: list[str],
    case_id: str,
    role: str,
) -> Path | None:
    if not isinstance(relative, str) or not relative:
        errors.append(f"{case_id}: {role} is missing")
        return None
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        errors.append(f"{case_id}: {role} escapes collection root: {relative}")
        return None
    if not path.exists():
        errors.append(f"{case_id}: {role} does not exist: {relative}")
        return None
    return path


def _required_file(
    root: Path,
    relative: object,
    errors: list[str],
    case_id: str | None = None,
) -> Path | None:
    prefix = f"{case_id}: " if case_id else ""
    if not isinstance(relative, str) or not relative:
        errors.append(f"{prefix}required path is missing")
        return None
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        errors.append(f"{prefix}path escapes collection root: {relative}")
        return None
    if not path.is_file() or path.stat().st_size == 0:
        errors.append(f"{prefix}required file missing or empty: {relative}")
        return None
    return path


def _reopen_ifc(
    path: Path,
    role: str,
    case_id: str,
    errors: list[str],
) -> int:
    try:
        model = ifcopenshell.open(path)
        if not model.schema:
            raise ValueError("schema is unavailable")
    except Exception as exc:  # IfcOpenShell raises multiple parser exceptions.
        errors.append(f"{case_id}: cannot reopen {role}: {exc}")
        return 0
    return 1


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a human-readable IFC repair Proof layout."
    )
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    result = validate_human_proof_collection(args.root)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"status={result['status']} cases={result['case_count']} "
            f"ifc_reopened={result['ifc_reopen_count']}"
        )
        for error in result["errors"]:
            print(f"ERROR {error}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
