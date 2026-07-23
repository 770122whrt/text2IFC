"""Transactional incremental application of audited IFC repair ChangeSets."""

from __future__ import annotations

import hashlib
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import ifcopenshell

from .audit import audit_changeset
from .registry import OperationRegistry
from .semantic_authoring import apply_semantic_assignments


APPLICATION_SCHEMA_VERSION = "text2ifc/ifc-repair-application/0.1"


def apply_changeset(
    *,
    damaged_ifc_path: Path | str,
    repair_request: str,
    changeset: Mapping[str, Any],
    output_path: Path | str,
    registry: OperationRegistry,
) -> dict[str, Any]:
    """Apply all operations in memory and publish only a verified IFC artifact."""

    damaged = Path(damaged_ifc_path).resolve()
    output = Path(output_path).resolve()
    if damaged == output:
        return _failure("INPUT_OVERWRITE_FORBIDDEN", "/output_path", str(output))
    if output.exists():
        return _failure("OUTPUT_ALREADY_EXISTS", "/output_path", str(output))

    audit = audit_changeset(
        damaged_ifc_path=damaged,
        repair_request=repair_request,
        changeset=changeset,
        registry=registry,
    )
    if not audit["valid"]:
        return {
            "schema_version": APPLICATION_SCHEMA_VERSION,
            "valid": False,
            "published": False,
            "audit": audit,
            "operations": [],
            "postconditions": [],
            "output": None,
            "issues": audit["issues"],
        }

    actual_fingerprint = "sha256:" + _sha256(damaged)
    if actual_fingerprint != changeset["base_model_fingerprint"]:
        return _failure(
            "BASE_MODEL_FINGERPRINT_MISMATCH",
            "/base_model_fingerprint",
            actual_fingerprint,
            audit=audit,
        )

    model = ifcopenshell.open(str(damaged))
    operation_results: list[dict[str, Any]] = []
    for operation in changeset["operations"]:
        try:
            changes = registry.dispatch(
                "applicator", operation, model=model
            )
            if operation.get("semantic_assignments") is not None:
                policy = registry.require_evaluation_policy(
                    str(operation["operation_type"])
                )
                semantic = apply_semantic_assignments(
                    model=model,
                    operation=operation,
                    application=changes,
                    target_role=policy.semantic_role,
                )
                changes["created"] = [
                    *changes.get("created", ()),
                    *semantic["created"],
                ]
                changes["modified"] = [
                    *changes.get("modified", ()),
                    *semantic.get("modified", ()),
                ]
                changes["semantic"] = semantic
        except Exception as error:  # operation boundary becomes structured evidence
            return _failure(
                "OPERATION_APPLICATION_FAILED",
                f"/operations/{len(operation_results)}",
                f"{type(error).__name__}: {error}",
                audit=audit,
                operations=operation_results,
            )
        operation_results.append(
            {
                "operation_id": operation["operation_id"],
                "operation_type": operation["operation_type"],
                "changes": changes,
            }
        )

    postcondition_results: list[dict[str, Any]] = []
    postcondition_issues: list[dict[str, str]] = []
    for index, (operation, application) in enumerate(
        zip(changeset["operations"], operation_results, strict=True)
    ):
        try:
            postcondition = registry.dispatch(
                "postcondition_checker",
                operation,
                model=model,
                application=application["changes"],
            )
        except Exception as error:
            return _failure(
                "OPERATION_POSTCONDITION_FAILED",
                f"/operations/{index}",
                f"{type(error).__name__}: {error}",
                audit=audit,
                operations=operation_results,
                postconditions=postcondition_results,
            )
        postcondition_results.append(
            {
                "operation_id": operation["operation_id"],
                **postcondition,
            }
        )
        postcondition_issues.extend(
            {
                **issue,
                "path": f"/operations/{index}" + issue.get("path", ""),
            }
            for issue in postcondition.get("issues", [])
        )
        if not postcondition.get("valid", False) and not postcondition.get("issues"):
            postcondition_issues.append(
                {
                    "code": "OPERATION_POSTCONDITION_FAILED",
                    "path": f"/operations/{index}",
                    "message": "Operation postcondition reported invalid without diagnostics.",
                }
            )
    if postcondition_issues:
        return _failure_many(
            postcondition_issues,
            audit=audit,
            operations=operation_results,
            postconditions=postcondition_results,
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{output.name}-",
        suffix=".tmp",
        dir=output.parent,
        delete=False,
    )
    temporary = Path(handle.name)
    handle.close()
    try:
        model.write(str(temporary))
        reopened = ifcopenshell.open(str(temporary))
        if reopened.schema != "IFC2X3":
            return _failure(
                "PUBLISHED_IFC_SCHEMA_MISMATCH",
                "/output",
                reopened.schema,
                audit=audit,
                operations=operation_results,
                postconditions=postcondition_results,
            )
        output_sha256 = _sha256(temporary)
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()

    return {
        "schema_version": APPLICATION_SCHEMA_VERSION,
        "valid": True,
        "published": True,
        "audit": audit,
        "operations": operation_results,
        "postconditions": postcondition_results,
        "output": {"path": str(output), "sha256": output_sha256},
        "issues": [],
    }


def _failure(
    code: str,
    path: str,
    message: str,
    *,
    audit: Mapping[str, Any] | None = None,
    operations: list[dict[str, Any]] | None = None,
    postconditions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return _failure_many(
        [{"code": code, "path": path, "message": message}],
        audit=audit,
        operations=operations,
        postconditions=postconditions,
    )


def _failure_many(
    issues: list[dict[str, str]],
    *,
    audit: Mapping[str, Any] | None = None,
    operations: list[dict[str, Any]] | None = None,
    postconditions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": APPLICATION_SCHEMA_VERSION,
        "valid": False,
        "published": False,
        "audit": audit,
        "operations": operations or [],
        "postconditions": postconditions or [],
        "output": None,
        "issues": sorted(
            issues, key=lambda issue: (issue["code"], issue["path"], issue["message"])
        ),
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
