"""Deterministic RepairIntent-to-resolved-context boundary.

This module is deliberately Provider-free.  It converts Phase 7 resolution
records into operation-scoped public authority and refuses to manufacture an
identity or semantic authorization when deterministic evidence is incomplete.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace
from typing import Any, Mapping

from .index_models import INDEX_SCHEMA_VERSION, ElementRecord, TypeRecord
from .index_store import IndexRepository
from .indexer import EXTRACTOR_VERSION
from .indexer import normalize_alias
from .repair_intent import OperationIntent, RepairIntent
from .registry import OperationRegistry
from .run_models import thaw_json
from .target_context import TargetContextError, build_target_context
from .target_query import ResolutionResult, resolve_target


RESOLUTION_FLOW_VERSION = "text2ifc/ifc-resolution-flow/0.1"
TYPE_CANDIDATE_MAX = 5
_PUBLIC_TYPE_DIMENSIONS = {
    "width": "width_mm",
    "height": "height_mm",
    "default sill height": "sill_height_mm",
}


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
        }


def resolve_repair_intent(
    intent: RepairIntent,
    repository: IndexRepository,
    *,
    expected_source_sha256: str,
    context_max_bytes: int = 48_000,
    operation_registry: OperationRegistry | None = None,
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
    for operation in intent.operations:
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

    return ResolutionBatch(
        status="resolved",
        operations=tuple(completed),
        source_ifc_sha256=expected_source_sha256,
        model_fingerprint=intent.model_fingerprint,
    )


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
    "resolve_repair_intent",
]
