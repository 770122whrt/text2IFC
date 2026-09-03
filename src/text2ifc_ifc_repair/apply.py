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
from .changesets import validate_changeset
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

    prepared_model = None
    prepared_fingerprint = None
    if not validate_changeset(changeset):
        prepared_fingerprint = "sha256:" + _sha256(damaged)
        prepared_model = ifcopenshell.open(str(damaged))
    audit = audit_changeset(
        damaged_ifc_path=damaged,
        repair_request=repair_request,
        changeset=changeset,
        registry=registry,
        prepared_model=prepared_model,
        prepared_fingerprint=prepared_fingerprint,
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

    actual_fingerprint = (
        prepared_fingerprint or "sha256:" + _sha256(damaged)
    )
    if actual_fingerprint != changeset["base_model_fingerprint"]:
        return _failure(
            "BASE_MODEL_FINGERPRINT_MISMATCH",
            "/base_model_fingerprint",
            actual_fingerprint,
            audit=audit,
        )

    model = (
        prepared_model
        if prepared_model is not None
        else ifcopenshell.open(str(damaged))
    )
    operation_results: list[dict[str, Any]] = []
    for operation in changeset["operations"]:
        try:
            changes = registry.dispatch(
                "applicator", operation, model=model
            )
            if operation.get("semantic_assignments") is not None:
                definition = registry.require(str(operation["operation_type"]))
                handler_owned_facts = frozenset(
                    str(item)
                    for item in definition.capability_constraints.get(
                        "handler_owned_semantic_facts", ()
                    )
                )
                scope_roles = {
                    scope: role
                    for role, scope in definition.semantic_scope_roles.items()
                }
                if not scope_roles:
                    policy = registry.require_evaluation_policy(
                        str(operation["operation_type"])
                    )
                    scope_roles = {
                        "window_occurrence": policy.semantic_role,
                        "opening_occurrence": "opening",
                    }
                explicit_assignment_scopes = {
                    str(item["scope"])
                    for item in operation["semantic_assignments"]
                    if item.get("scope") is not None
                }
                legacy_scope = (
                    next(iter(scope_roles))
                    if not explicit_assignment_scopes
                    and len(scope_roles) == 1
                    else "window_occurrence"
                )
                assignment_scopes = explicit_assignment_scopes or {
                    legacy_scope
                }
                unknown_scopes = assignment_scopes - set(scope_roles)
                if unknown_scopes:
                    raise ValueError(
                        "SEMANTIC_SCOPE_UNDECLARED:"
                        + ",".join(sorted(unknown_scopes))
                    )
                scoped_semantics = []
                for scope, target_role in scope_roles.items():
                    scoped_assignments = [
                        item
                        for item in operation["semantic_assignments"]
                        if item.get("scope", legacy_scope) == scope
                        and str(item.get("fact_key")) not in handler_owned_facts
                    ]
                    if not scoped_assignments:
                        continue
                    scoped_operation = {
                        **operation,
                        "semantic_assignments": scoped_assignments,
                    }
                    scoped_semantics.append(
                        (
                            scope,
                            apply_semantic_assignments(
                                model=model,
                                operation=scoped_operation,
                                application=changes,
                                target_role=target_role,
                            ),
                        )
                    )
                semantic = {
                    "created": [
                        item
                        for _, result in scoped_semantics
                        for item in result["created"]
                    ],
                    "modified": [
                        item
                        for _, result in scoped_semantics
                        for item in result.get("modified", ())
                    ],
                    "updated": [
                        item
                        for _, result in scoped_semantics
                        for item in result.get("updated", ())
                    ],
                    "skipped": [
                        item
                        for _, result in scoped_semantics
                        for item in result.get("skipped", ())
                    ],
                    "scopes": {
                        scope: result for scope, result in scoped_semantics
                    },
                }
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
