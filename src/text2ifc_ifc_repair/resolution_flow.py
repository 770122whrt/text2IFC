"""Deterministic RepairIntent-to-resolved-context boundary.

This module is deliberately Provider-free.  It converts Phase 7 resolution
records into operation-scoped public authority and refuses to manufacture an
identity or semantic authorization when deterministic evidence is incomplete.
"""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from dataclasses import dataclass, replace
from typing import Any, Mapping, Protocol

import ifcopenshell.guid

from .index_models import INDEX_SCHEMA_VERSION, ElementRecord, TypeRecord
from .index_store import IndexRepository
from .indexer import EXTRACTOR_VERSION
from .indexer import normalize_alias
from .repair_intent import OperationIntent, PublicProvenance, RepairIntent
from .occurrence_semantics import (
    derive_geometry_assignments,
    expand_semantic_bundles,
    quantity_assignments,
    resolve_occurrence_reuse,
)
from .property_intent import (
    ExactPropertyIntent,
    NaturalLanguagePropertyIntent,
    PropertyConfirmationBatch,
    PropertyConfirmationPreview,
    PropertyResolutionStatus,
    authorize_custom_property,
    authorize_standard_property,
    hash_json,
    normalize_property_scope,
    resolve_exact_property_intent,
)
from .registry import OperationRegistry
from .run_models import thaw_json
from .target_context import TargetContextError, build_target_context
from .target_query import ResolutionResult, resolve_target
from text2ifc_knowledge.registry import IfcKnowledgeRegistry, load_ifc2x3_registry
from text2ifc_knowledge.property_search import (
    PropertyKnowledgeQuery,
    PropertyResolutionDecision,
)


RESOLUTION_FLOW_VERSION = "text2ifc/ifc-resolution-flow/0.1"
TYPE_CANDIDATE_MAX = 5
PROPERTY_CONFIRMATION_EXCERPT_MAX = 160
_PUBLIC_TYPE_DIMENSIONS = {
    "width": "width_mm",
    "height": "height_mm",
    "default sill height": "sill_height_mm",
}


class PropertyKnowledgeResolverProtocol(Protocol):
    def resolve(
        self, query: PropertyKnowledgeQuery
    ) -> PropertyResolutionDecision: ...


@dataclass(frozen=True)
class ResolvedOperation:
    operation_id: str
    operation_type: str
    target_global_id: str | None
    scope_ids: tuple[str, ...]
    evidence_pointers: tuple[str, ...]
    parameters: Mapping[str, Any]
    context: Mapping[str, Any]
    authorized_semantics: tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "target_global_id": self.target_global_id,
            "scope_ids": list(self.scope_ids),
            "evidence_pointers": list(self.evidence_pointers),
            "parameters": thaw_json(self.parameters),
            "context": thaw_json(self.context),
            "authorized_semantics": [thaw_json(item) for item in self.authorized_semantics],
        }


@dataclass(frozen=True)
class ResolutionBatch:
    status: str
    operations: tuple[ResolvedOperation, ...] = ()
    reason_code: str | None = None
    operation_id: str | None = None
    candidates: tuple[dict[str, Any], ...] = ()
    source_ifc_sha256: str | None = None
    model_fingerprint: str | None = None
    property_preview: Mapping[str, Any] | None = None
    property_resolutions: tuple[Mapping[str, Any], ...] = ()
    schema_version: str = RESOLUTION_FLOW_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "reason_code": self.reason_code,
            "operation_id": self.operation_id,
            "source_ifc_sha256": self.source_ifc_sha256,
            "model_fingerprint": self.model_fingerprint,
            "operations": [item.to_dict() for item in self.operations],
            "candidates": [dict(item) for item in self.candidates],
            "property_preview": (
                None if self.property_preview is None else dict(self.property_preview)
            ),
            "property_resolutions": [
                thaw_json(item) for item in self.property_resolutions
            ],
        }


