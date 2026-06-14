"""Supported-scope projection for Phase 3 formal Text-to-JSON targets."""

from __future__ import annotations

import copy
from typing import Any

from text2ifc_contract.validation_v2 import validate_v2_document


class ProjectionError(ValueError):
    """Raised when a Draft partial document cannot be projected safely."""


ENTITY_DROP_CODES = {
    "CLASS_NOT_GENERATABLE",
    "COMPILER_ONLY_CLASS",
    "INVALID_ENTITY_CLASS",
    "MISSING_OBJECT_PLACEMENT",
    "MISSING_REPRESENTATION",
    "UNKNOWN_IFC_CLASS",
    "UNSUPPORTED_IFC_CLASS",
    "WALL_STANDARD_CASE_REQUIRES_RECTANGLE",
}
RELATIONSHIP_DROP_CODES = {
    "INVALID_RELATIONSHIP_CLASS",
    "RELATIONSHIP_ENDPOINT_TYPE_MISMATCH",
    "UNRESOLVED_RELATIONSHIP_ENDPOINT",
    "UNSUPPORTED_RELATIONSHIP_CLASS",
}
ATTRIBUTE_DROP_CODES = {
    "DERIVED_IFC_ATTRIBUTE",
    "INVALID_IFC_ATTRIBUTE",
    "INVALID_IFC_ATTRIBUTE_TYPE",
}
PROPERTY_DROP_CODES = {
    "INVALID_PROPERTY_TYPE",
    "PROPERTY_SET_NOT_APPLICABLE",
    "UNKNOWN_STANDARD_PROPERTY",
    "UNNAMESPACED_CUSTOM_PROPERTY_SET",
}
PLACEMENT_ENTITY_DROP_CODES = {
    "INVALID_PLACEMENT_PARENT_CLASS",
    "PLACEMENT_CYCLE",
    "PLACEMENT_DEPTH_EXCEEDED",
    "UNRESOLVED_PLACEMENT_PARENT",
}
MAX_PROJECTION_STEPS = 100_000


def _tokens(path: str) -> list[str]:
    return [
        token.replace("~1", "/").replace("~0", "~")
        for token in path.lstrip("/").split("/")
        if token != ""
    ]


def _at(document: Any, path: str) -> Any:
    current = document
    for token in _tokens(path):
        if isinstance(current, list):
            current = current[int(token)]
        else:
            current = current[token]
    return current


def _delete(document: Any, path: str) -> Any:
    tokens = _tokens(path)
    if not tokens:
        raise ProjectionError("cannot delete document root")
    parent = document
    for token in tokens[:-1]:
        if isinstance(parent, list):
            parent = parent[int(token)]
        else:
            parent = parent[token]
    leaf = tokens[-1]
    if isinstance(parent, list):
        index = int(leaf)
        value = parent[index]
        del parent[index]
        return value
    value = parent[leaf]
    del parent[leaf]
    return value


def _entity_path(issue_path: str) -> str:
    tokens = _tokens(issue_path)
    if len(tokens) < 2 or tokens[0] != "entities":
        raise ProjectionError(f"issue path does not identify an entity: {issue_path}")
    return f"/entities/{tokens[1]}"


def _relationship_path(issue_path: str) -> str:
    tokens = _tokens(issue_path)
    if len(tokens) < 2 or tokens[0] != "relationships":
        raise ProjectionError(
            f"issue path does not identify a relationship: {issue_path}"
        )
    return f"/relationships/{tokens[1]}"


def _property_set_path(issue_path: str) -> str:
    tokens = _tokens(issue_path)
    if len(tokens) < 4 or tokens[0] != "entities" or tokens[2] != "property_sets":
        raise ProjectionError(f"issue path does not identify a property: {issue_path}")
    if len(tokens) == 4:
        return issue_path
    return "/" + "/".join(_escape(token) for token in tokens[:5])


def _escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _entity_id_for_path(document: dict[str, Any], issue_path: str) -> str:
    try:
        entity = _at(document, _entity_path(issue_path))
    except (KeyError, IndexError, ValueError, TypeError):
        return ""
    return str(entity.get("id", ""))


def _relationship_id_for_path(document: dict[str, Any], issue_path: str) -> str:
    try:
        relationship = _at(document, _relationship_path(issue_path))
    except (KeyError, IndexError, ValueError, TypeError):
        return ""
    return str(relationship.get("id", ""))


def _omission(
    *,
    source_record: dict[str, Any],
    issue: Any,
    path: str,
    omitted_value: Any,
    reason: str,
    entity_id: str,
) -> dict[str, Any]:
    return {
        "source_file_id": source_record["id"],
        "source_sha256": source_record.get("sha256"),
        "entity_id": entity_id,
        "path": path,
        "issue_code": str(issue.code),
        "issue_path": str(issue.path),
        "message": str(issue.message),
        "reason": reason,
        "omitted_value": omitted_value,
    }


def _apply_issue(
    document: dict[str, Any],
    issue: Any,
    *,
    source_record: dict[str, Any],
) -> dict[str, Any]:
    code = issue.code
    issue_path = issue.path
    if code in ENTITY_DROP_CODES or code in PLACEMENT_ENTITY_DROP_CODES:
        path = _entity_path(issue_path)
        entity_id = _entity_id_for_path(document, issue_path)
        omitted = _delete(document, path)
        return _omission(
            source_record=source_record,
            issue=issue,
            path=path,
            omitted_value=omitted,
            reason="entity omitted because it is outside the formal generation profile",
            entity_id=entity_id,
        )
    if code in RELATIONSHIP_DROP_CODES:
        path = _relationship_path(issue_path)
        relationship_id = _relationship_id_for_path(document, issue_path)
        omitted = _delete(document, path)
        return _omission(
            source_record=source_record,
            issue=issue,
            path=path,
            omitted_value=omitted,
            reason="relationship omitted because its class or endpoints are not formal",
            entity_id=relationship_id,
        )
    if code in ATTRIBUTE_DROP_CODES:
        entity_id = _entity_id_for_path(document, issue_path)
        omitted = _delete(document, issue_path)
        return _omission(
            source_record=source_record,
            issue=issue,
            path=issue_path,
            omitted_value=omitted,
            reason="native IFC attribute omitted because validator rejected its value",
            entity_id=entity_id,
        )
    if code in PROPERTY_DROP_CODES:
        path = _property_set_path(issue_path)
        entity_id = _entity_id_for_path(document, issue_path)
        omitted = _delete(document, path)
        return _omission(
            source_record=source_record,
            issue=issue,
            path=path,
            omitted_value=omitted,
            reason="property value omitted because validator rejected its value",
            entity_id=entity_id,
        )
    raise ProjectionError(
        f"unsupported projection issue {issue.code} at {issue.path}: {issue.message}"
    )


def project_supported_scope_target(
    document: dict[str, Any],
    *,
    source_record: dict[str, Any],
) -> dict[str, Any]:
    target = copy.deepcopy(document)
    omissions: list[dict[str, Any]] = []
    for _ in range(MAX_PROJECTION_STEPS):
        issues = validate_v2_document(target)
        if not issues:
            return {
                "target": target,
                "omissions": omissions,
                "validation_issues": [],
            }
        omissions.append(
            _apply_issue(target, issues[0], source_record=source_record)
        )
    raise ProjectionError("projection step limit exceeded")
