from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from .index_models import ElementRecord, PropertyFact
from .index_store import IndexRepository
from .target_query import ResolutionResult, TargetQuery


TARGET_CONTEXT_SCHEMA_VERSION = "text2ifc/ifc-target-context/0.1"
NORMAL_MAX_CANDIDATES = 5
DIAGNOSTIC_MAX_CANDIDATES = 10


class TargetContextError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def build_target_context(
    repository: IndexRepository,
    query: TargetQuery,
    result: ResolutionResult,
    *,
    operation_hints: Sequence[str] = (),
    diagnostic: bool = False,
    max_bytes: int = 12_000,
) -> dict[str, Any]:
    if max_bytes < 1:
        raise ValueError("TARGET_CONTEXT_BUDGET_INVALID")
    cap = DIAGNOSTIC_MAX_CANDIDATES if diagnostic else NORMAL_MAX_CANDIDATES
    records = {record.record_id: record for record in repository.iter_records()}
    hits = list(result.candidates)
    if result.resolved_target_id:
        hits.sort(key=lambda hit: (hit.record_id != result.resolved_target_id, -hit.fused_score, hit.ifc_global_id or ""))
    selected_hits = hits[:cap]
    candidates = [
        _project_candidate(records[hit.record_id], hit.to_dict(), query.attribute_intents)
        for hit in selected_hits
        if hit.record_id in records
    ]
    context = {
        "schema_version": TARGET_CONTEXT_SCHEMA_VERSION,
        "base_model_fingerprint": repository.metadata.source_ifc_sha256,
        "query_schema_version": query.schema_version,
        "resolution_schema_version": result.schema_version,
        "score_version": result.score_version,
        "status": result.status,
        "resolved_target_id": result.resolved_target_id,
        "operation_hints": list(operation_hints),
        "candidate_targets": candidates,
        "model_constraints": {
            "ifc_schema": repository.metadata.ifc_schema,
            "index_schema_version": repository.metadata.index_schema_version,
            "vector_retrieval": "disabled",
            "facts_source": "current_ifc_only",
        },
        "context_budget": {
            "mode": "diagnostic" if diagnostic else "normal",
            "max_candidates": cap,
            "max_bytes": max_bytes,
            "selected_candidate_count": len(candidates),
            "omitted_candidate_count": len(hits) - len(candidates),
            "actual_bytes": 0,
            "estimated_tokens": 0,
            "token_estimator": "ceil(utf8_bytes/4)",
        },
    }
    _fit_budget(context, total_candidates=len(hits))
    return context


def canonical_target_context_json(context: Mapping[str, Any]) -> str:
    return json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _project_candidate(
    record: ElementRecord,
    hit: dict[str, Any],
    attribute_intents: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    allowed_facets = {
        key: record.facets[key]
        for key in (
            "editable_target",
            "role",
            "opening_global_ids",
            "host_wall_global_ids",
            "boundary_evidence",
            "grid_labels",
            "space_names",
        )
        if key in record.facets
    }
    allowed_geometry = {
        key: record.geometry_summary[key]
        for key in ("coordinate_basis", "orientation", "dimensions_mm", "dimensions_project_units")
        if key in record.geometry_summary
    }
    requested = _requested_property_terms(attribute_intents)
    properties = [
        _property_payload(fact)
        for fact in record.properties
        if requested and (
            fact.property_name.casefold() in requested or fact.set_name.casefold() in requested
        )
    ]
    return {
        "target_id": record.record_id,
        "ifc_global_id": record.ifc_global_id,
        "ifc_class": record.ifc_class,
        "name": record.name,
        "type_name": record.type_name,
        "storey_name": record.storey_name,
        "geometry_capability": record.geometry_capability,
        "geometry": allowed_geometry,
        "facets": allowed_facets,
        "properties": properties,
        "retrieval": {
            key: hit[key]
            for key in (
                "retriever",
                "retriever_version",
                "source_score",
                "fused_score",
                "matched_fields",
            )
        },
        "evidence": hit["evidence"],
    }


def _requested_property_terms(intents: Sequence[Mapping[str, Any]]) -> set[str]:
    terms: set[str] = set()
    for intent in intents:
        for key in ("property", "property_name", "set", "set_name"):
            value = intent.get(key)
            if isinstance(value, str) and value.strip():
                terms.add(value.casefold())
    return terms


def _property_payload(fact: PropertyFact) -> dict[str, Any]:
    return {
        "set_kind": fact.set_kind,
        "set_name": fact.set_name,
        "property_name": fact.property_name,
        "value": fact.value,
        "value_type": fact.value_type,
        "unit": fact.unit,
        "inherited": fact.inherited,
        "provenance": fact.provenance,
    }


def _fit_budget(context: dict[str, Any], *, total_candidates: int) -> None:
    budget = context["context_budget"]
    while True:
        _stabilize_measurement(context)
        if budget["actual_bytes"] <= budget["max_bytes"]:
            return
        if not context["candidate_targets"] or (
            len(context["candidate_targets"]) == 1 and context["resolved_target_id"]
        ):
            raise TargetContextError(
                "TARGET_CONTEXT_BUDGET_EXCEEDED",
                "Minimum target context exceeds the configured byte budget",
            )
        context["candidate_targets"].pop()
        budget["selected_candidate_count"] = len(context["candidate_targets"])
        budget["omitted_candidate_count"] = total_candidates - len(context["candidate_targets"])


def _stabilize_measurement(context: dict[str, Any]) -> None:
    budget = context["context_budget"]
    for _ in range(10):
        size = len(canonical_target_context_json(context).encode("utf-8"))
        tokens = (size + 3) // 4
        if size == budget["actual_bytes"] and tokens == budget["estimated_tokens"]:
            return
        budget["actual_bytes"] = size
        budget["estimated_tokens"] = tokens
    raise RuntimeError("TARGET_CONTEXT_MEASUREMENT_DID_NOT_STABILIZE")


__all__ = [
    "DIAGNOSTIC_MAX_CANDIDATES",
    "NORMAL_MAX_CANDIDATES",
    "TARGET_CONTEXT_SCHEMA_VERSION",
    "TargetContextError",
    "build_target_context",
    "canonical_target_context_json",
]
