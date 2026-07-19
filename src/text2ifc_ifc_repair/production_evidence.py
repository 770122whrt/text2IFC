"""Production-only semantic authority construction for Evaluation 0.2.

This module deliberately has no benchmark input type.  It turns an already
validated RepairIntent, deterministic resolution, public current-IFC records,
and registered operation policy into operation-owned expected facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from types import MappingProxyType
from typing import Any, Mapping

from .evaluation_policy import EvidenceSourceKind, SemanticApplicability
from .index_models import ElementRecord
from .registry import OperationRegistry
from .repair_intent import AttributeIntent, RepairIntent
from .resolution_flow import ResolutionBatch, ResolvedOperation
from .semantic_facts import SemanticFact, semantic_facts_from_element_record


_PRODUCTION_PRECEDENCE = (
    EvidenceSourceKind.EXPLICIT_REQUEST,
    EvidenceSourceKind.SURVIVING_TARGET,
    EvidenceSourceKind.SURVIVING_HOST,
    EvidenceSourceKind.SURVIVING_TYPE,
    EvidenceSourceKind.APPROVED_PROTOTYPE,
    EvidenceSourceKind.DETERMINISTIC_POLICY,
)
_PRODUCTION_SOURCES = frozenset(_PRODUCTION_PRECEDENCE)
_AUTHORIZED_SEMANTIC_KINDS = frozenset(
    {"formal_type_binding", "user_authorized_prototype"}
)


class ProductionEvidenceError(ValueError):
    """Stable fail-closed error at the production semantic boundary."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class EvidenceConflict:
    operation_id: str
    fact_key: str
    selected_source: EvidenceSourceKind
    rejected_source: EvidenceSourceKind
    selected_ref: str
    rejected_ref: str
    reason: str = "lower_authority_conflict"


@dataclass(frozen=True)
class ApplicabilityDecision:
    check_id: str
    applicability: str
    mandatory: bool
    outcome: str
    verified_absence: bool
    evidence_pointer: str


@dataclass(frozen=True)
class ProductionEvidence:
    expected_facts_by_operation: Mapping[str, tuple[SemanticFact, ...]]
    candidate_facts_by_operation: Mapping[str, tuple[SemanticFact, ...]]
    applicability_by_operation: Mapping[str, Mapping[str, ApplicabilityDecision]]
    operation_types: Mapping[str, str]
    conflicts: tuple[EvidenceConflict, ...]