def resolve_repair_intent(
    intent: RepairIntent,
    repository: IndexRepository,
    *,
    expected_source_sha256: str,
    context_max_bytes: int = 48_000,
    operation_registry: OperationRegistry | None = None,
    property_registry: IfcKnowledgeRegistry | None = None,
    property_knowledge_resolver: PropertyKnowledgeResolverProtocol | None = None,
) -> ResolutionBatch:
    """Resolve all operations in stable order or return one fail-closed pause."""

    metadata = repository.metadata
    if (
        metadata.source_ifc_sha256 != expected_source_sha256
        or metadata.index_schema_version != INDEX_SCHEMA_VERSION
        or metadata.extractor_version != EXTRACTOR_VERSION
    ):
        return _failure(intent, "stale_index", source_sha=expected_source_sha256)

    completed: list[ResolvedOperation] = []
    property_evidence: list[Mapping[str, Any]] = []
    pending_property_batches: list[PropertyConfirmationBatch] = []
    for operation in intent.operations:
        try:
            expanded_properties, expanded_quantities = expand_semantic_bundles(
                operation, intent.semantic_bundles
            )
        except ValueError as error:
            return _failure(
                intent,
                str(error),
                operation_id=operation.operation_id,
                operations=completed,
                source_sha=expected_source_sha256,
            )
        operation = replace(
            operation,
            property_intents=expanded_properties,
            quantity_intents=expanded_quantities,
        )
        result = resolve_target(repository, operation.target_query)
        if result.status != "resolved":
            reason = result.status
            if reason == "unsupported":
                return _failure(
                    intent, reason, operation_id=operation.operation_id,
                    operations=completed, source_sha=expected_source_sha256,
                )
            if reason == "not_found" and _has_unreliable_name_match(repository, operation):
                reason = "missing_evidence"
            return ResolutionBatch(
                status="clarification_required",
                reason_code=reason,
                operation_id=operation.operation_id,
                operations=tuple(completed),
                candidates=_public_candidates(repository, result),
                source_ifc_sha256=expected_source_sha256,
                model_fingerprint=intent.model_fingerprint,
            )

        record = _resolved_record(repository, result)
        if record is None or not record.identity_reliable or not record.ifc_global_id:
            return _failure(
                intent,
                "missing_evidence",
                operation_id=operation.operation_id,
                operations=completed,
                source_sha=expected_source_sha256,
            )
        try:
            context = build_target_context(
                repository,
                operation.target_query,
                result,
                max_bytes=context_max_bytes,
                operation_hints=(operation.operation_type,),
            )
        except TargetContextError:
            return _failure(
                intent,
                "context_budget_exceeded",
                operation_id=operation.operation_id,
                operations=completed,
                source_sha=expected_source_sha256,
            )
        context = {
            **context,
            "model_fingerprint": intent.model_fingerprint,
            "model_constraints": {
                **context["model_constraints"],
                "source_ifc_sha256": expected_source_sha256,
            },
        }
        operation_token = _escape_json_pointer_token(operation.operation_id)
        evidence = (
            f"resolved:/operations/{operation_token}/context/candidate_targets/0",
        ) if result.candidates[0].evidence else ()
        if not evidence:
            return _failure(
                intent,
                "missing_evidence",
                operation_id=operation.operation_id,
                operations=completed,
                source_sha=expected_source_sha256,
            )
        semantics: tuple[Mapping[str, Any], ...] = ()
        if record.type_global_id:
            semantics = (
                {
                    "kind": "formal_type_binding",
                    "global_id": record.type_global_id,
                    "provenance": "current_ifc",
                },
            )
        completed.append(
            ResolvedOperation(
                operation_id=operation.operation_id,
                operation_type=operation.operation_type,
                target_global_id=record.ifc_global_id,
                scope_ids=(record.ifc_global_id,),
                evidence_pointers=evidence,
                parameters=operation.parameters,
                context=context,
                authorized_semantics=semantics,
            )
        )

        if intent.schema_version == "text2ifc/ifc-repair-intent/0.4":
            explicit_quantity_assignments = quantity_assignments(
                operation.operation_id, operation.quantity_intents
            )
            explicit_quantity_slots = {
                item.fact_key for item in explicit_quantity_assignments
            }
            occurrence_assignments = [
                *explicit_quantity_assignments,
                *(
                    item
                    for item in derive_geometry_assignments(operation)
                    if item.fact_key not in explicit_quantity_slots
                ),
            ]
            if operation.occurrence_reuse_intent is not None:
                reuse_result = resolve_occurrence_reuse(
                    repository,
                    operation.occurrence_reuse_intent,
                    operation_id=operation.operation_id,
                )
                if reuse_result.status != "resolved":
                    return ResolutionBatch(
                        status="clarification_required",
                        reason_code=reuse_result.reason_code,
                        operation_id=operation.operation_id,
                        operations=tuple(completed),
                        candidates=tuple(
                            dict(item) for item in reuse_result.candidates
                        ),
                        source_ifc_sha256=expected_source_sha256,
                        model_fingerprint=intent.model_fingerprint,
                    )
                occurrence_assignments.extend(reuse_result.assignments)
            if occurrence_assignments:
                completed[-1] = replace(
                    completed[-1],
                    authorized_semantics=(
                        *completed[-1].authorized_semantics,
                        *(item.to_dict() for item in occurrence_assignments),
                    ),
                )

        prototype = operation.prototype_intent
        prototype_classes: tuple[str, ...] = ()
        prototype_dimension_paths: Mapping[str, tuple[str, ...]] = {}
        if operation_registry is not None:
            definition = operation_registry.require(operation.operation_type)
            prototype_classes = definition.prototype_ifc_classes
            prototype_dimension_paths = definition.prototype_dimension_paths
        if prototype is not None and prototype.reference_kind in {"global_id", "type_name"}:
            prototype_result = _explicit_prototype(
                repository,
                prototype,
                operation_id=operation.operation_id,
                source_sha=expected_source_sha256,
                model_fingerprint=intent.model_fingerprint,
                allowed_ifc_classes=prototype_classes,
            )
            if prototype_result[0] == "resolved":
                completed[-1] = replace(
                    completed[-1],
                    authorized_semantics=(*completed[-1].authorized_semantics, prototype_result[1]),
                )
            elif prototype_result[0] == "ambiguous":
                return ResolutionBatch(
                    status="clarification_required", reason_code="prototype_selection",
                    operation_id=operation.operation_id, operations=tuple(completed),
                    candidates=prototype_result[1], source_ifc_sha256=expected_source_sha256,
                    model_fingerprint=intent.model_fingerprint,
                )
            else:
                return _failure(
                    intent, "missing_evidence", operation_id=operation.operation_id,
                    operations=completed, source_sha=expected_source_sha256,
                )
        elif prototype is not None and prototype.reference_kind == "selection_required":
            if not prototype_classes:
                return _failure(
                    intent,
                    "missing_evidence",
                    operation_id=operation.operation_id,
                    operations=completed,
                    source_sha=expected_source_sha256,
                )
            candidates = _type_candidates(
                repository,
                operation_id=operation.operation_id,
                source_sha=expected_source_sha256,
                model_fingerprint=intent.model_fingerprint,
                allowed_ifc_classes=prototype_classes,
                requested_dimensions=_requested_prototype_dimensions(
                    operation.parameters, prototype_dimension_paths
                ),
            )
            if not candidates:
                return _failure(
                    intent,
                    "missing_evidence",
                    operation_id=operation.operation_id,
                    operations=completed,
                    source_sha=expected_source_sha256,
                )
            return ResolutionBatch(
                status="clarification_required",
                reason_code="prototype_selection",
                operation_id=operation.operation_id,
                operations=tuple(completed),
                candidates=candidates,
                source_ifc_sha256=expected_source_sha256,
                model_fingerprint=intent.model_fingerprint,
            )
        elif (
            prototype is None
            and operation_registry is not None
            and operation_registry.require(operation.operation_type).generated_type_template
            is not None
        ):
            authority = generated_type_authority(
                operation_registry.require(operation.operation_type),
                operation_id=operation.operation_id,
                request_hash=intent.source_request_hash,
                model_fingerprint=intent.model_fingerprint,
            )
            completed[-1] = replace(
                completed[-1],
                authorized_semantics=(
                    *completed[-1].authorized_semantics,
                    authority,
                ),
            )
            generated_facts = (
                operation_registry.require(
                    operation.operation_type
                ).generated_occurrence_facts
            )
            if generated_facts is not None:
                completed[-1] = replace(
                    completed[-1],
                    authorized_semantics=(
                        *completed[-1].authorized_semantics,
                        *tuple(generated_facts(target_record=record)),
                    ),
                )

        if operation.property_intents:
            if operation_registry is None:
                return _failure(
                    intent,
                    "PROPERTY_ADAPTER_UNAVAILABLE",
                    operation_id=operation.operation_id,
                    operations=completed,
                    source_sha=expected_source_sha256,
                )
            definition = operation_registry.require(operation.operation_type)
            property_target_class = definition.editable_occurrence_ifc_class
            if (
                property_target_class is None
                and record.ifc_class in definition.editable_occurrence_ifc_classes
            ):
                property_target_class = record.ifc_class
            if property_target_class is None:
                return _failure(
                    intent,
                    "PROPERTY_ADAPTER_UNAVAILABLE",
                    operation_id=operation.operation_id,
                    operations=completed,
                    source_sha=expected_source_sha256,
                )
            knowledge = property_registry or load_ifc2x3_registry()
            custom_previews: list[PropertyConfirmationPreview] = []
            for property_intent in operation.property_intents:
                try:
                    normalize_property_scope(property_intent.scope)
                except ValueError as error:
                    return _failure(
                        intent,
                        str(error),
                        operation_id=operation.operation_id,
                        operations=completed,
                        source_sha=expected_source_sha256,
                    )
                exact_intent = property_intent
                if isinstance(property_intent, NaturalLanguagePropertyIntent):
                    if property_knowledge_resolver is None:
                        return _failure(
                            intent,
                            "PROPERTY_KNOWLEDGE_RESOLVER_UNAVAILABLE",
                            operation_id=operation.operation_id,
                            operations=completed,
                            source_sha=expected_source_sha256,
                        )
                    knowledge_decision = property_knowledge_resolver.resolve(
                        PropertyKnowledgeQuery(
                            target_ifc_class=property_target_class,
                            phrase=str(property_intent.property_phrase),
                            raw_value=property_intent.raw_value,
                            raw_unit=property_intent.raw_unit,
                            scope=property_intent.scope,
                        )
                    )
                    evidence_document = _property_resolution_evidence(
                        operation.operation_id,
                        property_intent,
                        property_target_class,
                        knowledge_decision,
                    )
                    property_evidence.append(evidence_document)
                    if knowledge_decision.exact_intent is None:
                        return ResolutionBatch(
                            status="clarification_required",
                            reason_code=knowledge_decision.reason_code,
                            operation_id=operation.operation_id,
                            operations=tuple(completed),
                            source_ifc_sha256=expected_source_sha256,
                            model_fingerprint=intent.model_fingerprint,
                            property_resolutions=tuple(property_evidence),
                        )
                    resolved = knowledge_decision.exact_intent
                    exact_intent = ExactPropertyIntent(
                        set_name=resolved.set_name,
                        property_name=resolved.property_name,
                        value=resolved.value,
                        requested_value_type=resolved.requested_value_type,
                        requested_unit=resolved.requested_unit,
                        scope=resolved.scope,
                        source=property_intent.source,
                        intent_kind="exact_property",
                    )
                property_resolution = resolve_exact_property_intent(
                    exact_intent,
                    target_ifc_class=property_target_class,
                    existing_facts=(),
                    registry=knowledge,
                )
                if (
                    property_resolution.status
                    is PropertyResolutionStatus.CLARIFICATION_REQUIRED
                ):
                    return ResolutionBatch(
                        status="clarification_required",
                        reason_code=str(property_resolution.reason_code),
                        operation_id=operation.operation_id,
                        operations=tuple(completed),
                        source_ifc_sha256=expected_source_sha256,
                        model_fingerprint=intent.model_fingerprint,
                    )
                if (
                    property_resolution.status
                    is PropertyResolutionStatus.CUSTOM_CONFIRMATION_REQUIRED
                ):
                    custom_previews.append(
                        PropertyConfirmationPreview.create(
                            property_resolution,
                            operation_id=operation.operation_id,
                            target_global_id=record.ifc_global_id,
                            request_hash=intent.source_request_hash,
                            model_fingerprint=intent.model_fingerprint,
                            source=_bounded_confirmation_source(
                                exact_intent.source
                            ),
                        )
                    )
                    continue
                fact = authorize_standard_property(
                    property_resolution,
                    operation_id=operation.operation_id,
                    target_global_id=record.ifc_global_id,
                    request_hash=intent.source_request_hash,
                    model_fingerprint=intent.model_fingerprint,
                    source=exact_intent.source,
                )
                completed[-1] = replace(
                    completed[-1],
                    authorized_semantics=(
                        *completed[-1].authorized_semantics,
                        fact.to_dict(),
                    ),
                )
            if custom_previews:
                pending_property_batches.append(
                    PropertyConfirmationBatch.create(custom_previews)
                )

    if pending_property_batches:
        if len(pending_property_batches) == 1:
            batch = pending_property_batches[0]
            preview_document = (
                batch.items[0].to_dict()
                if len(batch.items) == 1
                else batch.to_dict()
            )
        else:
            preview_document = _property_transaction_preview(
                pending_property_batches
            )
        return ResolutionBatch(
            status="clarification_required",
            reason_code="property_confirmation",
            operation_id=pending_property_batches[0].operation_id,
            operations=tuple(completed),
            source_ifc_sha256=expected_source_sha256,
            model_fingerprint=intent.model_fingerprint,
            property_preview=preview_document,
            property_resolutions=tuple(property_evidence),
        )

    return ResolutionBatch(
        status="resolved",
        operations=tuple(completed),
        source_ifc_sha256=expected_source_sha256,
        model_fingerprint=intent.model_fingerprint,
        property_resolutions=tuple(property_evidence),
    )


