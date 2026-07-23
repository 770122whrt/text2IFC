"""Production-only semantic authority construction for Evaluation 0.2.

This module deliberately has no benchmark input type.  It turns an already
validated RepairIntent, deterministic resolution, public current-IFC records,
and registered operation policy into operation-owned expected facts.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fnmatch import fnmatchcase
from types import MappingProxyType
from typing import Any, Mapping

from .evaluation_policy import (
    EvidenceSourceKind,
    SemanticApplicability,
    extend_policy_with_explicit_facts,
    normalize_policy_fact_key,
)
from .run_models import hash_json
from .index_models import ElementRecord, TypeRecord
from .registry import OperationRegistry
from .repair_intent import AttributeIntent, RepairIntent
from .resolution_flow import ResolutionBatch, ResolvedOperation
from .semantic_facts import (
    SemanticFact,
    semantic_facts_from_element_record,
    semantic_facts_from_type_record,
)


_PRODUCTION_PRECEDENCE = (
    EvidenceSourceKind.EXPLICIT_REQUEST,
    EvidenceSourceKind.SURVIVING_TARGET,
    EvidenceSourceKind.SURVIVING_HOST,
    EvidenceSourceKind.SURVIVING_TYPE,
    EvidenceSourceKind.AUTHORIZED_TYPE_COHORT,
    EvidenceSourceKind.APPROVED_PROTOTYPE,
    EvidenceSourceKind.DETERMINISTIC_POLICY,
)
_PRODUCTION_SOURCES = frozenset(_PRODUCTION_PRECEDENCE)
_AUTHORIZED_SEMANTIC_KINDS = frozenset(
    {
        "formal_type_binding",
        "user_authorized_prototype",
        "system_generated_type",
        "authorized_property_fact",
    }
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
    type_records_by_global_id: Mapping[str, TypeRecord],
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
            type_records_by_global_id=type_records_by_global_id,
            deterministic_policy_facts=tuple(policy_facts.get(operation_id, ())),
            policy=policy,
            request_hash=intent.source_request_hash,
            model_fingerprint=intent.model_fingerprint,
        )
        selected, operation_conflicts = _select_authority(operation_id, candidates)
        policy = extend_policy_with_explicit_facts(
            policy,
            tuple(
                fact.fact_key
                for fact in selected
                if fact.source_kind is EvidenceSourceKind.EXPLICIT_REQUEST
            ),
            applicability=SemanticApplicability.REQUIRED,
        )
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
    type_records_by_global_id: Mapping[str, TypeRecord],
    deterministic_policy_facts: tuple[SemanticFact, ...],
    policy: Any,
    request_hash: str,
    model_fingerprint: str,
) -> tuple[SemanticFact, ...]:
    facts: list[SemanticFact] = [
        _request_fact(operation_id, item) for item in operation_intent.attribute_intents
    ]
    target_id = resolved_operation.target_global_id
    target = _record(records_by_global_id, target_id, role="target")
    if policy.target_authority_mode == "host_for_created_entity":
        facts.append(
            SemanticFact(
                fact_key="relationship:host",
                value=target_id,
                value_type=target.ifc_class,
                unit=None,
                inherited=False,
                pset_path=None,
                entity_source=f"{target.ifc_class}:{target_id}",
                source_kind=EvidenceSourceKind.SURVIVING_TARGET,
                source_ref=f"current-target:{target_id}",
                provenance=(f"resolved-host-target:{target_id}", f"operation:{operation_id}"),
            )
        )
        if target.storey_global_id:
            facts.append(
                SemanticFact(
                    fact_key="relationship:storey",
                    value=target.storey_global_id,
                    value_type="IfcBuildingStorey",
                    unit=None,
                    inherited=False,
                    pset_path=None,
                    entity_source=f"{target.ifc_class}:{target_id}",
                    source_kind=EvidenceSourceKind.SURVIVING_TARGET,
                    source_ref=f"current-target-storey:{target.storey_global_id}",
                    provenance=(f"resolved-host-target:{target_id}", f"operation:{operation_id}"),
                )
            )
    else:
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
        if kind == "authorized_property_fact":
            facts.append(
                _authorized_property_fact(
                    authority,
                    operation_id=operation_id,
                    operation_intent=operation_intent,
                    resolved_operation=resolved_operation,
                    request_hash=request_hash,
                    model_fingerprint=model_fingerprint,
                )
            )
            continue
        global_id = str(authority.get("global_id", ""))
        if kind == "system_generated_type":
            if (
                authority.get("authorization") != "deterministic_policy"
                or authority.get("operation_id") != operation_id
                or not global_id
            ):
                raise ProductionEvidenceError(
                    "GENERATED_TYPE_AUTHORITY_INVALID", operation_id
                )
            facts.append(
                SemanticFact(
                    fact_key="relationship:type",
                    value=global_id,
                    value_type=str(authority.get("ifc_class") or "IfcTypeObject"),
                    unit=None,
                    inherited=True,
                    pset_path=None,
                    entity_source=f"generated-type:{global_id}",
                    source_kind=EvidenceSourceKind.DETERMINISTIC_POLICY,
                    source_ref=f"generated-type:{global_id}",
                    provenance=(
                        f"operation:{operation_id}",
                        f"generated-type-template:{authority.get('template_version')}",
                    ),
                )
            )
            continue
        if kind == "formal_type_binding":
            if (
                policy.target_authority_mode == "edited_entity"
                and target.type_global_id != global_id
            ):
                raise ProductionEvidenceError("FORMAL_TYPE_BINDING_MISMATCH", global_id)
            source_kind = EvidenceSourceKind.SURVIVING_TYPE
            source_ref = f"formal-type:{global_id}"
            provenance = f"formal_type_binding:{authority.get('provenance', '')}"
        else:
            authorization = str(authority.get("authorization", ""))
            if authorization not in {"stored_user_answer", "explicit_request_reference"}:
                raise ProductionEvidenceError("PROTOTYPE_NOT_USER_APPROVED", global_id)
            source_kind = EvidenceSourceKind.APPROVED_PROTOTYPE
            source_ref = f"user-approved-prototype:{global_id}"
            provenance = f"user_authorization:{authorization}"
        type_record = _type_record(
            type_records_by_global_id, global_id, role=kind
        )
        created_type_authority = (
            policy.target_authority_mode == "host_for_created_entity"
            and kind == "user_authorized_prototype"
        ) or (
            policy.target_authority_mode == "edited_entity"
            and kind == "formal_type_binding"
        )
        if (
            policy.target_authority_mode == "host_for_created_entity"
            and kind == "formal_type_binding"
        ):
            continue
        facts.extend(
            _authorized_type_facts(
                type_record,
                operation_id=operation_id,
                source_kind=source_kind,
                source_ref=source_ref,
                authority_provenance=provenance,
            )
        )
        if created_type_authority:
            facts.append(
                SemanticFact(
                    fact_key="relationship:type",
                    value=global_id,
                    value_type=type_record.ifc_class,
                    unit=None,
                    inherited=True,
                    pset_path=None,
                    entity_source=f"{type_record.ifc_class}:{global_id}",
                    source_kind=source_kind,
                    source_ref=source_ref,
                    provenance=(provenance, f"operation:{operation_id}"),
                )
            )
            facts.extend(
                _authorized_type_cohort_facts(
                    type_global_id=global_id,
                    records_by_global_id=records_by_global_id,
                    operation_id=operation_id,
                    policy=policy,
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


def _authorized_property_fact(
    authority: Mapping[str, Any],
    *,
    operation_id: str,
    operation_intent: Any,
    resolved_operation: ResolvedOperation,
    request_hash: str,
    model_fingerprint: str,
) -> SemanticFact:
    supplied_hash = str(authority.get("property_hash", ""))
    expected_hash = hash_json(
        {
            str(key): value
            for key, value in authority.items()
            if key != "property_hash"
        }
    )
    if supplied_hash != expected_hash:
        raise ProductionEvidenceError(
            "AUTHORIZED_PROPERTY_HASH_MISMATCH", operation_id
        )
    if (
        authority.get("operation_id") != operation_id
        or authority.get("target_global_id") != resolved_operation.target_global_id
        or authority.get("ownership") != "occurrence_direct"
        or authority.get("request_hash") != request_hash
        or authority.get("model_fingerprint") != model_fingerprint
    ):
        raise ProductionEvidenceError(
            "AUTHORIZED_PROPERTY_BINDING_MISMATCH", operation_id
        )
    matching = [
        claim
        for claim in operation_intent.property_intents
        if claim.set_name == authority.get("set_name")
        and claim.property_name == authority.get("property_name")
        and claim.value == authority.get("value")
        and (claim.scope or "occurrence_direct") == authority.get("ownership")
    ]
    if len(matching) != 1:
        raise ProductionEvidenceError(
            "AUTHORIZED_PROPERTY_CLAIM_MISMATCH", operation_id
        )
    claim = matching[0]
    return SemanticFact(
        fact_key=f"pset:{authority['set_name']}.{authority['property_name']}",
        value=authority["value"],
        value_type=str(authority["value_type"]),
        unit=None if authority.get("unit") is None else str(authority["unit"]),
        inherited=False,
        pset_path=f"{authority['set_name']}.{authority['property_name']}",
        entity_source=f"request-operation:{operation_id}",
        source_kind=EvidenceSourceKind.EXPLICIT_REQUEST,
        source_ref=claim.source.reference,
        provenance=(
            f"request-source:{claim.source.source_kind}",
            f"request-evidence:{claim.source.reference}",
            f"operation:{operation_id}",
            f"property-hash:{supplied_hash}",
            *(
                (f"confirmation:{authority['confirmation_ref']}",)
                if authority.get("confirmation_ref")
                else ()
            ),
        ),
    )


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
                "source_ref": (
                    fact.source_ref
                    if fact.fact_key.startswith(("material:", "classification:"))
                    else source_ref
                ),
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


def _authorized_type_facts(
    record: TypeRecord,
    *,
    operation_id: str,
    source_kind: EvidenceSourceKind,
    source_ref: str,
    authority_provenance: str,
) -> tuple[SemanticFact, ...]:
    converted = semantic_facts_from_type_record(
        record, source_kind=source_kind, source_ref=source_ref
    )
    values_by_key: dict[str, set[str]] = {}
    for fact in converted:
        values_by_key.setdefault(fact.fact_key, set()).add(repr(fact.value))
    conflicting = sorted(key for key, values in values_by_key.items() if len(values) > 1)
    if conflicting:
        raise ProductionEvidenceError(
            "PROTOTYPE_TYPE_FACT_CONFLICT",
            f"{record.ifc_global_id}:{conflicting[0]}",
        )
    return tuple(
        SemanticFact(
            **{
                **fact.__dict__,
                "source_ref": (
                    fact.source_ref
                    if fact.fact_key.startswith(("material:", "classification:"))
                    else source_ref
                ),
                "provenance": (
                    *fact.provenance,
                    f"type_record:{record.ifc_global_id}",
                    authority_provenance,
                    f"operation:{operation_id}",
                ),
            }
        )
        for fact in sorted(converted, key=_fact_key)
    )


def _authorized_type_cohort_facts(
    *,
    type_global_id: str,
    records_by_global_id: Mapping[str, ElementRecord],
    operation_id: str,
    policy: Any,
) -> tuple[SemanticFact, ...]:
    """Promote only conflict-free, policy-authorized facts from the bound Type cohort."""

    patterns = tuple(policy.cohort_fact_patterns)
    if not patterns:
        return ()
    candidates: list[SemanticFact] = []
    for record in sorted(records_by_global_id.values(), key=lambda item: item.record_id):
        if record.type_global_id != type_global_id:
            continue
        for fact in semantic_facts_from_element_record(
            record,
            source_kind=EvidenceSourceKind.AUTHORIZED_TYPE_COHORT,
            source_ref=f"type-cohort:{type_global_id}",
        ):
            if fact.inherited:
                continue
            try:
                normalization = normalize_policy_fact_key(policy, fact.fact_key)
            except ValueError:
                continue
            normalized_key = normalization.fact_key
            if not any(fnmatchcase(normalized_key, pattern) for pattern in patterns):
                continue
            candidates.append(
                replace(
                    fact,
                    fact_key=normalized_key,
                    provenance=(
                        *fact.provenance,
                        f"source_fact_key:{normalization.source_fact_key}",
                        f"cohort-type:{type_global_id}",
                        f"cohort-record:{record.record_id}",
                        f"operation:{operation_id}",
                    ),
                )
            )

    by_key: dict[str, list[SemanticFact]] = {}
    for fact in candidates:
        by_key.setdefault(fact.fact_key, []).append(fact)
    selected: list[SemanticFact] = []
    for fact_key in sorted(by_key):
        values = {
            (repr(fact.value), fact.value_type, fact.unit)
            for fact in by_key[fact_key]
        }
        if len(values) > 1:
            raise ProductionEvidenceError(
                "AUTHORIZED_TYPE_COHORT_CONFLICT",
                f"{type_global_id}:{fact_key}",
            )
        representative = sorted(by_key[fact_key], key=_fact_key)[0]
        selected.append(
            replace(
                representative,
                provenance=tuple(
                    sorted(
                        {
                            item
                            for fact in by_key[fact_key]
                            for item in fact.provenance
                        }
                    )
                ),
            )
        )
    return tuple(selected)


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
        absence_verified = (
            category in verified_absent
            or spec.check_id in verified_absent
            or spec.fact_pattern in verified_absent
        )
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


def _type_record(
    records: Mapping[str, TypeRecord], global_id: str, *, role: str
) -> TypeRecord:
    if not global_id or global_id not in records:
        raise ProductionEvidenceError("PROTOTYPE_TYPE_NOT_INDEXED", f"{role}:{global_id}")
    record = records[global_id]
    if not record.identity_reliable or record.ifc_global_id != global_id:
        raise ProductionEvidenceError("UNRELIABLE_AUTHORIZED_TYPE", f"{role}:{global_id}")
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