def build_production_evidence(
    *,
    intent: RepairIntent,
    resolution: ResolutionBatch,
    changeset: Mapping[str, Any],
    registry: OperationRegistry,
    records_by_global_id: Mapping[str, ElementRecord],
    deterministic_policy_facts_by_operation: Mapping[
        str, tuple[SemanticFact, ...]
    ] | None = None,
    verified_absent_categories_by_operation: Mapping[str, tuple[str, ...]] | None = None,
) -> ProductionEvidence:
    """Build deterministic operation-scoped production expectations.

    Similarity, Provider claims and benchmark Gold cannot be represented by
    this signature.  Registered deterministic values remain explicit injected
    facts so the generic orchestrator does not grow entity-family branches.
    """

    if not isinstance(intent, RepairIntent):
        raise ProductionEvidenceError("INVALID_REPAIR_INTENT", type(intent).__name__)
    if not isinstance(resolution, ResolutionBatch) or resolution.status != "resolved":
        raise ProductionEvidenceError("UNRESOLVED_PRODUCTION_CONTEXT", resolution.status)

    policy_facts = deterministic_policy_facts_by_operation or {}
    verified_absence = verified_absent_categories_by_operation or {}
    intents = {item.operation_id: item for item in intent.operations}
    resolved = {item.operation_id: item for item in resolution.operations}
    changes = {
        str(item.get("operation_id")): item
        for item in changeset.get("operations", ())
        if isinstance(item, Mapping)
    }
    operation_ids = set(intents)
    if operation_ids != set(resolved) or operation_ids != set(changes):
        raise ProductionEvidenceError(
            "OPERATION_AUTHORITY_SET_MISMATCH",
            f"intent={sorted(operation_ids)} resolution={sorted(resolved)} changeset={sorted(changes)}",
        )
    foreign = (set(policy_facts) | set(verified_absence)) - operation_ids
    if foreign:
        raise ProductionEvidenceError("CROSS_OPERATION_EVIDENCE", sorted(foreign)[0])

    expected_by_operation: dict[str, tuple[SemanticFact, ...]] = {}
    candidates_by_operation: dict[str, tuple[SemanticFact, ...]] = {}
    applicability_by_operation: dict[str, Mapping[str, ApplicabilityDecision]] = {}
    operation_types: dict[str, str] = {}
    conflicts: list[EvidenceConflict] = []
    for operation_id in sorted(operation_ids):
        operation_intent = intents[operation_id]
        resolved_operation = resolved[operation_id]
        changeset_operation = changes[operation_id]
        operation_type = operation_intent.operation_type
        if (
            resolved_operation.operation_type != operation_type
            or str(changeset_operation.get("operation_type")) != operation_type
        ):
            raise ProductionEvidenceError("OPERATION_TYPE_MISMATCH", operation_id)
        policy = registry.require_evaluation_policy(operation_type)
        operation_types[operation_id] = operation_type
        candidates = _operation_candidates(
            operation_id=operation_id,
            operation_intent=operation_intent,
            resolved_operation=resolved_operation,
            records_by_global_id=records_by_global_id,
            deterministic_policy_facts=tuple(policy_facts.get(operation_id, ())),
            policy=policy,
        )
        selected, operation_conflicts = _select_authority(operation_id, candidates)
        candidates_by_operation[operation_id] = candidates
        expected_by_operation[operation_id] = selected
        conflicts.extend(operation_conflicts)
        applicability_by_operation[operation_id] = MappingProxyType(
            _applicability(
                operation_id=operation_id,
                policy=policy,
                selected=selected,
                verified_absent=frozenset(verified_absence.get(operation_id, ())),
            )
        )

    return ProductionEvidence(
        expected_facts_by_operation=MappingProxyType(expected_by_operation),
        candidate_facts_by_operation=MappingProxyType(candidates_by_operation),
        applicability_by_operation=MappingProxyType(applicability_by_operation),
        operation_types=MappingProxyType(operation_types),
        conflicts=tuple(sorted(conflicts, key=_conflict_key)),
    )