def _property_resolution_evidence(
    operation_id: str,
    claim: NaturalLanguagePropertyIntent,
    target_ifc_class: str,
    decision: PropertyResolutionDecision,
) -> dict[str, Any]:
    return {
        "operation_id": operation_id,
        "query": {
            "schema_version": "text2ifc/property-knowledge-query/0.1",
            "target_ifc_class": target_ifc_class,
            "property_phrase": claim.property_phrase,
            "raw_value": claim.raw_value,
            "raw_unit": claim.raw_unit,
            "scope": claim.scope,
            "source": claim.source.to_dict(),
        },
        "candidates": [
            {
                "record_id": item.record.record_id,
                "authority": item.record.authority,
                "canonical_path": item.record.canonical_path,
                "retrieval_paths": list(item.retrieval_paths),
                "keyword_score": item.keyword_score,
                "vector_score": item.vector_score,
                "source_ref": item.record.source_ref,
                "source_hash": item.record.source_hash,
            }
            for item in decision.candidates
        ],
        "decision": {
            "schema_version": decision.schema_version,
            "status": decision.status,
            "reason_code": decision.reason_code,
            "exact_intent": (
                None
                if decision.exact_intent is None
                else {
                    "set_name": decision.exact_intent.set_name,
                    "property_name": decision.exact_intent.property_name,
                    "value": decision.exact_intent.value,
                    "requested_value_type": (
                        decision.exact_intent.requested_value_type
                    ),
                    "requested_unit": decision.exact_intent.requested_unit,
                    "scope": decision.exact_intent.scope,
                }
            ),
        },
    }


