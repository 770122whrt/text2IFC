"""Typed, Gold-free semantic compiler input for IFC repair operations."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatchcase
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from .evaluation_policy import EvidenceSourceKind, SemanticApplicability
from .production_evidence import ProductionEvidence
from .registry import OperationRegistry


SEMANTIC_MANIFEST_SCHEMA_VERSION = "text2ifc/ifc-repair-semantic-manifest/0.1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_MANIFEST_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-semantic-manifest-0.1.schema.json"
)
_SUPPORTED_FACT_KINDS = frozenset(
    {"relationship", "attribute", "pset", "quantity", "material", "classification", "label"}
)
_AUTHORIZED_SOURCES = frozenset(
    {
        EvidenceSourceKind.EXPLICIT_REQUEST,
        EvidenceSourceKind.SURVIVING_TARGET,
        EvidenceSourceKind.SURVIVING_HOST,
        EvidenceSourceKind.SURVIVING_TYPE,
        EvidenceSourceKind.AUTHORIZED_TYPE_COHORT,
        EvidenceSourceKind.APPROVED_PROTOTYPE,
        EvidenceSourceKind.DETERMINISTIC_POLICY,
    }
)


class SemanticManifestError(ValueError):
    """Stable machine-readable semantic manifest failure."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


class SemanticOwnership(str, Enum):
    OCCURRENCE_DIRECT = "occurrence_direct"
    TYPE_INHERITED = "type_inherited"


class SemanticAuthoringAction(str, Enum):
    SET_ATTRIBUTE = "set_attribute"
    SET_OCCURRENCE_PSET = "set_occurrence_pset"
    SET_QUANTITY = "set_quantity"
    REUSE_MATERIAL = "reuse_material"
    REUSE_CLASSIFICATION = "reuse_classification"
    BIND_RELATIONSHIP = "bind_relationship"
    INHERIT_FROM_TYPE = "inherit_from_type"


@dataclass(frozen=True)
class SemanticAssignment:
    operation_id: str
    fact_key: str
    source_fact_key: str
    value: Any
    value_type: str
    unit: str | None
    ownership: SemanticOwnership
    applicability: SemanticApplicability
    source_kind: EvidenceSourceKind
    source_ref: str
    provenance: tuple[str, ...]
    authoring_action: SemanticAuthoringAction


@dataclass(frozen=True)
class SemanticManifest:
    schema_version: str
    manifest_id: str
    operation_id: str
    operation_type: str
    base_model_fingerprint: str
    policy_id: str
    policy_version: str
    assignments: tuple[SemanticAssignment, ...]


def semantic_assignment_identity(
    assignment: SemanticAssignment,
) -> tuple[str, str, str, str]:
    """Return the operation-neutral deterministic assignment identity."""

    return (
        assignment.operation_id,
        assignment.fact_key,
        assignment.ownership.value,
        assignment.authoring_action.value,
    )


def order_semantic_assignments(
    assignments: Sequence[SemanticAssignment],
) -> tuple[SemanticAssignment, ...]:
    """Deduplicate identical assignments, reject conflicts, and sort stably."""

    by_slot: dict[tuple[str, str], SemanticAssignment] = {}
    for assignment in assignments:
        slot = (assignment.operation_id, assignment.fact_key)
        previous = by_slot.get(slot)
        if previous is not None and previous != assignment:
            raise SemanticManifestError(
                "CONFLICTING_SEMANTIC_ASSIGNMENT", assignment.fact_key
            )
        by_slot[slot] = assignment
    return tuple(sorted(by_slot.values(), key=semantic_assignment_identity))


