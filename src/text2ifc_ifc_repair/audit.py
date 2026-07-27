"""Common structured audit dispatcher for IFC repair ChangeSets."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import ifcopenshell

from .changesets import validate_changeset
from .registry import OperationRegistry, OperationRegistryError


AUDIT_SCHEMA_VERSION = "text2ifc/ifc-repair-audit/0.1"


def audit_changeset(
    *,
    damaged_ifc_path: Path | str,
    repair_request: str,
    changeset: Mapping[str, Any],
    registry: OperationRegistry,
) -> dict[str, Any]:
    """Audit common bindings and dispatch operation-specific preconditions."""

    checks: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    operation_audits: list[dict[str, Any]] = []
    contract_issues = validate_changeset(changeset)
    if contract_issues:
        issues.extend(
            {"code": issue.code, "path": issue.path, "message": issue.message}
            for issue in contract_issues
        )
        checks.append(
            {
                "code": "CHANGESET_SCHEMA",
                "status": "failed",
                "evidence": {"issue_count": len(contract_issues)},
            }
        )
        return _audit_result(checks, issues, operation_audits)
    checks.append(
        {"code": "CHANGESET_SCHEMA", "status": "passed", "evidence": {}}
    )

    damaged = Path(damaged_ifc_path)
    model = ifcopenshell.open(str(damaged))
    _check(
        checks,
        issues,
        code="IFC_SCHEMA",
        passed=model.schema == "IFC2X3",
        failure_code="UNSUPPORTED_IFC_SCHEMA",
        path="/base_model_fingerprint",
        evidence={"actual_schema": model.schema},
    )
    actual_fingerprint = "sha256:" + hashlib.sha256(damaged.read_bytes()).hexdigest()
    _check(
        checks,
        issues,
        code="BASE_MODEL_FINGERPRINT",
        passed=changeset["base_model_fingerprint"] == actual_fingerprint,
        failure_code="BASE_MODEL_FINGERPRINT_MISMATCH",
        path="/base_model_fingerprint",
        evidence={"actual_fingerprint": actual_fingerprint},
    )
    actual_request_hash = "sha256:" + hashlib.sha256(
        repair_request.encode("utf-8")
    ).hexdigest()
    _check(
        checks,
        issues,
        code="SOURCE_REQUEST_HASH",
        passed=changeset["source_request_hash"] == actual_request_hash,
        failure_code="SOURCE_REQUEST_HASH_MISMATCH",
        path="/source_request_hash",
        evidence={"actual_request_hash": actual_request_hash},
    )

    seen_targets: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    seen_conflict_domains: dict[
        tuple[str, str], list[Mapping[str, Any]]
    ] = {}
    for index, operation in enumerate(changeset["operations"]):
        operation_path = f"/operations/{index}"
        try:
            definition = registry.require(str(operation["operation_type"]))
        except OperationRegistryError as error:
            issues.append(
                {
                    "code": error.code,
                    "path": f"{operation_path}/operation_type",
                    "message": error.detail,
                }
            )
            checks.append(
                {
                    "code": "OPERATION_REGISTRATION",
                    "status": "failed",
                    "evidence": {"operation_type": operation["operation_type"]},
                }
            )
            continue
        checks.append(
            {
                "code": "OPERATION_REGISTRATION",
                "status": "passed",
                "evidence": {"operation_type": definition.operation_type},
            }
        )
        operation_contract_issues = [
            *registry.validate_target(operation),
            *registry.validate_parameters(operation),
        ]
        if operation_contract_issues:
            issues.extend(
                {
                    "code": issue.code,
                    "path": operation_path + issue.path,
                    "message": issue.message,
                }
                for issue in operation_contract_issues
            )
            continue

        target_ids = [
            str(value)
            for key, value in operation["target"].items()
            if key.endswith("_global_id")
        ]
        if len(target_ids) != 1:
            issues.append(
                {
                    "code": "INVALID_OPERATION_TARGET",
                    "path": f"{operation_path}/target",
                    "message": "Operation must declare exactly one IFC GlobalId target.",
                }
            )
            continue
        target_id = target_ids[0]
        operation_key = (definition.operation_type, target_id)
        domain_host_id = str(
            operation["target"].get("wall_global_id")
            or operation.get("parameters", {}).get("host_wall_global_id")
            or target_id
        )
        domain_key = (
            str(definition.conflict_domain),
            domain_host_id,
        )
        previous_operations = (
            seen_conflict_domains.get(domain_key, [])
            if definition.conflict_domain is not None
            else seen_targets.get(operation_key, [])
        )
        conflict_issues = []
        if previous_operations and definition.operation_conflict_checker is None:
            conflict_issues.append(
                {
                    "code": "DUPLICATE_TARGET_OPERATION",
                    "path": f"{operation_path}/target",
                    "message": f"Duplicate {definition.operation_type} for {target_id}.",
                }
            )
        elif previous_operations:
            for previous in previous_operations:
                conflict_issues.extend(
                    {
                        **issue,
                        "path": operation_path + str(issue["path"]),
                    }
                    for issue in definition.operation_conflict_checker(
                        previous,
                        operation,
                    )
                )
        if conflict_issues:
            issues.extend(conflict_issues)
            continue
        seen_targets.setdefault(operation_key, []).append(operation)
        if definition.conflict_domain is not None:
            seen_conflict_domains.setdefault(domain_key, []).append(operation)
        common_operation_issues = _target_issues(
            model=model,
            target_id=target_id,
            target_ifc_classes=definition.target_ifc_classes,
            scope=changeset["scope"],
            path=f"{operation_path}/target",
        )
        if common_operation_issues:
            issues.extend(common_operation_issues)
            continue

        result = registry.dispatch(
            "precondition_checker", operation, model=model
        )
        prefixed_issues = [
            {
                **issue,
                "path": operation_path + issue["path"],
            }
            for issue in result["issues"]
        ]
        issues.extend(prefixed_issues)
        operation_audits.append(
            {
                "operation_id": operation["operation_id"],
                "operation_type": operation["operation_type"],
                "valid": not prefixed_issues,
                "checks": result["checks"],
                "evidence": result["evidence"],
            }
        )
    return _audit_result(checks, issues, operation_audits)


def _target_issues(
    *,
    model: Any,
    target_id: str,
    target_ifc_classes: tuple[str, ...],
    scope: Mapping[str, Any],
    path: str,
) -> list[dict[str, str]]:
    if target_id not in scope["target_ids"]:
        return [{"code": "TARGET_OUTSIDE_SCOPE", "path": path, "message": target_id}]
    if target_id in scope["forbidden_ids"]:
        return [{"code": "FORBIDDEN_TARGET", "path": path, "message": target_id}]
    try:
        target = model.by_guid(target_id)
    except RuntimeError:
        target = None
    if target is None:
        return [{"code": "TARGET_NOT_FOUND", "path": path, "message": target_id}]
    if not any(target.is_a(ifc_class) for ifc_class in target_ifc_classes):
        return [
            {
                "code": "TARGET_CLASS_NOT_ALLOWED",
                "path": path,
                "message": f"{target.is_a()} is not allowed.",
            }
        ]
    return []


def _check(
    checks: list[dict[str, Any]],
    issues: list[dict[str, str]],
    *,
    code: str,
    passed: bool,
    failure_code: str,
    path: str,
    evidence: Mapping[str, Any],
) -> None:
    checks.append(
        {"code": code, "status": "passed" if passed else "failed", "evidence": dict(evidence)}
    )
    if not passed:
        issues.append(
            {"code": failure_code, "path": path, "message": failure_code}
        )


def _audit_result(
    checks: list[dict[str, Any]],
    issues: list[dict[str, str]],
    operation_audits: list[dict[str, Any]],
) -> dict[str, Any]:
    sorted_issues = sorted(
        issues, key=lambda issue: (issue["code"], issue["path"], issue["message"])
    )
    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "valid": not sorted_issues,
        "checks": checks,
        "operation_audits": operation_audits,
        "issues": sorted_issues,
    }