def authorize_prototype(
    batch: ResolutionBatch,
    *,
    operation_id: str,
    candidate_token: str,
    authorized: bool,
) -> ResolutionBatch:
    """Attach only an explicit, offered, affirmative Prototype authorization."""

    if batch.status != "clarification_required" or batch.reason_code != "prototype_selection":
        raise ValueError("PROTOTYPE_AUTHORIZATION_NOT_PENDING")
    if not authorized:
        raise ValueError("PROTOTYPE_AUTHORIZATION_REQUIRED")
    candidate = next((item for item in batch.candidates if item["token"] == candidate_token), None)
    if (
        candidate is None
        or candidate.get("candidate_kind") != "type"
        or operation_id != batch.operation_id
    ):
        raise ValueError("PROTOTYPE_CANDIDATE_NOT_OFFERED")
    updated: list[ResolvedOperation] = []
    for operation in batch.operations:
        if operation.operation_id == operation_id:
            semantics = (*operation.authorized_semantics, {
                "kind": "user_authorized_prototype",
                "global_id": candidate["public_id"],
                "authorization": "stored_user_answer",
            })
            operation = replace(operation, authorized_semantics=semantics)
        updated.append(operation)
    return replace(
        batch,
        status="resolved",
        reason_code=None,
        operation_id=None,
        operations=tuple(updated),
        candidates=(),
    )