def _operation_candidates(
    *,
    operation_id: str,
    operation_intent: Any,
    resolved_operation: ResolvedOperation,
    records_by_global_id: Mapping[str, ElementRecord],
    deterministic_policy_facts: tuple[SemanticFact, ...],
    policy: Any,
) -> tuple[SemanticFact, ...]:
    facts: list[SemanticFact] = [
        _request_fact(operation_id, item) for item in operation_intent.attribute_intents
    ]
    target_id = resolved_operation.target_global_id
    target = _record(records_by_global_id, target_id, role="target")
    facts.extend(
        _record_facts(
            target,
            operation_id=operation_id,
            source_kind=EvidenceSourceKind.SURVIVING_TARGET,
            source_ref=f"current-target:{target_id}",
            authority_provenance="resolved_current_target",
        )
    )

    host_ids = _host_ids(operation_intent.target_query.host_global_id, target)
    for host_id in host_ids:
        host = _record(records_by_global_id, host_id, role="host")
        facts.append(
            SemanticFact(
                fact_key="relationship:host",
                value=host_id,
                value_type="IfcGloballyUniqueId",
                unit=None,
                inherited=False,
                pset_path=None,
                entity_source=f"{target.ifc_class}:{target_id}",
                source_kind=EvidenceSourceKind.SURVIVING_TARGET,
                source_ref=f"current-relationship:host:{host_id}",
                provenance=(
                    f"operation:{operation_id}",
                    f"resolved-target:{target_id}",
                    f"current-host-relationship:{host_id}",
                ),
            )
        )
        facts.extend(
            _record_facts(
                host,
                operation_id=operation_id,
                source_kind=EvidenceSourceKind.SURVIVING_HOST,
                source_ref=f"current-host:{host_id}",
                authority_provenance=f"formal_host_relationship:{target_id}",
            )
        )

    for authority in resolved_operation.authorized_semantics:
        kind = str(authority.get("kind", ""))
        if kind not in _AUTHORIZED_SEMANTIC_KINDS:
            raise ProductionEvidenceError(
                "UNAUTHORIZED_SEMANTIC_AUTHORITY", f"{operation_id}:{kind}"
            )
        global_id = str(authority.get("global_id", ""))
        record = _record(records_by_global_id, global_id, role=kind)
        if kind == "formal_type_binding":
            if target.type_global_id != global_id:
                raise ProductionEvidenceError("FORMAL_TYPE_BINDING_MISMATCH", global_id)
            source_kind = EvidenceSourceKind.SURVIVING_TYPE
            source_ref = f"formal-type:{global_id}"
            provenance = f"formal_type_binding:{authority.get('provenance', '')}"
        else:
            if authority.get("authorization") != "stored_user_answer":
                raise ProductionEvidenceError("PROTOTYPE_NOT_USER_APPROVED", global_id)
            source_kind = EvidenceSourceKind.APPROVED_PROTOTYPE
            source_ref = f"user-approved-prototype:{global_id}"
            provenance = "user_authorization:stored_user_answer"
        facts.extend(
            _record_facts(
                record,
                operation_id=operation_id,
                source_kind=source_kind,
                source_ref=source_ref,
                authority_provenance=provenance,
            )
        )

    for fact in deterministic_policy_facts:
        if fact.source_kind is EvidenceSourceKind.PRIVATE_ORIGINAL:
            raise ProductionEvidenceError(
                "PRODUCTION_PRIVATE_ORIGINAL_FORBIDDEN", operation_id
            )
        if fact.source_kind is not EvidenceSourceKind.DETERMINISTIC_POLICY:
            raise ProductionEvidenceError("INVALID_POLICY_FACT_SOURCE", operation_id)
        if not any(
            fnmatchcase(fact.fact_key, spec.fact_pattern)
            and EvidenceSourceKind.DETERMINISTIC_POLICY in spec.allowed_sources
            for spec in policy.semantic_facts
        ):
            raise ProductionEvidenceError("UNREGISTERED_POLICY_FACT", fact.fact_key)
        facts.append(_scope_fact(fact, operation_id))

    for fact in facts:
        if fact.source_kind is EvidenceSourceKind.PRIVATE_ORIGINAL:
            raise ProductionEvidenceError(
                "PRODUCTION_PRIVATE_ORIGINAL_FORBIDDEN", operation_id
            )
        if fact.source_kind not in _PRODUCTION_SOURCES:
            raise ProductionEvidenceError(
                "UNAUTHORIZED_PRODUCTION_SOURCE", fact.source_kind.value
            )
    return tuple(sorted(facts, key=_fact_key))


def _request_fact(operation_id: str, intent: AttributeIntent) -> SemanticFact:
    if intent.intent_kind == "pset":
        fact_key = f"pset:{intent.name.removeprefix('pset:')}"
        pset_path = intent.name.removeprefix("pset:")
    elif intent.intent_kind == "material":
        fact_key = f"material:{intent.name.removeprefix('material:')}"
        pset_path = None
    elif intent.intent_kind == "attribute":
        fact_key = f"attribute:{intent.name.removeprefix('attribute:')}"
        pset_path = None
    else:
        raise ProductionEvidenceError("UNSUPPORTED_REQUEST_FACT_KIND", intent.intent_kind)
    return SemanticFact(
        fact_key=fact_key,
        value=intent.value,
        value_type=_value_type(intent.value),
        unit=None,
        inherited=False,
        pset_path=pset_path,
        entity_source=f"request-operation:{operation_id}",
        source_kind=EvidenceSourceKind.EXPLICIT_REQUEST,
        source_ref=intent.source.reference,
        provenance=(
            f"request-source:{intent.source.source_kind}",
            f"request-evidence:{intent.source.reference}",
            f"operation:{operation_id}",
        ),
    )


def _record_facts(
    record: ElementRecord,
    *,
    operation_id: str,
    source_kind: EvidenceSourceKind,
    source_ref: str,
    authority_provenance: str,
) -> tuple[SemanticFact, ...]:
    return tuple(
        SemanticFact(
            **{
                **fact.__dict__,
                "source_ref": source_ref,
                "provenance": (
                    *fact.provenance,
                    authority_provenance,
                    f"operation:{operation_id}",
                ),
            }
        )
        for fact in semantic_facts_from_element_record(
            record,
            source_kind=source_kind,
            source_ref=source_ref,
        )
    )


