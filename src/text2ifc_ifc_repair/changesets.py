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
BOUND_CHANGESET_SCHEMA_VERSION_0_3 = "text2ifc/ifc-repair-changeset/0.3"
BOUND_CHANGESET_SCHEMA_VERSION_0_4 = "text2ifc/ifc-repair-changeset/0.4"
DRAFT_CHANGESET_SCHEMA_VERSION = "text2ifc/ifc-repair-changeset-draft/0.2"
DRAFT_CHANGESET_SCHEMA_VERSION_0_3 = "text2ifc/ifc-repair-changeset-draft/0.3"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHANGESET_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-changeset-0.1.schema.json"
)
BOUND_CHANGESET_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-changeset-0.2.schema.json"
BOUND_CHANGESET_SCHEMA_PATH_0_3 = PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-changeset-0.3.schema.json"
BOUND_CHANGESET_SCHEMA_PATH_0_4 = PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-changeset-0.4.schema.json"
DRAFT_CHANGESET_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-changeset-draft-0.2.schema.json"
DRAFT_CHANGESET_SCHEMA_PATH_0_3 = PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-changeset-draft-0.3.schema.json"


@lru_cache(maxsize=1)
def _cached_changeset_schema() -> dict[str, Any]:
    schema = json.loads(CHANGESET_SCHEMA_PATH.read_text(encoding="utf-8"))
    _assert_local_references(schema)
    Draft202012Validator.check_schema(schema)
    return schema


def load_changeset_schema() -> dict[str, Any]:
    """Return an isolated copy of the public IFC repair ChangeSet schema."""

    return copy.deepcopy(_cached_changeset_schema())


@lru_cache(maxsize=4)
def _cached_schema(path: str) -> dict[str, Any]:
    schema = json.loads(Path(path).read_text(encoding="utf-8"))
    _assert_local_references(schema)
    Draft202012Validator.check_schema(schema)
    return schema


def load_changeset_draft_schema(
    version: str = DRAFT_CHANGESET_SCHEMA_VERSION,
) -> dict[str, Any]:
    path = {
        DRAFT_CHANGESET_SCHEMA_VERSION: DRAFT_CHANGESET_SCHEMA_PATH,
        DRAFT_CHANGESET_SCHEMA_VERSION_0_3: DRAFT_CHANGESET_SCHEMA_PATH_0_3,
    }.get(version)
    if path is None:
        raise ValueError(f"unsupported draft ChangeSet schema: {version}")
    return copy.deepcopy(_cached_schema(str(path)))


def load_bound_changeset_schema(
    version: str = BOUND_CHANGESET_SCHEMA_VERSION,
) -> dict[str, Any]:
    path = {
        BOUND_CHANGESET_SCHEMA_VERSION: BOUND_CHANGESET_SCHEMA_PATH,
        BOUND_CHANGESET_SCHEMA_VERSION_0_3: BOUND_CHANGESET_SCHEMA_PATH_0_3,
        BOUND_CHANGESET_SCHEMA_VERSION_0_4: BOUND_CHANGESET_SCHEMA_PATH_0_4,
    }.get(version)
    if path is None:
        raise ValueError(f"unsupported bound ChangeSet schema: {version}")
    return copy.deepcopy(_cached_schema(str(path)))


def validate_changeset(document: Any) -> list[ValidationIssue]:
    """Return stable structural and envelope-level semantic diagnostics."""

    version = document.get("schema_version") if isinstance(document, Mapping) else None
    if version == BOUND_CHANGESET_SCHEMA_VERSION:
        schema = _cached_schema(str(BOUND_CHANGESET_SCHEMA_PATH))
    elif version == BOUND_CHANGESET_SCHEMA_VERSION_0_3:
        schema = _cached_schema(str(BOUND_CHANGESET_SCHEMA_PATH_0_3))
    elif version == BOUND_CHANGESET_SCHEMA_VERSION_0_4:
        schema = _cached_schema(str(BOUND_CHANGESET_SCHEMA_PATH_0_4))
    else:
        schema = _cached_changeset_schema()
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