def _failure(
    intent: RepairIntent,
    reason: str,
    *,
    operation_id: str | None = None,
    operations: list[ResolvedOperation] | None = None,
    source_sha: str,
) -> ResolutionBatch:
    return ResolutionBatch(
        status="failed",
        reason_code=reason,
        operation_id=operation_id,
        operations=tuple(operations or ()),
        source_ifc_sha256=source_sha,
        model_fingerprint=intent.model_fingerprint,
    )


def _resolved_record(repository: IndexRepository, result: ResolutionResult) -> ElementRecord | None:
    return next(
        (record for record in repository.iter_records() if record.record_id == result.resolved_target_id),
        None,
    )


def _has_unreliable_name_match(repository: IndexRepository, operation: OperationIntent) -> bool:
    requested = {name.casefold() for name in operation.target_query.names}
    return bool(requested) and any(
        not record.identity_reliable and (record.name or "").casefold() in requested
        for record in repository.iter_records()
    )


def _public_candidates(
    repository: IndexRepository, result: ResolutionResult
) -> tuple[dict[str, Any], ...]:
    records = {record.record_id: record for record in repository.iter_records()}
    return tuple(
        _public_record(records[hit.record_id], "target")
        for hit in result.candidates
        if hit.record_id in records and records[hit.record_id].identity_reliable
    )


