"""Validate the checked-in IFC repair success-case collection.

The command is intentionally independent from the production evaluator. It
checks that frozen proof artifacts still agree with their manifests and can be
used as a release/checkpoint gate before adding another operation family.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

import ifcopenshell

from text2ifc_ifc_repair.prompt_profiles import load_prompt_profiles


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COLLECTION = (
    ROOT / "dataset" / "processed" / "proof" / "ifc-repair-success-cases"
)
MANDATORY_LEVELS = ("L1", "L2")
BOUND_CHANGESET_ROLES = ("bound_changeset", "bound_changeset_replayed")
PRODUCTION_EVALUATION_ROLES = (
    "production_publication_evidence",
    "production_evaluation",
)


@dataclass
class ProofValidationResult:
    status: str
    collection_root: str
    case_count: int = 0
    operation_count: int = 0
    checked_file_count: int = 0
    reopened_ifc_count: int = 0
    errors: list[str] = field(default_factory=list)
    cases: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "text2ifc/ifc-repair-proof-validation/0.1",
            "status": self.status,
            "collection_root": self.collection_root,
            "case_count": self.case_count,
            "operation_count": self.operation_count,
            "checked_file_count": self.checked_file_count,
            "reopened_ifc_count": self.reopened_ifc_count,
            "errors": self.errors,
            "cases": self.cases,
        }


def validate_success_case_collection(
    collection_root: Path | str = DEFAULT_COLLECTION,
) -> ProofValidationResult:
    root = Path(collection_root).resolve()
    result = ProofValidationResult(status="failed", collection_root=root.as_posix())
    try:
        collection = _read_json(root / "manifest.json")
        cases = collection.get("cases")
        if not isinstance(cases, list):
            raise ValueError("collection manifest cases must be a list")
        if int(collection.get("case_count", -1)) != len(cases):
            raise ValueError("collection case_count does not match cases")
        case_ids = [str(item.get("case_id")) for item in cases]
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("collection case_id values must be unique")
        result.case_count = len(cases)
        for case in cases:
            try:
                summary = _validate_case(root, case)
                result.cases.append(summary)
                result.operation_count += summary["operation_count"]
                result.checked_file_count += summary["checked_file_count"]
                result.reopened_ifc_count += summary["reopened_ifc_count"]
            except Exception as error:
                case_id = str(case.get("case_id", "<unknown>"))
                result.errors.append(f"{case_id}: {error}")
    except Exception as error:
        result.errors.append(f"collection: {error}")
    result.status = "passed" if not result.errors else "failed"
    return result


def _validate_case(root: Path, case: Mapping[str, Any]) -> dict[str, Any]:
    case_id = str(case["case_id"])
    if case.get("status") != "accepted":
        raise ValueError("case status must be accepted")
    operation_count = int(case["operation_count"])
    if operation_count < 1:
        raise ValueError("operation_count must be positive")

    report_path = _safe_path(root, str(case["report"]))
    files_path = _safe_path(root, str(case["files"]))
    if not report_path.is_file():
        raise FileNotFoundError(f"missing report: {report_path}")
    files_manifest = _read_json(files_path)
    if files_manifest.get("case_id") != case_id:
        raise ValueError("FILES.json case_id mismatch")
    case_root = files_path.parent

    entries = files_manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("FILES.json files must be a non-empty list")
    listed_paths: set[str] = set()
    roles: dict[str, Path] = {}
    checked_file_count = 0
    for entry in entries:
        relative = str(entry["path"])
        if relative in listed_paths:
            raise ValueError(f"duplicate FILES.json path: {relative}")
        listed_paths.add(relative)
        artifact = _safe_path(case_root, relative)
        if not artifact.is_file():
            raise FileNotFoundError(f"missing artifact: {relative}")
        expected_size = int(entry["size_bytes"])
        actual_size = artifact.stat().st_size
        if actual_size != expected_size:
            raise ValueError(
                f"size mismatch for {relative}: {actual_size} != {expected_size}"
            )
        expected_hash = _normalize_sha256(str(entry["sha256"]))
        actual_hash = _sha256(artifact)
        if actual_hash != expected_hash:
            raise ValueError(f"SHA-256 mismatch for {relative}")
        role = str(entry["role"])
        if role in roles:
            raise ValueError(f"duplicate artifact role: {role}")
        roles[role] = artifact
        checked_file_count += 1

    actual_paths = {
        path.relative_to(case_root).as_posix()
        for path in case_root.rglob("*")
        if path.is_file()
    }
    expected_paths = listed_paths | {"FILES.json", "REPORT.md"}
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        unindexed = sorted(actual_paths - expected_paths)
        raise ValueError(
            f"FILES.json coverage mismatch; missing={missing}, unindexed={unindexed}"
        )

    required_role_paths = {
        "original_ground_truth": _safe_path(root, str(case["original_ifc"])),
        "repair_input_ifc": _safe_path(root, str(case["damaged_ifc"])),
        "published_repair_output": _safe_path(root, str(case["repaired_ifc"])),
    }
    reopened_ifc_count = 0
    for role, manifest_path in required_role_paths.items():
        artifact = roles.get(role)
        if artifact is None or artifact != manifest_path:
            raise ValueError(f"{role} path does not match collection manifest")
        model = ifcopenshell.open(str(artifact))
        if model.schema != "IFC2X3":
            raise ValueError(f"{role} schema is {model.schema}, expected IFC2X3")
        reopened_ifc_count += 1

    damaged_hash = _sha256(required_role_paths["repair_input_ifc"])
    changeset_path = _path_for_any_role(roles, BOUND_CHANGESET_ROLES)
    changeset = _read_json(changeset_path)
    if _normalize_sha256(str(changeset["base_model_fingerprint"])) != damaged_hash:
        raise ValueError("Bound ChangeSet base_model_fingerprint mismatch")
    expected_operation_types = {
        str(item)
        for item in case.get(
            "operation_types", (case.get("operation_type"),)
        )
        if item is not None
    }
    if not expected_operation_types:
        raise ValueError("case operation types must be non-empty")
    _check_operations(
        changeset.get("operations"),
        operation_count=operation_count,
        operation_types=expected_operation_types,
        source="Bound ChangeSet",
    )

    intent_path = roles.get("stage1_repair_intent")
    if intent_path is not None:
        intent = _read_json(intent_path)
        _check_operations(
            intent.get("operations"),
            operation_count=operation_count,
            operation_types=expected_operation_types,
            source="RepairIntent",
        )
    elif case.get("provider_evidence_mode") == "offline_bound_deterministic":
        _check_prompt_profile_evidence(
            roles,
            changeset=changeset,
            operation_count=operation_count,
        )
    else:
        raise ValueError("missing stage1_repair_intent")

    application_path = roles.get("application_result")
    if application_path is not None:
        application = _read_json(application_path)
        if (
            application.get("valid") is not True
            or application.get("published") is not True
            or len(application.get("operations", ())) != operation_count
        ):
            raise ValueError("application_result is not a complete publication")
    source_manifest_path = roles.get("source_run_manifest")
    if source_manifest_path is not None:
        source_manifest = _read_json(source_manifest_path)
        if source_manifest.get("synthetic_fallback_used") is not False:
            raise ValueError("source run used synthetic fallback")
        if source_manifest.get("public_targeting", {}).get("guid_free") is True:
            _check_guid_free_targeting(
                roles,
                operation_count=operation_count,
                operation_types=expected_operation_types,
            )
    injected_failure_path = roles.get("injected_failure_application")
    if injected_failure_path is not None:
        injected = _read_json(injected_failure_path)
        if (
            injected.get("valid") is not False
            or injected.get("published") is not False
        ):
            raise ValueError("injected failure did not fail closed")

    production_path = _path_for_any_role(roles, PRODUCTION_EVALUATION_ROLES)
    production = _read_json(production_path)
    _check_success_evaluation(production, operation_count=operation_count)
    private_path = roles.get("private_ground_truth_evaluation")
    if private_path is not None:
        _check_success_evaluation(
            _read_json(private_path),
            operation_count=operation_count,
        )

    return {
        "case_id": case_id,
        "status": "passed",
        "operation_count": operation_count,
        "checked_file_count": checked_file_count,
        "reopened_ifc_count": reopened_ifc_count,
        "damaged_sha256": f"sha256:{damaged_hash}",
        "changeset_schema_version": changeset.get("schema_version"),
    }


def _check_operations(
    operations: Any,
    *,
    operation_count: int,
    operation_types: set[str],
    source: str,
) -> None:
    if not isinstance(operations, list) or len(operations) != operation_count:
        raise ValueError(f"{source} operation count mismatch")
    actual_types = {str(item.get("operation_type")) for item in operations}
    if actual_types != operation_types:
        raise ValueError(f"{source} operation_type mismatch: {sorted(actual_types)}")


def _check_prompt_profile_evidence(
    roles: Mapping[str, Path],
    *,
    changeset: Mapping[str, Any],
    operation_count: int,
) -> None:
    path = roles.get("prompt_profile_evidence")
    if path is None:
        raise ValueError("missing prompt_profile_evidence")
    evidence = _read_json(path)
    if evidence.get("schema_version") != (
        "text2ifc/phase11-prompt-routing-proof/0.1"
    ):
        raise ValueError("prompt profile evidence schema mismatch")
    bindings = evidence.get("operation_bindings")
    if not isinstance(bindings, list) or len(bindings) != operation_count:
        raise ValueError("prompt profile operation binding count mismatch")
    operations = {
        str(item["operation_id"]): str(item["operation_type"])
        for item in changeset["operations"]
    }
    profiles = load_prompt_profiles()
    for binding in bindings:
        operation_id = str(binding["operation_id"])
        operation_type = str(binding["operation_type"])
        profile_id = str(binding["profile_id"])
        if operations.get(operation_id) != operation_type:
            raise ValueError("prompt profile operation binding mismatch")
        profile = profiles.get(profile_id)
        if profile is None or profile.operation_type != operation_type:
            raise ValueError("prompt profile registry binding mismatch")
        if profile.profile_hash != str(binding["profile_hash"]):
            raise ValueError("prompt profile hash mismatch")
    selected = evidence.get("selected")
    if not isinstance(selected, Mapping):
        raise ValueError("prompt profile selected evidence missing")
    if set(selected.get("profile_ids", ())) != {
        str(item["profile_id"]) for item in bindings
    }:
        raise ValueError("selected prompt profile set mismatch")


def _check_guid_free_targeting(
    roles: Mapping[str, Path],
    *,
    operation_count: int,
    operation_types: set[str],
) -> None:
    request_path = roles.get("user_request")
    intent_path = roles.get("guid_free_repair_intent")
    resolution_path = roles.get("deterministic_target_resolution")
    if request_path is None or intent_path is None or resolution_path is None:
        raise ValueError("GUID-free targeting evidence is incomplete")
    request = request_path.read_text(encoding="utf-8")
    if re.search(
        r"(?<![0-9A-Za-z_$])[0-3][0-9A-Za-z_$]{21}(?![0-9A-Za-z_$])",
        request,
    ):
        raise ValueError("public request contains an IFC GlobalId")
    intent = _read_json(intent_path)
    _check_operations(
        intent.get("operations"),
        operation_count=operation_count,
        operation_types=operation_types,
        source="GUID-free RepairIntent",
    )
    for operation in intent["operations"]:
        query = operation.get("target_query", {})
        if any(
            query.get(field) is not None
            for field in ("global_id", "storey_global_id", "host_global_id")
        ):
            raise ValueError("public target_query contains an IFC GlobalId")
        if not query.get("names") or not query.get("storey_name"):
            raise ValueError("public target_query lacks name/storey selectors")
    resolution = _read_json(resolution_path)
    if resolution.get("status") != "resolved":
        raise ValueError("deterministic target resolution did not resolve")
    operations = resolution.get("operations")
    if not isinstance(operations, list) or len(operations) != operation_count:
        raise ValueError("target resolution operation count mismatch")
    if any(not item.get("target_global_id") for item in operations):
        raise ValueError("target resolution lacks an internal binding")


def _check_success_evaluation(
    evaluation: Mapping[str, Any],
    *,
    operation_count: int,
) -> None:
    if evaluation.get("status") != "passed":
        raise ValueError("production evaluation status is not passed")
    if evaluation.get("complete_repair_success") is not True:
        raise ValueError("complete_repair_success is not true")
    if evaluation.get("successful_artifact_publishable") is not True:
        raise ValueError("successful_artifact_publishable is not true")
    for section in ("application", "preservation"):
        payload = evaluation.get(section)
        if not isinstance(payload, Mapping) or payload.get("status") != "passed":
            raise ValueError(f"evaluation {section} gate is not passed")
    operations = evaluation.get("operations")
    if not isinstance(operations, list) or len(operations) != operation_count:
        raise ValueError("evaluation operation count mismatch")
    for operation in operations:
        levels = {
            str(item.get("level")): str(item.get("status"))
            for item in operation.get("levels", ())
        }
        for level in MANDATORY_LEVELS:
            if levels.get(level) != "passed":
                raise ValueError(
                    f"{operation.get('operation_id')} {level} is not passed"
                )


def _path_for_any_role(roles: Mapping[str, Path], candidates: Iterable[str]) -> Path:
    matches = [roles[role] for role in candidates if role in roles]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one artifact role from {tuple(candidates)}")
    return matches[0]


def _safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"path escapes proof root: {relative}") from error
    return path


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _normalize_sha256(value: str) -> str:
    normalized = value.removeprefix("sha256:").lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"invalid SHA-256 value: {value}")
    return normalized


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate frozen IFC repair proof cases."
    )
    parser.add_argument(
        "--collection-root",
        type=Path,
        default=DEFAULT_COLLECTION,
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    result = validate_success_case_collection(args.collection_root)
    if args.as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(
            f"status={result.status} cases={result.case_count} "
            f"operations={result.operation_count} "
            f"files={result.checked_file_count} "
            f"ifc_reopened={result.reopened_ifc_count}"
        )
        for error in result.errors:
            print(f"ERROR {error}")
    return 0 if result.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