def validate_changeset_draft(
    document: Any,
    *,
    expected_version: str | None = None,
) -> list[ValidationIssue]:
    version = (
        expected_version
        if expected_version is not None
        else document.get("schema_version")
        if isinstance(document, Mapping)
        else None
    )
    path = {
        DRAFT_CHANGESET_SCHEMA_VERSION: DRAFT_CHANGESET_SCHEMA_PATH,
        DRAFT_CHANGESET_SCHEMA_VERSION_0_3: DRAFT_CHANGESET_SCHEMA_PATH_0_3,
    }.get(version, DRAFT_CHANGESET_SCHEMA_PATH)
    validator = Draft202012Validator(_cached_schema(str(path)))
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
    bound_schema_version: str = BOUND_CHANGESET_SCHEMA_VERSION,
    resolved_authority: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind a non-authoritative Provider draft to immutable semantic manifests."""

    issues = validate_changeset_draft(
        draft,
        expected_version=(
            str(draft.get("schema_version"))
            if resolved_authority is not None
            else None
        ),
    )
    if issues:
        raise ValueError(f"DRAFT_SCHEMA_INVALID:{issues[0].path}")
    if resolved_authority is not None:
        _require_exact_draft_authority(draft, resolved_authority)
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
                    _assignment_payload(
                        assignment,
                        bound_schema_version=bound_schema_version,
                    )
                    for assignment in manifest.assignments
                ],
            }
        )
    if manifests:
        raise ValueError("SEMANTIC_MANIFEST_SET_MISMATCH")
    bound = {
        "schema_version": bound_schema_version,
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


def _require_exact_draft_authority(
    draft: Mapping[str, Any],
    authority: Mapping[str, Any],
) -> None:
    expected_operations = list(authority.get("operations", ()))
    actual_operations = list(draft.get("operations", ()))
    if len(actual_operations) != len(expected_operations):
        raise ValueError(
            "DRAFT_AUTHORITY_OPERATION_CARDINALITY_MISMATCH:/operations"
        )
    expected_ids = [str(item.get("operation_id", "")) for item in expected_operations]
    actual_ids = [str(item.get("operation_id", "")) for item in actual_operations]
    if (
        len(set(actual_ids)) != len(actual_ids)
        or set(actual_ids) != set(expected_ids)
    ):
        raise ValueError("DRAFT_AUTHORITY_OPERATION_ID_SET_MISMATCH:/operations")
    if not _identifier_set_equal(
        draft.get("scope"), authority.get("scope")
    ):
        raise ValueError("DRAFT_AUTHORITY_SCOPE_MISMATCH:/scope")
    if not _identifier_set_equal(
        draft.get("evidence_refs"), authority.get("evidence_refs")
    ):
        raise ValueError("DRAFT_AUTHORITY_EVIDENCE_MISMATCH:/evidence_refs")

    expected_by_id = {
        str(item["operation_id"]): item for item in expected_operations
    }
    for index, operation in enumerate(actual_operations):
        operation_id = str(operation["operation_id"])
        expected = expected_by_id[operation_id]
        if operation.get("operation_type") != expected.get("operation_type"):
            raise ValueError(
                "DRAFT_AUTHORITY_OPERATION_TYPE_MISMATCH:"
                f"/operations/{index}/operation_type"
            )
        if operation.get("target") != expected.get("target"):
            raise ValueError(
                f"DRAFT_AUTHORITY_TARGET_MISMATCH:/operations/{index}/target"
            )
        if operation.get("parameters") != expected.get("parameters"):
            raise ValueError(
                "DRAFT_AUTHORITY_PARAMETERS_MISMATCH:"
                f"/operations/{index}/parameters"
            )
        if not _identifier_set_equal(
            operation.get("evidence_refs"), expected.get("evidence_refs")
        ):
            raise ValueError(
                "DRAFT_AUTHORITY_OPERATION_EVIDENCE_MISMATCH:"
                f"/operations/{index}/evidence_refs"
            )


def _identifier_set_equal(draft_value: Any, authority_value: Any) -> bool:
    """Compare draft-authority identifier collections as sets.

    The deterministic authority builds ``scope`` and ``evidence_refs`` as
    ``sorted(set(...))`` identifier collections, and the published draft
    schema declares them with ``uniqueItems: true`` — they are sets, not
    ordered sequences.  A Provider returning the same identifiers in a
    different order is set-equivalent and must bind; any identifier drift,
    duplication, or shape change still fails closed.
    """

    if isinstance(draft_value, Mapping) and isinstance(
        authority_value, Mapping
    ):
        if set(draft_value.keys()) != set(authority_value.keys()):
            return False
        return all(
            _identifier_set_equal(draft_value[key], authority_value[key])
            for key in draft_value
        )
    if isinstance(draft_value, (list, tuple)) and isinstance(
        authority_value, (list, tuple)
    ):
        return len(draft_value) == len(authority_value) and sorted(
            str(item) for item in draft_value
        ) == sorted(str(item) for item in authority_value)
    if isinstance(draft_value, (list, tuple)) or isinstance(
        authority_value, (list, tuple)
    ):
        return False
    return draft_value == authority_value


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


def _assignment_payload(
    value: Any,
    *,
    bound_schema_version: str,
) -> dict[str, Any]:
    payload = _plain_json(value)
    payload["provenance"] = list(dict.fromkeys(payload["provenance"]))
    if bound_schema_version == BOUND_CHANGESET_SCHEMA_VERSION:
        payload.pop("scope", None)
        payload.pop("derivation", None)
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