def _public_record(record: ElementRecord, operation_id: str) -> dict[str, Any]:
    public_id = str(record.ifc_global_id)
    token = hashlib.sha256(f"{operation_id}:{public_id}".encode("utf-8")).hexdigest()[:24]
    evidence = [
        f"identity:{public_id}",
        f"class:{record.ifc_class}",
    ]
    if record.name:
        evidence.append(f"name:{record.name}")
    if record.storey_name:
        evidence.append(f"storey:{record.storey_name}")
    return {
        "token": token,
        "public_id": public_id,
        "ifc_class": record.ifc_class,
        "name": record.name,
        "storey": record.storey_name,
        "position": json.dumps(record.geometry_summary, ensure_ascii=False, sort_keys=True),
        "evidence": evidence,
    }


def _escape_json_pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _bounded_confirmation_source(
    source: PublicProvenance,
) -> PublicProvenance:
    """Bound repeated UI excerpts while retaining immutable source identity."""

    excerpt = " ".join(source.excerpt.split())
    if len(excerpt) > PROPERTY_CONFIRMATION_EXCERPT_MAX:
        excerpt = excerpt[: PROPERTY_CONFIRMATION_EXCERPT_MAX - 1].rstrip() + "…"
    return PublicProvenance(
        source_kind=source.source_kind,
        reference=source.reference,
        excerpt=excerpt,
    )


def _explicit_prototype(
    repository: IndexRepository,
    prototype: Any,
    *,
    operation_id: str,
    source_sha: str,
    model_fingerprint: str,
    allowed_ifc_classes: tuple[str, ...] = (),
) -> tuple[str, Any]:
    if prototype.reference_kind == "global_id":
        match = repository.get_type_by_global_id(prototype.reference)
        matches = [match] if match is not None else []
        lookup_kind = "type_global_id"
    else:
        matches = repository.find_type_aliases(normalize_alias(prototype.reference))
        lookup_kind = "type_name"
    matches = [
        item
        for item in matches
        if item.identity_reliable
        and item.ifc_global_id
        and (not allowed_ifc_classes or item.ifc_class in allowed_ifc_classes)
    ]
    if len(matches) == 1:
        return "resolved", {
            "kind": "user_authorized_prototype",
            "global_id": matches[0].ifc_global_id,
            "authorization": "explicit_request_reference",
            "prototype_lookup": lookup_kind,
            "request_provenance": prototype.source.to_dict(),
        }
    if len(matches) > 1:
        candidates = tuple(
            _public_type_record(
                repository,
                item,
                operation_id=operation_id,
                source_sha=source_sha,
                model_fingerprint=model_fingerprint,
            )
            for item in matches[:TYPE_CANDIDATE_MAX]
        )
        return "ambiguous", candidates
    return "not_found", ()


def _type_candidates(
    repository: IndexRepository,
    *,
    operation_id: str,
    source_sha: str,
    model_fingerprint: str,
    allowed_ifc_classes: tuple[str, ...],
    requested_dimensions: Mapping[str, float],
) -> tuple[dict[str, Any], ...]:
    records = sorted(
        (
            item
            for item in repository.iter_type_records()
            if item.identity_reliable and item.ifc_global_id
            and item.ifc_class in allowed_ifc_classes
            and _dimensions_match(
                _type_dimensions(item), requested_dimensions
            )
        ),
        key=lambda item: (item.ifc_class, item.name or "", item.ifc_global_id or ""),
    )
    return tuple(
        _public_type_record(
            repository,
            item,
            operation_id=operation_id,
            source_sha=source_sha,
            model_fingerprint=model_fingerprint,
        )
        for item in records[:TYPE_CANDIDATE_MAX]
    )