def _scope_fact(fact: SemanticFact, operation_id: str) -> SemanticFact:
    return SemanticFact(
        **{
            **fact.__dict__,
            "provenance": (*fact.provenance, f"operation:{operation_id}"),
        }
    )


def _select_authority(
    operation_id: str, candidates: tuple[SemanticFact, ...]
) -> tuple[tuple[SemanticFact, ...], tuple[EvidenceConflict, ...]]:
    precedence = {kind: index for index, kind in enumerate(_PRODUCTION_PRECEDENCE)}
    by_key: dict[str, list[SemanticFact]] = {}
    for fact in candidates:
        by_key.setdefault(fact.fact_key, []).append(fact)
    selected: list[SemanticFact] = []
    conflicts: list[EvidenceConflict] = []
    for fact_key in sorted(by_key):
        ordered = sorted(
            by_key[fact_key],
            key=lambda fact: (
                precedence[fact.source_kind],
                fact.source_ref,
                repr(fact.value),
            ),
        )
        winner = ordered[0]
        selected.append(winner)
        for rejected in ordered[1:]:
            if rejected.value != winner.value:
                conflicts.append(
                    EvidenceConflict(
                        operation_id=operation_id,
                        fact_key=fact_key,
                        selected_source=winner.source_kind,
                        rejected_source=rejected.source_kind,
                        selected_ref=winner.source_ref,
                        rejected_ref=rejected.source_ref,
                    )
                )
    return tuple(selected), tuple(conflicts)


def _applicability(
    *,
    operation_id: str,
    policy: Any,
    selected: tuple[SemanticFact, ...],
    verified_absent: frozenset[str],
) -> dict[str, ApplicabilityDecision]:
    decisions: dict[str, ApplicabilityDecision] = {}
    for spec in policy.semantic_facts:
        present = any(fnmatchcase(fact.fact_key, spec.fact_pattern) for fact in selected)
        category = spec.fact_pattern.split(":", 1)[0]
        absence_verified = category in verified_absent
        if present:
            outcome = "evaluable"
        elif spec.applicability is SemanticApplicability.REQUIRED:
            outcome = "not_evaluable"
        elif absence_verified or spec.applicability is SemanticApplicability.INFORMATIONAL:
            outcome = "not_required"
        else:
            outcome = "not_evaluable"
        decisions[spec.check_id] = ApplicabilityDecision(
            check_id=spec.check_id,
            applicability=spec.applicability.value,
            mandatory=(
                spec.applicability is SemanticApplicability.REQUIRED
                or outcome not in {"not_required"}
            ),
            outcome=outcome,
            verified_absence=absence_verified,
            evidence_pointer=f"production-evidence:/{operation_id}/{spec.check_id}",
        )
    return decisions


def _record(
    records: Mapping[str, ElementRecord], global_id: str | None, *, role: str
) -> ElementRecord:
    if not global_id or global_id not in records:
        raise ProductionEvidenceError("MISSING_AUTHORIZED_RECORD", f"{role}:{global_id}")
    record = records[global_id]
    if not record.identity_reliable or record.ifc_global_id != global_id:
        raise ProductionEvidenceError("UNRELIABLE_AUTHORIZED_RECORD", f"{role}:{global_id}")
    return record


def _host_ids(explicit_host: str | None, target: ElementRecord) -> tuple[str, ...]:
    values = set()
    if explicit_host:
        values.add(explicit_host)
    for value in target.facets.get("host_wall_global_ids", ()):
        if value:
            values.add(str(value))
    return tuple(sorted(values))


def _value_type(value: Any) -> str:
    if isinstance(value, bool):
        return "IfcBoolean"
    if isinstance(value, int):
        return "IfcInteger"
    if isinstance(value, float):
        return "IfcReal"
    return "IfcLabel"


def _fact_key(fact: SemanticFact) -> tuple[str, str, str]:
    return fact.fact_key, fact.source_kind.value, fact.source_ref


def _conflict_key(conflict: EvidenceConflict) -> tuple[str, str, str, str]:
    return (
        conflict.operation_id,
        conflict.fact_key,
        conflict.rejected_source.value,
        conflict.rejected_ref,
    )


__all__ = [
    "ApplicabilityDecision",
    "EvidenceConflict",
    "ProductionEvidence",
    "ProductionEvidenceError",
    "build_production_evidence",
]
