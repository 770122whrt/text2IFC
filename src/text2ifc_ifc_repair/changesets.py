"""Schema-backed contract for unified semantic IFC repair ChangeSets."""

from __future__ import annotations

import copy
import json
import math
from collections.abc import Iterable, Mapping, Sequence
from functools import lru_cache
from numbers import Number
from pathlib import Path
from typing import Any
from dataclasses import asdict
from enum import Enum

from jsonschema import Draft202012Validator

from text2ifc_contract.validation import ValidationIssue


CHANGESET_SCHEMA_VERSION = "text2ifc/ifc-repair-changeset/0.1"
BOUND_CHANGESET_SCHEMA_VERSION = "text2ifc/ifc-repair-changeset/0.2"
DRAFT_CHANGESET_SCHEMA_VERSION = "text2ifc/ifc-repair-changeset-draft/0.2"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHANGESET_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-changeset-0.1.schema.json"
)
BOUND_CHANGESET_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-changeset-0.2.schema.json"
DRAFT_CHANGESET_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-changeset-draft-0.2.schema.json"


@lru_cache(maxsize=1)
def _cached_changeset_schema() -> dict[str, Any]:
    schema = json.loads(CHANGESET_SCHEMA_PATH.read_text(encoding="utf-8"))
    _assert_local_references(schema)
    Draft202012Validator.check_schema(schema)
    return schema


def load_changeset_schema() -> dict[str, Any]:
    """Return an isolated copy of the public IFC repair ChangeSet schema."""

    return copy.deepcopy(_cached_changeset_schema())


@lru_cache(maxsize=2)
def _cached_schema(path: str) -> dict[str, Any]:
    schema = json.loads(Path(path).read_text(encoding="utf-8"))
    _assert_local_references(schema)
    Draft202012Validator.check_schema(schema)
    return schema


def load_changeset_draft_schema() -> dict[str, Any]:
    return copy.deepcopy(_cached_schema(str(DRAFT_CHANGESET_SCHEMA_PATH)))


def load_bound_changeset_schema() -> dict[str, Any]:
    return copy.deepcopy(_cached_schema(str(BOUND_CHANGESET_SCHEMA_PATH)))


def validate_changeset(document: Any) -> list[ValidationIssue]:
    """Return stable structural and envelope-level semantic diagnostics."""

    version = document.get("schema_version") if isinstance(document, Mapping) else None
    schema = (
        _cached_schema(str(BOUND_CHANGESET_SCHEMA_PATH))
        if version == BOUND_CHANGESET_SCHEMA_VERSION
        else _cached_changeset_schema()
    )
    validator = Draft202012Validator(schema)
    issues = [
        ValidationIssue(
            code="SCHEMA_VALIDATION_ERROR",
            path=_pointer(error.absolute_path),
            message=error.message,
        )
        for error in validator.iter_errors(document)
    ]
    if issues or not isinstance(document, dict):
        return _sort_issues(issues)
    issues.extend(_semantic_issues(document))
    issues.extend(_non_finite_number_issues(document))
    return _sort_issues(issues)


def validate_changeset_draft(document: Any) -> list[ValidationIssue]:
    validator = Draft202012Validator(_cached_schema(str(DRAFT_CHANGESET_SCHEMA_PATH)))
    issues = [
        ValidationIssue(
            code="DRAFT_SCHEMA_VALIDATION_ERROR",
            path=_pointer(error.absolute_path),
            message=error.message,
        )
        for error in validator.iter_errors(document)
    ]
    issues.extend(_non_finite_number_issues(document))
    return _sort_issues(issues)