def authorize_property_confirmation(
    batch: ResolutionBatch,
    *,
    operation_id: str,
    answer_kind: str,
    preview_hash: str,
    confirmation_ref: str,
) -> ResolutionBatch:
    if (
        batch.status != "clarification_required"
        or batch.reason_code != "property_confirmation"
        or batch.property_preview is None
        or operation_id != batch.operation_id
    ):
        raise ValueError("PROPERTY_CONFIRMATION_NOT_PENDING")
    if batch.property_preview.get("preview_kind") == "property_transaction":
        transaction = _validate_property_transaction_preview(
            batch.property_preview
        )
        if answer_kind != "confirm_property":
            raise ValueError("PROPERTY_CONFIRMATION_REQUIRED")
        if preview_hash != transaction["preview_hash"]:
            raise ValueError("PROPERTY_CONFIRMATION_HASH_MISMATCH")
        facts_by_operation: dict[str, tuple[Any, ...]] = {}
        for preview_batch in transaction["batches"]:
            facts_by_operation[preview_batch.operation_id] = tuple(
                authorize_custom_property(
                    preview,
                    answer_kind=answer_kind,
                    preview_hash=preview.preview_hash,
                    confirmation_ref=confirmation_ref,
                )
                for preview in preview_batch.items
            )
        operations = tuple(
            replace(
                operation,
                authorized_semantics=(
                    *operation.authorized_semantics,
                    *(
                        fact.to_dict()
                        for fact in facts_by_operation.get(
                            operation.operation_id, ()
                        )
                    ),
                ),
            )
            for operation in batch.operations
        )
        return replace(
            batch,
            status="resolved",
            reason_code=None,
            operation_id=None,
            operations=operations,
            property_preview=None,
        )
    if batch.property_preview.get("preview_kind") == "property_batch":
        preview_batch = PropertyConfirmationBatch.from_dict(batch.property_preview)
        if answer_kind != "confirm_property":
            raise ValueError("PROPERTY_CONFIRMATION_REQUIRED")
        if preview_hash != preview_batch.preview_hash:
            raise ValueError("PROPERTY_CONFIRMATION_HASH_MISMATCH")
        facts = tuple(
            authorize_custom_property(
                preview,
                answer_kind=answer_kind,
                preview_hash=preview.preview_hash,
                confirmation_ref=confirmation_ref,
            )
            for preview in preview_batch.items
        )
    else:
        preview = PropertyConfirmationPreview.from_dict(batch.property_preview)
        facts = (
            authorize_custom_property(
                preview,
                answer_kind=answer_kind,
                preview_hash=preview_hash,
                confirmation_ref=confirmation_ref,
            ),
        )
    operations = tuple(
        replace(
            operation,
            authorized_semantics=(
                *operation.authorized_semantics,
                *(fact.to_dict() for fact in facts),
            ),
        )
        if operation.operation_id == operation_id
        else operation
        for operation in batch.operations
    )
    return replace(
        batch,
        status="resolved",
        reason_code=None,
        operation_id=None,
        operations=operations,
        property_preview=None,
    )


def _property_transaction_preview(
    batches: list[PropertyConfirmationBatch],
) -> dict[str, Any]:
    if not 2 <= len(batches) <= 16:
        raise ValueError("PROPERTY_TRANSACTION_SIZE_INVALID")
    operation_ids = [item.operation_id for item in batches]
    if len(operation_ids) != len(set(operation_ids)):
        raise ValueError("PROPERTY_TRANSACTION_DUPLICATE_OPERATION")
    request_hashes = {item.request_hash for item in batches}
    model_fingerprints = {item.model_fingerprint for item in batches}
    if len(request_hashes) != 1 or len(model_fingerprints) != 1:
        raise ValueError("PROPERTY_TRANSACTION_BINDING_MISMATCH")
    canonical = {
        "preview_kind": "property_transaction",
        "request_hash": next(iter(request_hashes)),
        "model_fingerprint": next(iter(model_fingerprints)),
        "batch_hashes": [item.preview_hash for item in batches],
    }
    return {
        **canonical,
        "batches": [item.to_dict() for item in batches],
        "preview_hash": hash_json(canonical),
    }


