"""Deterministic, public-only occurrence semantic resolution.

The module deliberately owns policy and source selection in one place.  It
does not author IFC, call a Provider, query the vector index for values, or
read private Ground Truth.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from .index_models import ElementRecord, PropertyFact
from .index_store import IndexRepository
from .indexer import normalize_alias
from .repair_intent import (
    OccurrenceReuseIntent,
    OccurrenceSemanticBundle,
    OperationIntent,
    PublicProvenance,
    QuantityIntent,
)
from .property_intent import ExactPropertyIntent, NaturalLanguagePropertyIntent


class OccurrenceSemanticSource(str, Enum):
    EXPLICIT_VALUE = "explicit_value"
    DETERMINISTIC_DERIVED = "deterministic_derived"
    TYPE_INHERITED = "type_inherited"
    APPROVED_OCCURRENCE_PROTOTYPE = "approved_occurrence_prototype"
    AUTHORIZED_TYPE_COHORT = "authorized_type_cohort"


class FactPolicy(str, Enum):
    COPY_SAFE = "copy_safe"
    IDENTITY_CONTEXTUAL = "identity_contextual"
    HOST_STOREY_DERIVED = "host_storey_derived"
    GEOMETRY_DERIVED = "geometry_derived"


FACT_POLICY_REGISTRY: Mapping[str, FactPolicy] = {
    "GlobalId": FactPolicy.IDENTITY_CONTEXTUAL,
    "Tag": FactPolicy.IDENTITY_CONTEXTUAL,
    "Mark": FactPolicy.IDENTITY_CONTEXTUAL,
    "Level": FactPolicy.HOST_STOREY_DERIVED,
    "Storey": FactPolicy.HOST_STOREY_DERIVED,
    "Host": FactPolicy.HOST_STOREY_DERIVED,
    "SillHeight": FactPolicy.GEOMETRY_DERIVED,
    "Elevation": FactPolicy.GEOMETRY_DERIVED,
    "Placement": FactPolicy.GEOMETRY_DERIVED,
    "Width": FactPolicy.GEOMETRY_DERIVED,
    "Height": FactPolicy.GEOMETRY_DERIVED,
    "Area": FactPolicy.GEOMETRY_DERIVED,
    "Perimeter": FactPolicy.GEOMETRY_DERIVED,
}


@dataclass(frozen=True)
class OccurrenceSemanticAssignment:
    operation_id: str
    scope: str
    fact_key: str
    value: Any
    value_type: str
    unit: str | None
    source_kind: OccurrenceSemanticSource
    source_ref: str
    provenance: tuple[str, ...]
    authoring_action: str
    derivation: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "authorized_occurrence_assignment",
            "operation_id": self.operation_id,
            "scope": self.scope,
            "fact_key": self.fact_key,
            "value": self.value,
            "value_type": self.value_type,
            "unit": self.unit,
            "source_kind": self.source_kind.value,
            "source_ref": self.source_ref,
            "provenance": list(self.provenance),
            "authoring_action": self.authoring_action,
            "derivation": None if self.derivation is None else dict(self.derivation),
        }


@dataclass(frozen=True)
class OccurrenceSemanticResult:
    status: str
    assignments: tuple[OccurrenceSemanticAssignment, ...] = ()
    reason_code: str | None = None
    candidates: tuple[Mapping[str, Any], ...] = ()


def fact_policy(fact_key: str) -> FactPolicy:
    """Return the centralized copy/derive policy for a fact path."""

    leaf = fact_key.rsplit(".", 1)[-1]
    return FACT_POLICY_REGISTRY.get(leaf, FactPolicy.COPY_SAFE)


def expand_semantic_bundles(
    operation: OperationIntent,
    bundles: Sequence[OccurrenceSemanticBundle],
) -> tuple[
    tuple[ExactPropertyIntent | NaturalLanguagePropertyIntent, ...],
    tuple[QuantityIntent, ...],
]:
    """Expand declared bundles, then let operation-local values override slots."""

    by_id = {bundle.bundle_id: bundle for bundle in bundles}
    properties: dict[
        tuple[str, str], ExactPropertyIntent | NaturalLanguagePropertyIntent
    ] = {}
    quantities: dict[tuple[str, str], QuantityIntent] = {}
    for bundle_ref in operation.semantic_bundle_refs:
        bundle = by_id.get(bundle_ref)
        if bundle is None:
            raise ValueError(f"UNKNOWN_SEMANTIC_BUNDLE:{bundle_ref}")
        for intent in bundle.property_intents:
            properties[_property_slot(intent)] = intent
        for intent in bundle.quantity_intents:
            quantities[_quantity_slot(intent)] = intent
    for intent in operation.property_intents:
        properties[_property_slot(intent)] = intent
    for intent in operation.quantity_intents:
        quantities[_quantity_slot(intent)] = intent
    return tuple(properties.values()), tuple(quantities.values())


def resolve_exact_occurrence_reference(
    repository: IndexRepository,
    reuse: OccurrenceReuseIntent,
) -> OccurrenceSemanticResult:
    """Resolve a GUID or exact human identity; zero/multiple matches clarify."""

    if reuse.reference_kind == "global_id":
        record = repository.get_by_global_id(reuse.reference)
        matches = () if record is None else (record,)
    elif reuse.reference_kind == "name":
        normalized = normalize_alias(reuse.reference)
        matches = tuple(
            record
            for record in repository.find_aliases(normalized)
            if record.identity_reliable
            and record.ifc_class in {"IfcWindow", "IfcOpeningElement"}
        )
    else:
        return OccurrenceSemanticResult(
            "clarification_required", reason_code="OCCURRENCE_REFERENCE_KIND_INVALID"
        )
    if len(matches) != 1:
        return OccurrenceSemanticResult(
            "clarification_required",
            reason_code=(
                "OCCURRENCE_REFERENCE_NOT_FOUND"
                if not matches
                else "OCCURRENCE_REFERENCE_AMBIGUOUS"
            ),
            candidates=tuple(_public_identity(item) for item in matches[:5]),
        )
    return OccurrenceSemanticResult(
        "resolved",
        candidates=(_public_identity(matches[0]),),
    )


def resolve_occurrence_reuse(
    repository: IndexRepository,
    reuse: OccurrenceReuseIntent,
    *,
    operation_id: str,
) -> OccurrenceSemanticResult:
    """Resolve the authorized reuse mode into copy-safe assignments."""

    if reuse.mode == "same_type_consensus":
        return resolve_type_cohort_consensus(
            repository, reuse, operation_id=operation_id
        )
    reference = resolve_exact_occurrence_reference(repository, reuse)
    if reference.status != "resolved":
        return reference
    identity = reference.candidates[0]
    record = repository.get_by_global_id(str(identity["global_id"]))
    assert record is not None
    assignments: list[OccurrenceSemanticAssignment] = []
    for fact in record.properties:
        path = f"{fact.set_name}.{fact.property_name}"
        if (
            fact.inherited
            or not _included(path, reuse.include_patterns)
            or fact_policy(path) is not FactPolicy.COPY_SAFE
        ):
            continue
        assignments.append(
            OccurrenceSemanticAssignment(
                operation_id=operation_id,
                scope=(
                    "opening_occurrence"
                    if record.ifc_class == "IfcOpeningElement"
                    else "window_occurrence"
                ),
                fact_key=f"pset:{path}",
                value=fact.value,
                value_type=fact.value_type or _primitive_type(fact.value),
                unit=fact.unit,
                source_kind=OccurrenceSemanticSource.APPROVED_OCCURRENCE_PROTOTYPE,
                source_ref=f"guid:{record.ifc_global_id}",
                provenance=(
                    reuse.source.reference,
                    fact.provenance,
                ),
                authoring_action="set_occurrence_pset",
            )
        )
    return OccurrenceSemanticResult("resolved", tuple(assignments))


def resolve_type_cohort_consensus(
    repository: IndexRepository,
    reuse: OccurrenceReuseIntent,
    *,
    operation_id: str,
) -> OccurrenceSemanticResult:
    """Return only unanimous, copy-safe scalar facts for an authorized Type."""

    type_ids: tuple[str, ...]
    if reuse.reference_kind == "type_global_id":
        type_ids = (
            (reuse.reference,)
            if repository.get_type_by_global_id(reuse.reference) is not None
            else ()
        )
    elif reuse.reference_kind == "type_name":
        matches = tuple(
            item
            for item in repository.find_type_aliases(normalize_alias(reuse.reference))
            if item.identity_reliable and item.ifc_global_id
        )
        type_ids = tuple(str(item.ifc_global_id) for item in matches)
    else:
        type_ids = ()
    if len(type_ids) != 1:
        return OccurrenceSemanticResult(
            "clarification_required",
            reason_code=(
                "TYPE_COHORT_NOT_FOUND"
                if not type_ids
                else "TYPE_COHORT_AMBIGUOUS"
            ),
        )
    cohort = tuple(
        record
        for record in repository.iter_records()
        if record.identity_reliable
        and record.type_global_id == type_ids[0]
        and record.ifc_class in {"IfcWindow", "IfcOpeningElement"}
    )
    if not cohort:
        return OccurrenceSemanticResult(
            "clarification_required", reason_code="TYPE_COHORT_EMPTY"
        )

    slots: dict[str, list[tuple[ElementRecord, PropertyFact]]] = {}
    for record in cohort:
        for fact in record.properties:
            path = f"{fact.set_name}.{fact.property_name}"
            if fact.inherited or not _included(path, reuse.include_patterns):
                continue
            if fact_policy(path) is not FactPolicy.COPY_SAFE:
                continue
            slots.setdefault(path, []).append((record, fact))

    assignments: list[OccurrenceSemanticAssignment] = []
    conflicts: list[Mapping[str, Any]] = []
    for path, facts in sorted(slots.items()):
        if len(facts) != len(cohort):
            conflicts.append({"fact_key": path, "reason": "missing_member"})
            continue
        canonical = {_canonical_fact(item[1]) for item in facts}
        if len(canonical) != 1:
            conflicts.append(
                {
                    "fact_key": path,
                    "reason": "mixed_value_or_unit",
                    "members": [
                        {
                            "global_id": item[0].ifc_global_id,
                            "value_digest": _digest(_canonical_fact(item[1])),
                        }
                        for item in facts[:5]
                    ],
                }
            )
            continue
        fact = facts[0][1]
        assignments.append(
            OccurrenceSemanticAssignment(
                operation_id=operation_id,
                scope="window_occurrence",
                fact_key=f"pset:{path}",
                value=fact.value,
                value_type=fact.value_type or "IfcLabel",
                unit=fact.unit,
                source_kind=OccurrenceSemanticSource.AUTHORIZED_TYPE_COHORT,
                source_ref=f"type:{type_ids[0]}",
                provenance=(
                    reuse.source.reference,
                    f"current_ifc:type_cohort:{type_ids[0]}",
                ),
                authoring_action="set_occurrence_pset",
            )
        )
    if conflicts:
        return OccurrenceSemanticResult(
            "clarification_required",
            reason_code="TYPE_COHORT_FACT_CONFLICT",
            candidates=tuple(conflicts[:5]),
        )
    return OccurrenceSemanticResult("resolved", tuple(assignments))


def explicit_assignments(
    operation: OperationIntent,
    bundles: Sequence[OccurrenceSemanticBundle],
) -> tuple[OccurrenceSemanticAssignment, ...]:
    properties, quantities = expand_semantic_bundles(operation, bundles)
    result: list[OccurrenceSemanticAssignment] = []
    for intent in properties:
        if not isinstance(intent, ExactPropertyIntent):
            raise ValueError("NATURAL_LANGUAGE_PROPERTY_REQUIRES_RESOLUTION")
        assert intent.set_name is not None and intent.property_name is not None
        path = f"{intent.set_name}.{intent.property_name}"
        result.append(
            OccurrenceSemanticAssignment(
                operation_id=operation.operation_id,
                scope="window_occurrence",
                fact_key=f"pset:{path}",
                value=intent.value,
                value_type=intent.requested_value_type or _primitive_type(intent.value),
                unit=intent.requested_unit,
                source_kind=OccurrenceSemanticSource.EXPLICIT_VALUE,
                source_ref=intent.source.reference,
                provenance=_provenance(intent.source),
                authoring_action="set_occurrence_pset",
            )
        )
    for intent in quantities:
        result.append(
            OccurrenceSemanticAssignment(
                operation_id=operation.operation_id,
                scope=intent.scope,
                fact_key=f"quantity:{intent.set_name}.{intent.quantity_name}",
                value=intent.value,
                value_type=intent.value_type,
                unit=intent.unit,
                source_kind=OccurrenceSemanticSource.EXPLICIT_VALUE,
                source_ref=intent.source.reference,
                provenance=_provenance(intent.source),
                authoring_action="set_quantity",
            )
        )
    return tuple(result)


def quantity_assignments(
    operation_id: str,
    quantities: Sequence[QuantityIntent],
) -> tuple[OccurrenceSemanticAssignment, ...]:
    return tuple(
        OccurrenceSemanticAssignment(
            operation_id=operation_id,
            scope=intent.scope,
            fact_key=f"quantity:{intent.set_name}.{intent.quantity_name}",
            value=intent.value,
            value_type=intent.value_type,
            unit=intent.unit,
            source_kind=OccurrenceSemanticSource.EXPLICIT_VALUE,
            source_ref=intent.source.reference,
            provenance=_provenance(intent.source),
            authoring_action="set_quantity",
        )
        for intent in quantities
    )


def derive_geometry_assignments(
    operation: OperationIntent,
) -> tuple[OccurrenceSemanticAssignment, ...]:
    """Derive supported geometry quantities from already bound parameters."""

    opening = operation.parameters.get("opening", {})
    width = opening.get("width_mm")
    height = opening.get("height_mm")
    derived: list[OccurrenceSemanticAssignment] = []
    values = (
        ("Width", width, "window_occurrence"),
        ("Height", height, "window_occurrence"),
    )
    for name, millimetres, scope in values:
        if millimetres is None:
            continue
        derivation = {
            "formula": "identity_mm",
            "input_digest": _digest((name, millimetres)),
        }
        derived.append(
            OccurrenceSemanticAssignment(
                operation_id=operation.operation_id,
                scope=scope,
                # Keep the authority slot canonical. The IFC writer maps
                # window-base back to the IFC2X3 BaseQuantities set.
                fact_key=f"quantity:window-base.{name}",
                value=float(millimetres),
                value_type="IfcQuantityLength",
                unit="mm",
                source_kind=OccurrenceSemanticSource.DETERMINISTIC_DERIVED,
                source_ref=f"operation:{operation.operation_id}:parameters/opening",
                provenance=(f"resolved-operation:{operation.operation_id}",),
                authoring_action="set_quantity",
                derivation=derivation,
            )
        )
    if width is not None and height is not None:
        derived.append(
            OccurrenceSemanticAssignment(
                operation_id=operation.operation_id,
                scope="window_occurrence",
                fact_key="quantity:window-base.Area",
                value=float(width) * float(height),
                value_type="IfcQuantityArea",
                unit="mm2",
                source_kind=OccurrenceSemanticSource.DETERMINISTIC_DERIVED,
                source_ref=f"operation:{operation.operation_id}:parameters/opening",
                provenance=(f"resolved-operation:{operation.operation_id}",),
                authoring_action="set_quantity",
                derivation={
                    "formula": "width_mm * height_mm",
                    "input_digest": _digest((width, height)),
                },
            )
        )
    return tuple(derived)


def _property_slot(
    intent: ExactPropertyIntent | NaturalLanguagePropertyIntent,
) -> tuple[str, str]:
    if isinstance(intent, ExactPropertyIntent):
        if intent.set_name is None or intent.property_name is None:
            raise ValueError("INCOMPLETE_EXACT_PROPERTY")
        return intent.set_name, intent.property_name
    if intent.property_phrase is None:
        raise ValueError("INCOMPLETE_NATURAL_LANGUAGE_PROPERTY")
    return "natural_language", intent.property_phrase


def _quantity_slot(intent: QuantityIntent) -> tuple[str, str]:
    return intent.scope, f"{intent.set_name}.{intent.quantity_name}"


def _included(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _canonical_fact(fact: PropertyFact) -> str:
    return json.dumps(
        [fact.value, fact.value_type, fact.unit],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _public_identity(record: ElementRecord) -> Mapping[str, Any]:
    return {
        "global_id": record.ifc_global_id,
        "ifc_class": record.ifc_class,
        "name": record.name,
        "type_global_id": record.type_global_id,
    }


def _primitive_type(value: Any) -> str:
    if isinstance(value, bool):
        return "IfcBoolean"
    if isinstance(value, int):
        return "IfcInteger"
    if isinstance(value, float):
        return "IfcReal"
    return "IfcLabel"


def _provenance(source: PublicProvenance) -> tuple[str, ...]:
    return (source.reference, f"{source.source_kind}:{source.excerpt}")


__all__ = [
    "FACT_POLICY_REGISTRY",
    "FactPolicy",
    "OccurrenceSemanticAssignment",
    "OccurrenceSemanticResult",
    "OccurrenceSemanticSource",
    "derive_geometry_assignments",
    "expand_semantic_bundles",
    "explicit_assignments",
    "fact_policy",
    "quantity_assignments",
    "resolve_exact_occurrence_reference",
    "resolve_occurrence_reuse",
    "resolve_type_cohort_consensus",
]