def bind_repair_changeset(
    *,
    draft: Mapping[str, Any],
    semantic_manifests: Sequence[Any],
    semantic_manifest_hashes: Mapping[str, str],
    source_request_hash: str,
    base_model_fingerprint: str,
) -> dict[str, Any]:
    """Bind a non-authoritative Provider draft to immutable semantic manifests."""

    issues = validate_changeset_draft(draft)
    if issues:
        raise ValueError(f"DRAFT_SCHEMA_INVALID:{issues[0].path}")
    if draft["source_request_hash"] != source_request_hash:
        raise ValueError("SOURCE_REQUEST_HASH_MISMATCH")
    if draft["base_model_fingerprint"] != base_model_fingerprint:
        raise ValueError("BASE_MODEL_FINGERPRINT_MISMATCH")
    manifests = {item.operation_id: item for item in semantic_manifests}
    operations = []
    for operation in draft["operations"]:
        operation_id = str(operation["operation_id"])
        manifest = manifests.pop(operation_id, None)
        if manifest is None:
            raise ValueError(f"SEMANTIC_MANIFEST_OPERATION_MISMATCH:{operation_id}")
        expected_hash = semantic_manifest_hashes.get(operation_id)
        if expected_hash != draft["semantic_manifest_sha256"]:
            raise ValueError(f"SEMANTIC_MANIFEST_HASH_MISMATCH:{operation_id}")
        if (
            manifest.base_model_fingerprint != base_model_fingerprint
            or manifest.operation_type != operation["operation_type"]
        ):
            raise ValueError(f"SEMANTIC_MANIFEST_BINDING_MISMATCH:{operation_id}")
        operations.append(
            {
                **copy.deepcopy(dict(operation)),
                "semantic_manifest": {
                    "manifest_id": manifest.manifest_id,
                    "policy_id": manifest.policy_id,
                    "policy_version": manifest.policy_version,
                },
                "semantic_assignments": [
                    _assignment_payload(assignment)
                    for assignment in manifest.assignments
                ],
            }
        )
    if manifests:
        raise ValueError("SEMANTIC_MANIFEST_SET_MISMATCH")
    bound = {
        "schema_version": BOUND_CHANGESET_SCHEMA_VERSION,
        "changeset_id": str(draft["draft_id"]).replace("draft", "changeset", 1),
        "binding_status": "bound",
        "base_model_fingerprint": base_model_fingerprint,
        "source_request_hash": source_request_hash,
        "semantic_manifest_ref": draft["semantic_manifest_ref"],
        "semantic_manifest_sha256": draft["semantic_manifest_sha256"],
        "scope": copy.deepcopy(draft["scope"]),
        "evidence_refs": copy.deepcopy(draft["evidence_refs"]),
        "preconditions": copy.deepcopy(draft["preconditions"]),
        "postconditions": copy.deepcopy(draft["postconditions"]),
        "operations": operations,
    }
    bound_issues = validate_changeset(bound)
    if bound_issues:
        raise ValueError(f"BOUND_CHANGESET_INVALID:{bound_issues[0].path}")
    return bound


def _plain_json(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _plain_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_json(item) for item in value]
    return copy.deepcopy(value)


def _assignment_payload(value: Any) -> dict[str, Any]:
    payload = _plain_json(value)
    payload["provenance"] = list(dict.fromkeys(payload["provenance"]))
    return payload


def canonical_changeset_json(document: Any) -> str:
    """Serialize one valid ChangeSet deterministically without mutation."""

    issues = validate_changeset(document)
    if issues:
        raise ValueError(f"invalid IFC repair ChangeSet: {issues[0].code}")
    return json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _semantic_issues(document: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    operation_ids: set[str] = set()
    declared_evidence = set(document["evidence_refs"])
    for index, operation in enumerate(document["operations"]):
        operation_id = operation["operation_id"]
        if operation_id in operation_ids:
            issues.append(
                ValidationIssue(
                    code="DUPLICATE_CHANGESET_OPERATION_ID",
                    path=f"/operations/{index}/operation_id",
                    message=f"Operation ID {operation_id!r} is duplicated.",
                )
            )
        operation_ids.add(operation_id)
        for evidence_index, evidence_ref in enumerate(operation["evidence_refs"]):
            if evidence_ref not in declared_evidence:
                issues.append(
                    ValidationIssue(
                        code="UNDECLARED_CHANGESET_EVIDENCE",
                        path=f"/operations/{index}/evidence_refs/{evidence_index}",
                        message=f"Evidence {evidence_ref!r} is not declared by the envelope.",
                    )
                )
    return issues


def _non_finite_number_issues(
    value: Any,
    path: tuple[Any, ...] = (),
) -> list[ValidationIssue]:
    if isinstance(value, Mapping):
        return [
            issue
            for key, child in value.items()
            for issue in _non_finite_number_issues(child, (*path, key))
        ]
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [
            issue
            for index, child in enumerate(value)
            for issue in _non_finite_number_issues(child, (*path, index))
        ]
    if isinstance(value, Number) and not isinstance(value, bool):
        try:
            finite = math.isfinite(value)
        except (OverflowError, TypeError, ValueError):
            finite = False
        if not finite:
            return [
                ValidationIssue(
                    code="NON_FINITE_NUMBER",
                    path=_pointer(path),
                    message="Number must be finite.",
                )
            ]
    return []


def _assert_local_references(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and (
                not isinstance(child, str) or not child.startswith("#")
            ):
                raise ValueError(f"Remote schema references are forbidden: {child!r}")
            _assert_local_references(child)
    elif isinstance(value, list):
        for child in value:
            _assert_local_references(child)


def _pointer(parts: Iterable[Any]) -> str:
    tokens = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(tokens) if tokens else "/"


def _sort_issues(issues: Iterable[ValidationIssue]) -> list[ValidationIssue]:
    return sorted(set(issues), key=lambda issue: (issue.path, issue.code, issue.message))