def _validate_property_transaction_preview(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    if value.get("preview_kind") != "property_transaction":
        raise ValueError("PROPERTY_TRANSACTION_KIND_INVALID")
    batches = [
        PropertyConfirmationBatch.from_dict(item)
        for item in value.get("batches", ())
    ]
    rebuilt = _property_transaction_preview(batches)
    if dict(value) != rebuilt:
        raise ValueError("PROPERTY_TRANSACTION_HASH_MISMATCH")
    return {**rebuilt, "batches": batches}


def generated_type_authority(
    definition: Any,
    *,
    operation_id: str,
    request_hash: str,
    model_fingerprint: str,
) -> dict[str, Any]:
    """Create operation-bound authority without inspecting project Types."""

    builder = getattr(definition, "generated_type_template", None)
    if builder is None:
        raise ValueError("GENERATED_TYPE_TEMPLATE_UNAVAILABLE")
    template = dict(
        builder(
            operation_id=operation_id,
            request_hash=request_hash,
            model_fingerprint=model_fingerprint,
        )
    )
    template_id = str(
        template.pop(
            "template_id",
            f"{definition.operation_type}.generated-type",
        )
    )
    template_version = str(template.pop("template_version"))
    ifc_class = str(template.pop("ifc_class"))
    formal_attributes = {
        str(key): template[key]
        for key in sorted(template)
        if key
        in {
            "construction_type",
            "operation_type",
            "parameter_takes_precedence",
            "sizeable",
        }
    }
    template_digest = hash_json(
        {
            "template_id": template_id,
            "template_version": template_version,
            "ifc_class": ifc_class,
            "formal_attributes": formal_attributes,
            "template": template,
        }
    )
    canonical = json.dumps(
        {
            "operation_id": operation_id,
            "request_hash": request_hash,
            "model_fingerprint": model_fingerprint,
            "template_version": template_version,
            "template_id": template_id,
            "ifc_class": ifc_class,
            "template_digest": template_digest,
            "template": template,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    value = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"https://text2ifc.local/ifc-repair/generated-type/{canonical}",
    )
    return {
        "kind": "system_generated_type",
        "global_id": ifcopenshell.guid.compress(value.hex),
        "ifc_class": ifc_class,
        "template_id": template_id,
        "template_version": template_version,
        "template_digest": template_digest,
        "formal_attributes": formal_attributes,
        "authorization": "deterministic_policy",
        "operation_id": operation_id,
        "template": template,
    }


def _public_type_record(
    repository: IndexRepository,
    record: TypeRecord,
    *,
    operation_id: str,
    source_sha: str,
    model_fingerprint: str,
) -> dict[str, Any]:
    public_id = str(record.ifc_global_id)
    token_input = f"{operation_id}:{public_id}:{source_sha}:{model_fingerprint}"
    token = hashlib.sha256(token_input.encode("utf-8")).hexdigest()[:24]
    dimensions = _type_dimensions(record)
    occurrence_count, storeys = repository.type_occurrence_summary(public_id)
    evidence = [f"identity:{public_id}", f"class:{record.ifc_class}"]
    if record.name:
        evidence.append(f"name:{record.name}")
    for key in sorted(dimensions):
        evidence.append(f"dimension:{key}:{dimensions[key]}")
    evidence.append(f"occurrences:{occurrence_count}")
    evidence.extend(f"storey:{storey}" for storey in storeys)
    return {
        "candidate_kind": "type",
        "token": token,
        "public_id": public_id,
        "ifc_class": record.ifc_class,
        "name": record.name,
        "dimensions": {key: dimensions[key] for key in sorted(dimensions)},
        "occurrence_count": occurrence_count,
        "storeys": list(storeys),
        "evidence": evidence,
    }


def _requested_prototype_dimensions(
    parameters: Mapping[str, Any],
    paths: Mapping[str, tuple[str, ...]],
) -> dict[str, float]:
    dimensions: dict[str, float] = {}
    for public_name, path in paths.items():
        value: Any = parameters
        for part in path:
            if not isinstance(value, Mapping) or part not in value:
                value = None
                break
            value = value[part]
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            dimensions[public_name] = float(value)
    return dimensions


def _type_dimensions(record: TypeRecord) -> dict[str, float]:
    dimensions: dict[str, float] = {}
    for fact in record.properties:
        if fact.set_kind != "pset" or fact.set_name.casefold() != "dimensions":
            continue
        key = _PUBLIC_TYPE_DIMENSIONS.get(fact.property_name.casefold())
        if key is not None and isinstance(fact.value, (int, float)):
            dimensions[key] = float(fact.value)
    return dimensions


def _dimensions_match(
    candidate: Mapping[str, float], requested: Mapping[str, float]
) -> bool:
    return all(
        key in candidate
        and math.isclose(candidate[key], value, rel_tol=0.0, abs_tol=1e-6)
        for key, value in requested.items()
    )


__all__ = [
    "RESOLUTION_FLOW_VERSION",
    "ResolutionBatch",
    "ResolvedOperation",
    "authorize_prototype",
    "authorize_property_confirmation",
    "generated_type_authority",
    "resolve_repair_intent",
]
