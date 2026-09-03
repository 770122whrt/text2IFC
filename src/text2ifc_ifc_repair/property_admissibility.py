"""Pure execution admissibility for one Stage 1.5 property decision."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

from text2ifc_knowledge.property_search import (
    PropertyKnowledgeRecord,
    normalize_property_value,
)
from text2ifc_knowledge.registry import IfcKnowledgeRegistry

from .property_intent import (
    AuthorizedPropertyFact,
    ExactPropertyIntent,
    NaturalLanguagePropertyIntent,
    PropertyResolutionStatus,
    authorize_standard_property,
    construct_exact_property_intent,
    resolve_exact_property_intent,
)


ADMISSIBILITY_SCHEMA_VERSION = "text2ifc/ifc-property-admissibility/0.1"


@dataclass(frozen=True)
class PropertyAdmissibilityResult:
    status: str
    reason_code: str
    document: Mapping[str, Any]
    exact_intent: ExactPropertyIntent | None = None

    def to_dict(self) -> dict[str, Any]:
        document = dict(self.document)
        document["checks"] = dict(document["checks"])
        return json.loads(
            json.dumps(document, ensure_ascii=False, allow_nan=False)
        )


def admit_property_decision(
    *,
    query: Mapping[str, Any],
    candidate_set: Mapping[str, Any],
    decision: Mapping[str, Any],
    decision_trace: Mapping[str, Any],
    policy: Mapping[str, Any],
    records: Iterable[PropertyKnowledgeRecord],
    registry: IfcKnowledgeRegistry,
    claim: NaturalLanguagePropertyIntent,
    project_length_unit: str = "m",
) -> PropertyAdmissibilityResult:
    """Recheck executability without deciding natural-language semantics."""

    query_document = _plain(query)
    candidate_document = _plain(candidate_set)
    decision_document = _plain(decision)
    policy_document = _plain(policy)
    checks = _empty_checks()

    if _schema_errors(
        query_document,
        "schemas/agent/ifc-property-resolution-query-0.2.schema.json",
    ):
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_QUERY_SCHEMA_INVALID",
        )
    if _schema_errors(
        candidate_document,
        "schemas/agent/ifc-property-candidate-set-0.1.schema.json",
    ):
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_EVIDENCE_SCHEMA_INVALID",
        )
    if _schema_errors(
        decision_document,
        "schemas/agent/ifc-property-rerank-decision-0.1.schema.json",
    ):
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_DECISION_SCHEMA_INVALID",
        )
    if _schema_errors(
        policy_document,
        "schemas/ifc/knowledge/property_resolution_policy.schema.json",
    ):
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_POLICY_INVALID",
        )

    if not _decision_binding_matches(
        query=query_document,
        candidate_set=candidate_document,
        trace=decision_trace,
    ):
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_DECISION_BINDING_MISMATCH",
        )
    if not _claim_matches_query(claim, query_document):
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_QUERY_CLAIM_MISMATCH",
        )

    semantic_status = str(decision_document["decision"])
    if semantic_status == "unsupported":
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="unsupported",
            reason_code="PROPERTY_RERANKER_UNSUPPORTED",
        )
    if semantic_status == "clarification_required":
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="clarification_required",
            reason_code="PROPERTY_RERANKER_CLARIFICATION",
        )
    if decision_document["conflicting_candidate_ids"]:
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_DECISION_CONFLICT_UNRESOLVED",
            selected_candidate_id=str(
                decision_document.get("selected_candidate_id") or ""
            ),
        )

    selected_id = str(decision_document["selected_candidate_id"])
    offered = {
        str(item["candidate_id"]): item
        for item in candidate_document["candidates"]
    }
    candidate = offered.get(selected_id)
    if candidate is None:
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_CANDIDATE_NOT_OFFERED",
            selected_candidate_id=selected_id,
        )
    checks["offered_candidate"] = True
    checks["conflict_resolved"] = True

    records_by_public_id = {
        _public_record_id(record): record for record in records
    }
    public_record_id = str(candidate["record_id"])
    record = records_by_public_id.get(public_record_id)
    if record is None:
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_AUTHORITATIVE_RECORD_MISSING",
            selected_candidate_id=selected_id,
        )
    checks["authoritative_record_present"] = True

    # The authoritative record, rather than Provider-returned evidence, decides
    # whether this authoring path can represent the selected property.
    if record.template_type != policy_document["supported_template"]:
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_SCALAR_TEMPLATE_UNSUPPORTED",
            selected_candidate_id=selected_id,
            authoritative_record_id=public_record_id,
        )
    if not _candidate_matches_record(candidate, record):
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_CANDIDATE_RECORD_MISMATCH",
            selected_candidate_id=selected_id,
            authoritative_record_id=public_record_id,
        )

    target_class = str(query_document["target_ifc_class"])
    if not record.is_applicable(target_class, registry):
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_TARGET_CLASS_INAPPLICABLE",
            selected_candidate_id=selected_id,
            authoritative_record_id=public_record_id,
        )
    checks["target_class_applicable"] = True

    checks["scalar_template_supported"] = True

    scope = query_document.get("scope")
    if scope != policy_document["supported_scope"] or claim.scope != scope:
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_OCCURRENCE_SCOPE_REQUIRED",
            selected_candidate_id=selected_id,
            authoritative_record_id=public_record_id,
        )
    checks["occurrence_scope_supported"] = True

    raw_unit = query_document.get("raw_unit")
    if raw_unit is not None and not record.unit_types:
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_UNIT_INCOMPATIBLE",
            selected_candidate_id=selected_id,
            authoritative_record_id=public_record_id,
        )
    if record.value_type is None:
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code="PROPERTY_VALUE_TYPE_INCOMPATIBLE",
            selected_candidate_id=selected_id,
            authoritative_record_id=public_record_id,
        )
    try:
        normalized_value, normalized_unit = normalize_property_value(
            query_document["raw_value"],
            raw_unit=None if raw_unit is None else str(raw_unit),
            value_type=record.value_type,
            project_length_unit=project_length_unit,
        )
    except ValueError as error:
        reason = (
            "PROPERTY_UNIT_INCOMPATIBLE"
            if "UNIT" in str(error)
            else "PROPERTY_VALUE_TYPE_INCOMPATIBLE"
        )
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="rejected",
            reason_code=reason,
            selected_candidate_id=selected_id,
            authoritative_record_id=public_record_id,
        )
    checks["value_type_compatible"] = True
    checks["unit_compatible"] = True

    if float(candidate["score"]) < float(
        policy_document["minimum_retrieval_score"]
    ):
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="clarification_required",
            reason_code="PROPERTY_RETRIEVAL_BELOW_FLOOR",
            selected_candidate_id=selected_id,
            authoritative_record_id=public_record_id,
        )
    checks["minimum_retrieval_quality_met"] = True

    if record.authority == "current_ifc_project":
        return _result(
            query=query_document,
            candidate_set=candidate_document,
            policy=policy_document,
            checks=checks,
            status="custom_confirmation_required",
            reason_code="PROPERTY_CUSTOM_CONFIRMATION_REQUIRED",
            selected_candidate_id=selected_id,
            authoritative_record_id=public_record_id,
        )
    exact_intent = construct_exact_property_intent(
        record=record,
        claim=claim,
        normalized_value=normalized_value,
        normalized_unit=normalized_unit,
        scope=str(scope),
    )
    return _result(
        query=query_document,
        candidate_set=candidate_document,
        policy=policy_document,
        checks=checks,
        status="passed",
        reason_code="PROPERTY_ADMISSIBLE",
        selected_candidate_id=selected_id,
        authoritative_record_id=public_record_id,
        exact_intent=exact_intent,
    )


def authorize_admissible_standard_property(
    result: PropertyAdmissibilityResult,
    *,
    registry: IfcKnowledgeRegistry,
    target_ifc_class: str,
    existing_facts: Iterable[Any],
    operation_id: str,
    target_global_id: str,
    request_hash: str,
    model_fingerprint: str,
) -> AuthorizedPropertyFact:
    """Route only a passed exact intent through the existing Binder authority."""

    if result.status != "passed" or result.exact_intent is None:
        raise ValueError("PROPERTY_ADMISSIBILITY_NOT_PASSED")
    resolution = resolve_exact_property_intent(
        result.exact_intent,
        target_ifc_class=target_ifc_class,
        existing_facts=existing_facts,
        registry=registry,
    )
    if resolution.status is not PropertyResolutionStatus.STANDARD_RESOLVED:
        raise ValueError(
            str(resolution.reason_code or "STANDARD_PROPERTY_NOT_RESOLVED")
        )
    return authorize_standard_property(
        resolution,
        operation_id=operation_id,
        target_global_id=target_global_id,
        request_hash=request_hash,
        model_fingerprint=model_fingerprint,
        source=result.exact_intent.source,
    )


def _result(
    *,
    query: Mapping[str, Any],
    candidate_set: Mapping[str, Any],
    policy: Mapping[str, Any],
    checks: Mapping[str, bool],
    status: str,
    reason_code: str,
    selected_candidate_id: str | None = None,
    authoritative_record_id: str | None = None,
    exact_intent: ExactPropertyIntent | None = None,
) -> PropertyAdmissibilityResult:
    run_id = str(query.get("run_id", "unknown"))
    operation_id = str(query.get("operation_id", "unknown"))
    claim_id = str(query.get("claim_id", "unknown"))
    document = {
        "schema_version": ADMISSIBILITY_SCHEMA_VERSION,
        "admissibility_id": (
            f"property-admissibility:{run_id}:{operation_id}:{claim_id}"
        ),
        "query_id": str(query.get("query_id", "property-query:unknown")),
        "candidate_set_id": str(
            candidate_set.get("candidate_set_id", "property-candidates:unknown")
        ),
        "decision_id": f"property-decision:{run_id}:{operation_id}:{claim_id}",
        "policy_id": str(
            policy.get("policy_id", "ifc2x3.single-value.vector-reranker")
        ),
        "policy_version": str(policy.get("version", "0.2")),
        "status": status,
        "selected_candidate_id": selected_candidate_id,
        "authoritative_record_id": authoritative_record_id,
        "checks": dict(checks),
        "reason_code": reason_code,
    }
    return PropertyAdmissibilityResult(
        status=status,
        reason_code=reason_code,
        document=MappingProxyType(
            {**document, "checks": MappingProxyType(dict(checks))}
        ),
        exact_intent=exact_intent,
    )


def _empty_checks() -> dict[str, bool]:
    return {
        "offered_candidate": False,
        "authoritative_record_present": False,
        "target_class_applicable": False,
        "scalar_template_supported": False,
        "value_type_compatible": False,
        "unit_compatible": False,
        "occurrence_scope_supported": False,
        "minimum_retrieval_quality_met": False,
        "conflict_resolved": False,
    }


def _claim_matches_query(
    claim: NaturalLanguagePropertyIntent,
    query: Mapping[str, Any],
) -> bool:
    return (
        claim.property_phrase == query.get("property_phrase")
        and claim.raw_value == query.get("raw_value")
        and claim.raw_unit == query.get("raw_unit")
        and claim.scope == query.get("scope")
    )


def _decision_binding_matches(
    *,
    query: Mapping[str, Any],
    candidate_set: Mapping[str, Any],
    trace: Mapping[str, Any],
) -> bool:
    if candidate_set.get("query_id") != query.get("query_id"):
        return False
    if candidate_set.get("corpus_version") != query.get("corpus_version"):
        return False
    expected = {
        "run_id": query.get("run_id"),
        "request_id": query.get("request_id"),
        "model_id": query.get("model_id"),
        "operation_id": query.get("operation_id"),
        "claim_id": query.get("claim_id"),
        "query_id": query.get("query_id"),
        "candidate_set_id": candidate_set.get("candidate_set_id"),
        "provider_call_ordinal": "property_resolution",
        "status": "valid",
    }
    return all(trace.get(key) == value for key, value in expected.items())


def _candidate_matches_record(
    candidate: Mapping[str, Any],
    record: PropertyKnowledgeRecord,
) -> bool:
    expected_unit = record.unit_types[0] if len(record.unit_types) == 1 else None
    expected = {
        "record_id": _public_record_id(record),
        "canonical_path": record.canonical_path,
        "set_name": record.set_name,
        "property_name": record.property_name,
        "applicable_classes": list(record.applicable_classes),
        "template_type": record.template_type,
        "value_type": record.value_type,
        "unit": expected_unit,
        "standard_status": (
            "standard" if record.authority == "ifc2x3_psd" else "project_custom"
        ),
        "source": {
            "kind": (
                "ifc2x3_psd"
                if record.authority == "ifc2x3_psd"
                else "project_record"
            ),
            "reference": record.source_ref or record.canonical_path,
        },
    }
    return all(candidate.get(key) == value for key, value in expected.items())


def _public_record_id(record: PropertyKnowledgeRecord) -> str:
    if record.authority == "ifc2x3_psd":
        return f"ifc2x3:{record.canonical_path}"
    target = record.applicable_classes[0] if record.applicable_classes else "IfcObject"
    return f"project:{target}:{record.canonical_path}"


def _schema_errors(document: Mapping[str, Any], relative_path: str) -> tuple[Any, ...]:
    root = Path(__file__).resolve().parents[2]
    schema = json.loads((root / relative_path).read_text(encoding="utf-8"))
    return tuple(Draft202012Validator(schema).iter_errors(document))


def _plain(value: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(dict(value), ensure_ascii=False, allow_nan=False))


__all__ = [
    "ADMISSIBILITY_SCHEMA_VERSION",
    "PropertyAdmissibilityResult",
    "admit_property_decision",
    "authorize_admissible_standard_property",
]