@lru_cache(maxsize=1)
def _cached_schema() -> dict[str, Any]:
    schema = json.loads(SEMANTIC_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def load_semantic_manifest_schema() -> dict[str, Any]:
    return copy.deepcopy(_cached_schema())


def parse_semantic_manifest(document: Any) -> SemanticManifest:
    if not isinstance(document, Mapping):
        raise SemanticManifestError("INVALID_SEMANTIC_MANIFEST", "expected object")
    if document.get("schema_version") != SEMANTIC_MANIFEST_SCHEMA_VERSION:
        raise SemanticManifestError(
            "SEMANTIC_MANIFEST_SCHEMA_VERSION_MISMATCH",
            repr(document.get("schema_version")),
        )
    assignments = document.get("assignments")
    if not isinstance(assignments, Sequence) or isinstance(assignments, (str, bytes)):
        raise SemanticManifestError("INVALID_SEMANTIC_ASSIGNMENTS", "expected array")
    operation_id = str(document.get("operation_id") or "")
    for index, payload in enumerate(assignments):
        _validate_assignment_semantics(payload, operation_id=operation_id, index=index)
    structural = sorted(
        Draft202012Validator(_cached_schema()).iter_errors(document),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if structural:
        error = structural[0]
        raise SemanticManifestError("SEMANTIC_MANIFEST_SCHEMA_INVALID", error.message)

    parsed = order_semantic_assignments(
        tuple(_parse_assignment(payload) for payload in assignments)
    )
    policy = document["policy"]
    return SemanticManifest(
        schema_version=SEMANTIC_MANIFEST_SCHEMA_VERSION,
        manifest_id=str(document["manifest_id"]),
        operation_id=operation_id,
        operation_type=str(document["operation_type"]),
        base_model_fingerprint=str(document["base_model_fingerprint"]),
        policy_id=str(policy["policy_id"]),
        policy_version=str(policy["policy_version"]),
        assignments=parsed,
    )


def build_semantic_manifest(
    *,
    production_evidence: ProductionEvidence,
    operation_id: str,
    base_model_fingerprint: str,
    registry: OperationRegistry,
) -> SemanticManifest:
    """Compile the same authoritative facts used by L2 into authoring input."""

    try:
        operation_type = production_evidence.operation_types[operation_id]
        facts = production_evidence.expected_facts_by_operation[operation_id]
        decisions = production_evidence.applicability_by_operation[operation_id]
    except KeyError as error:
        raise SemanticManifestError(
            "SEMANTIC_MANIFEST_OPERATION_NOT_FOUND", operation_id
        ) from error
    policy = registry.require_evaluation_policy(operation_type)
    assignments: list[dict[str, Any]] = []
    for fact in facts:
        spec = next(
            (
                candidate
                for candidate in policy.semantic_facts
                if fnmatchcase(fact.fact_key, candidate.fact_pattern)
            ),
            None,
        )
        if spec is None:
            applicability = SemanticApplicability.CONDITIONAL
        else:
            decision = decisions[spec.check_id]
            if decision.outcome != "evaluable":
                continue
            applicability = spec.applicability
        source_fact_key = next(
            (
                item.partition(":")[2]
                for item in fact.provenance
                if item.startswith("source_fact_key:")
            ),
            fact.fact_key,
        )
        ownership = (
            SemanticOwnership.TYPE_INHERITED
            if fact.source_kind
            in {
                EvidenceSourceKind.SURVIVING_TYPE,
                EvidenceSourceKind.APPROVED_PROTOTYPE,
            }
            else SemanticOwnership.OCCURRENCE_DIRECT
        )
        assignments.append(
            {
                "operation_id": operation_id,
                "fact_key": fact.fact_key,
                "source_fact_key": source_fact_key,
                "value": copy.deepcopy(fact.value),
                "value_type": fact.value_type or "IfcValue",
                "unit": fact.unit,
                "ownership": ownership.value,
                "applicability": applicability.value,
                "source_kind": fact.source_kind.value,
                "source_ref": fact.source_ref,
                "provenance": list(fact.provenance),
                "authoring_action": _authoring_action(
                    fact.fact_key, ownership
                ).value,
            }
        )
    identity = json.dumps(
        {
            "operation_id": operation_id,
            "operation_type": operation_type,
            "base_model_fingerprint": base_model_fingerprint,
            "policy_id": policy.policy_id,
            "policy_version": policy.version,
            "assignments": assignments,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return parse_semantic_manifest(
        {
            "schema_version": SEMANTIC_MANIFEST_SCHEMA_VERSION,
            "manifest_id": f"semantic-manifest-{hashlib.sha256(identity).hexdigest()[:24]}",
            "operation_id": operation_id,
            "operation_type": operation_type,
            "base_model_fingerprint": base_model_fingerprint,
            "policy": {
                "policy_id": policy.policy_id,
                "policy_version": policy.version,
            },
            "assignments": assignments,
        }
    )


def _authoring_action(
    fact_key: str, ownership: SemanticOwnership
) -> SemanticAuthoringAction:
    if ownership is SemanticOwnership.TYPE_INHERITED:
        return SemanticAuthoringAction.INHERIT_FROM_TYPE
    category = fact_key.partition(":")[0]
    return {
        "relationship": SemanticAuthoringAction.BIND_RELATIONSHIP,
        "attribute": SemanticAuthoringAction.SET_ATTRIBUTE,
        "label": SemanticAuthoringAction.SET_ATTRIBUTE,
        "pset": SemanticAuthoringAction.SET_OCCURRENCE_PSET,
        "quantity": SemanticAuthoringAction.SET_QUANTITY,
        "material": SemanticAuthoringAction.REUSE_MATERIAL,
        "classification": SemanticAuthoringAction.REUSE_CLASSIFICATION,
    }[category]


def _validate_assignment_semantics(payload: Any, *, operation_id: str, index: int) -> None:
    if not isinstance(payload, Mapping):
        raise SemanticManifestError("INVALID_SEMANTIC_ASSIGNMENT", str(index))
    if str(payload.get("operation_id") or "") != operation_id:
        raise SemanticManifestError(
            "CROSS_OPERATION_SEMANTIC_ASSIGNMENT", str(payload.get("operation_id"))
        )
    provenance = payload.get("provenance")
    if not isinstance(provenance, Sequence) or isinstance(provenance, (str, bytes)) or not provenance or any(not str(item).strip() for item in provenance):
        raise SemanticManifestError("MISSING_SEMANTIC_PROVENANCE", str(index))
    try:
        source = EvidenceSourceKind(str(payload.get("source_kind")))
    except ValueError as error:
        raise SemanticManifestError(
            "UNAUTHORIZED_SEMANTIC_SOURCE", str(payload.get("source_kind"))
        ) from error
    if source not in _AUTHORIZED_SOURCES:
        raise SemanticManifestError("UNAUTHORIZED_SEMANTIC_SOURCE", source.value)
    fact_key = str(payload.get("fact_key") or "")
    fact_kind = fact_key.partition(":")[0]
    if fact_kind not in _SUPPORTED_FACT_KINDS:
        raise SemanticManifestError("UNSUPPORTED_SEMANTIC_FACT_KIND", fact_key)
    if _contains_non_finite(payload.get("value")):
        raise SemanticManifestError("NON_FINITE_SEMANTIC_VALUE", fact_key)


def _parse_assignment(payload: Mapping[str, Any]) -> SemanticAssignment:
    return SemanticAssignment(
        operation_id=str(payload["operation_id"]),
        fact_key=str(payload["fact_key"]),
        source_fact_key=str(payload["source_fact_key"]),
        value=copy.deepcopy(payload["value"]),
        value_type=str(payload["value_type"]),
        unit=None if payload["unit"] is None else str(payload["unit"]),
        ownership=SemanticOwnership(str(payload["ownership"])),
        applicability=SemanticApplicability(str(payload["applicability"])),
        source_kind=EvidenceSourceKind(str(payload["source_kind"])),
        source_ref=str(payload["source_ref"]),
        provenance=tuple(str(item) for item in payload["provenance"]),
        authoring_action=SemanticAuthoringAction(str(payload["authoring_action"])),
    )


def _contains_non_finite(value: Any) -> bool:
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, Mapping):
        return any(_contains_non_finite(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_non_finite(item) for item in value)
    return False


__all__ = [
    "SEMANTIC_MANIFEST_SCHEMA_VERSION",
    "SemanticAssignment",
    "SemanticAuthoringAction",
    "SemanticManifest",
    "SemanticManifestError",
    "SemanticOwnership",
    "load_semantic_manifest_schema",
    "build_semantic_manifest",
    "order_semantic_assignments",
    "parse_semantic_manifest",
    "semantic_assignment_identity",
]
