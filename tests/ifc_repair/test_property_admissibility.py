from __future__ import annotations

from dataclasses import replace
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from text2ifc_ifc_repair.property_intent import NaturalLanguagePropertyIntent
from text2ifc_ifc_repair.repair_intent import PublicProvenance
from text2ifc_knowledge.property_search import (
    PropertyKnowledgeRecord,
    build_standard_property_records,
    default_standard_corpus_fingerprint,
)
from text2ifc_knowledge.registry import load_ifc2x3_registry


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _module():
    module_name = "text2ifc_ifc_repair.property_admissibility"
    assert importlib.util.find_spec(module_name) is not None, (
        "Plan 12.1-04 property admissibility module is missing"
    )
    return importlib.import_module(module_name)


@pytest.fixture(scope="module")
def knowledge():
    registry = load_ifc2x3_registry(PROJECT_ROOT)
    records = build_standard_property_records(
        registry,
        corpus_fingerprint=default_standard_corpus_fingerprint(),
    )
    by_path = {record.canonical_path: record for record in records}
    return registry, by_path


def _source() -> PublicProvenance:
    return PublicProvenance(
        source_kind="user_request",
        reference="request:/text/claim-1",
        excerpt="Set load bearing to true on the selected beam.",
    )


def _claim(
    *,
    phrase: str = "load bearing",
    value: object = True,
    unit: str | None = None,
    scope: str | None = "occurrence_direct",
) -> NaturalLanguagePropertyIntent:
    return NaturalLanguagePropertyIntent(
        property_phrase=phrase,
        raw_value=value,
        raw_unit=unit,
        scope=scope,
        source=_source(),
    )


def _query(
    claim: NaturalLanguagePropertyIntent,
    *,
    target_class: str = "IfcBeam",
) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/ifc-property-resolution-query/0.2",
        "query_id": "property-query:run-1:operation-1:claim-1",
        "run_id": "run-1",
        "request_id": "request-1",
        "model_id": "model-1",
        "operation_id": "operation-1",
        "operation_type": "set_occurrence_properties",
        "claim_id": "claim-1",
        "property_phrase": claim.property_phrase,
        "target_ifc_class": target_class,
        "raw_value": claim.raw_value,
        "raw_value_kind": (
            "boolean"
            if isinstance(claim.raw_value, bool)
            else "integer"
            if isinstance(claim.raw_value, int)
            else "number"
            if isinstance(claim.raw_value, float)
            else "string"
        ),
        "raw_unit": claim.raw_unit,
        "scope": claim.scope,
        "corpus_version": "ifc2x3-property-records/0.2",
    }


def _public_record_id(record: PropertyKnowledgeRecord) -> str:
    if record.authority == "ifc2x3_psd":
        return f"ifc2x3:{record.canonical_path}"
    target = record.applicable_classes[0]
    return f"project:{target}:{record.canonical_path}"


def _candidate(
    record: PropertyKnowledgeRecord,
    *,
    rank: int,
    score: float,
) -> dict[str, Any]:
    public_id = _public_record_id(record)
    return {
        "candidate_id": f"candidate:{rank}:{public_id}",
        "record_id": public_id,
        "rank": rank,
        "score": score,
        "canonical_path": record.canonical_path,
        "set_name": record.set_name,
        "property_name": record.property_name,
        "definition": record.definition or record.canonical_path,
        "applicable_classes": list(record.applicable_classes),
        "template_type": record.template_type,
        "value_type": record.value_type,
        "unit": record.unit_types[0] if len(record.unit_types) == 1 else None,
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


def _candidate_set(
    query: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/ifc-property-candidate-set/0.1",
        "candidate_set_id": "property-candidates:run-1:operation-1:claim-1",
        "query_id": query["query_id"],
        "corpus_version": query["corpus_version"],
        "embedding_model": {
            "model_id": "BAAI/bge-m3",
            "model_version": "fixture/0.1",
        },
        "document_renderer_version": "property-record-text/0.1",
        "collection_version": "ifc2x3-property-vector/0.2",
        "candidates": candidates,
    }


def _decision(
    decision: str,
    *,
    selected: str | None = None,
    conflicts: list[str] | None = None,
    question: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
        "decision": decision,
        "selected_candidate_id": selected,
        "conflicting_candidate_ids": list(conflicts or []),
        "clarification_question": question,
    }


def _trace(query: dict[str, Any], candidate_set: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": query["run_id"],
        "request_id": query["request_id"],
        "model_id": query["model_id"],
        "operation_id": query["operation_id"],
        "claim_id": query["claim_id"],
        "query_id": query["query_id"],
        "candidate_set_id": candidate_set["candidate_set_id"],
        "provider_call_ordinal": "property_resolution",
        "status": "valid",
    }


def _policy() -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/property-resolution-policy/0.2",
        "policy_id": "ifc2x3.single-value.vector-reranker",
        "version": "0.2",
        "max_candidates": 5,
        "max_attempts": 2,
        "vector_required": True,
        "minimum_retrieval_score": 0.5,
        "alias_authority": False,
        "vector_top1_authority": False,
        "vector_margin_authority": False,
        "standard_selection": "stage_1_5_required",
        "project_or_custom": "explicit_confirmation_required",
        "explicit_canonical": "exact_path_bypass",
        "supported_template": "TypePropertySingleValue",
        "supported_scope": "occurrence_direct",
    }


def _valid_case(knowledge):
    registry, by_path = knowledge
    record = by_path["Pset_BeamCommon.LoadBearing"]
    claim = _claim()
    query = _query(claim)
    candidates = _candidate_set(query, [_candidate(record, rank=1, score=0.92)])
    decision = _decision(
        "confirmed",
        selected=candidates["candidates"][0]["candidate_id"],
    )
    return {
        "registry": registry,
        "records": (record,),
        "claim": claim,
        "query": query,
        "candidate_set": candidates,
        "decision": decision,
        "decision_trace": _trace(query, candidates),
        "policy": _policy(),
    }


def _admit(case):
    return _module().admit_property_decision(**case)


def test_valid_standard_selection_constructs_exact_intent_from_record_and_claim(
    knowledge,
) -> None:
    case = _valid_case(knowledge)
    result = _admit(case)

    assert result.status == "passed"
    assert result.reason_code == "PROPERTY_ADMISSIBLE"
    assert result.exact_intent is not None
    record = case["records"][0]
    exact = result.exact_intent
    assert exact.set_name == record.set_name
    assert exact.property_name == record.property_name
    assert exact.requested_value_type == record.value_type
    assert exact.value is case["claim"].raw_value
    assert exact.requested_unit is None
    assert exact.scope == "occurrence_direct"
    assert exact.source is case["claim"].source

    document = result.to_dict()
    schema = json.loads(
        (
            PROJECT_ROOT
            / "schemas/agent/ifc-property-admissibility-0.1.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert not list(Draft202012Validator(schema).iter_errors(document))
    assert document["query_id"] == case["query"]["query_id"]
    assert document["candidate_set_id"] == case["candidate_set"][
        "candidate_set_id"
    ]
    assert document["decision_id"] == (
        "property-decision:run-1:operation-1:claim-1"
    )
    serialized = json.dumps(exact.to_dict(), ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "candidate_set",
        "retrieval",
        "score",
        "margin",
        "reasoning",
        "decision_id",
    ):
        assert forbidden not in serialized


def test_inherited_wall_property_remains_authorable_for_wall_standard_case(
    knowledge,
) -> None:
    registry, by_path = knowledge
    record = by_path["Pset_WallCommon.IsExternal"]
    claim = _claim(phrase="external", value=True)
    query = _query(claim, target_class="IfcWallStandardCase")
    candidate_set = _candidate_set(
        query,
        [_candidate(record, rank=1, score=0.92)],
    )
    result = _admit(
        {
            "registry": registry,
            "records": (record,),
            "claim": claim,
            "query": query,
            "candidate_set": candidate_set,
            "decision": _decision(
                "confirmed",
                selected=candidate_set["candidates"][0]["candidate_id"],
            ),
            "decision_trace": _trace(query, candidate_set),
            "policy": _policy(),
        }
    )

    fact = _module().authorize_admissible_standard_property(
        result,
        registry=registry,
        target_ifc_class="IfcWallStandardCase",
        existing_facts=(),
        operation_id="operation-1",
        target_global_id="wall-guid-1",
        request_hash="existing-request-binding",
        model_fingerprint="existing-model-binding",
    )
    assert fact.set_name == "Pset_WallCommon"
    assert fact.property_name == "IsExternal"
    assert fact.value is True


@pytest.mark.parametrize(
    ("mutator", "reason_code"),
    [
        (
            lambda case: case["decision"].update(
                selected_candidate_id="candidate:9:ifc2x3:Pset_BeamCommon.Invented"
            ),
            "PROPERTY_CANDIDATE_NOT_OFFERED",
        ),
        (
            lambda case: case["query"].update(target_ifc_class="IfcWindow"),
            "PROPERTY_TARGET_CLASS_INAPPLICABLE",
        ),
        (
            lambda case: case.update(
                records=(
                    replace(
                        case["records"][0],
                        template_type="TypePropertyListValue",
                    ),
                )
            ),
            "PROPERTY_SCALAR_TEMPLATE_UNSUPPORTED",
        ),
        (
            lambda case: case.update(records=()),
            "PROPERTY_AUTHORITATIVE_RECORD_MISSING",
        ),
        (
            lambda case: case["query"].update(
                raw_value="yes",
                raw_value_kind="string",
            ),
            "PROPERTY_QUERY_CLAIM_MISMATCH",
        ),
        (
            lambda case: (
                case.update(claim=_claim(value="yes")),
                case["query"].update(raw_value="yes", raw_value_kind="string"),
            ),
            "PROPERTY_VALUE_TYPE_INCOMPATIBLE",
        ),
        (
            lambda case: (
                case.update(claim=_claim(unit="mm")),
                case["query"].update(raw_unit="mm"),
            ),
            "PROPERTY_UNIT_INCOMPATIBLE",
        ),
        (
            lambda case: (
                case.update(claim=_claim(scope="type_owned")),
                case["query"].update(scope="type_owned"),
            ),
            "PROPERTY_OCCURRENCE_SCOPE_REQUIRED",
        ),
        (
            lambda case: case["candidate_set"]["candidates"][0].update(score=0.49),
            "PROPERTY_RETRIEVAL_BELOW_FLOOR",
        ),
        (
            lambda case: case["decision"].update(
                conflicting_candidate_ids=[
                    case["candidate_set"]["candidates"][0]["candidate_id"]
                ]
            ),
            "PROPERTY_DECISION_CONFLICT_UNRESOLVED",
        ),
        (
            lambda case: case["decision"].update(selected_candidate_id=None),
            "PROPERTY_DECISION_SCHEMA_INVALID",
        ),
        (
            lambda case: case["decision_trace"].update(
                candidate_set_id="property-candidates:other"
            ),
            "PROPERTY_DECISION_BINDING_MISMATCH",
        ),
        (
            lambda case: case["candidate_set"].update(
                query_id="property-query:other"
            ),
            "PROPERTY_DECISION_BINDING_MISMATCH",
        ),
        (
            lambda case: case["candidate_set"].update(
                corpus_version="ifc2x3-property-records/stale"
            ),
            "PROPERTY_DECISION_BINDING_MISMATCH",
        ),
        (
            lambda case: case["candidate_set"]["candidates"][0].update(
                retrieval_paths=["reviewed_alias"]
            ),
            "PROPERTY_EVIDENCE_SCHEMA_INVALID",
        ),
    ],
)
def test_one_defect_matrix_fails_before_exact_intent(
    knowledge,
    mutator,
    reason_code: str,
) -> None:
    case = _valid_case(knowledge)
    mutator(case)
    result = _admit(case)
    assert result.status != "passed"
    assert result.reason_code == reason_code
    assert result.exact_intent is None


def test_project_candidate_requires_explicit_confirmation_and_no_exact_intent(
    knowledge,
) -> None:
    registry, by_path = knowledge
    standard = by_path["Pset_BeamCommon.LoadBearing"]
    project = replace(
        standard,
        record_id="project-record-load-bearing",
        authority="current_ifc_project",
        source_ref="ifc:current-public-model",
    )
    claim = _claim()
    query = _query(claim)
    candidate_set = _candidate_set(
        query,
        [_candidate(project, rank=1, score=0.91)],
    )
    result = _admit(
        {
            "registry": registry,
            "records": (project,),
            "claim": claim,
            "query": query,
            "candidate_set": candidate_set,
            "decision": _decision(
                "confirmed",
                selected=candidate_set["candidates"][0]["candidate_id"],
            ),
            "decision_trace": _trace(query, candidate_set),
            "policy": _policy(),
        }
    )
    assert result.status == "custom_confirmation_required"
    assert result.reason_code == "PROPERTY_CUSTOM_CONFIRMATION_REQUIRED"
    assert result.exact_intent is None


def test_vector_top1_or_large_margin_cannot_bypass_stage_1_5(knowledge) -> None:
    case = _valid_case(knowledge)
    case["candidate_set"]["candidates"][0]["score"] = 1.0
    case["decision"] = _decision("unsupported")
    result = _admit(case)
    assert result.status == "unsupported"
    assert result.exact_intent is None


def test_valid_non_top1_selection_with_small_margin_is_not_program_rejected(
    knowledge,
) -> None:
    registry, by_path = knowledge
    selected_record = by_path["Pset_BeamCommon.LoadBearing"]
    top_record = by_path["Pset_BeamCommon.IsExternal"]
    claim = _claim()
    query = _query(claim)
    candidate_set = _candidate_set(
        query,
        [
            _candidate(top_record, rank=1, score=0.61),
            _candidate(selected_record, rank=2, score=0.60),
        ],
    )
    selected_id = candidate_set["candidates"][1]["candidate_id"]
    result = _admit(
        {
            "registry": registry,
            "records": (top_record, selected_record),
            "claim": claim,
            "query": query,
            "candidate_set": candidate_set,
            "decision": _decision("confirmed", selected=selected_id),
            "decision_trace": _trace(query, candidate_set),
            "policy": _policy(),
        }
    )
    assert result.status == "passed"
    assert result.exact_intent is not None
    assert result.exact_intent.property_name == "LoadBearing"
    assert result.to_dict()["checks"]["conflict_resolved"] is True


def test_passed_result_routes_through_existing_exact_resolver_and_binder(
    knowledge,
) -> None:
    case = _valid_case(knowledge)
    result = _admit(case)
    fact = _module().authorize_admissible_standard_property(
        result,
        registry=case["registry"],
        target_ifc_class="IfcBeam",
        existing_facts=(),
        operation_id="operation-1",
        target_global_id="beam-guid-1",
        request_hash="existing-request-binding",
        model_fingerprint="existing-model-binding",
    )
    assert fact.set_name == "Pset_BeamCommon"
    assert fact.property_name == "LoadBearing"
    assert fact.value is True
    assert fact.value_type == "IfcBoolean"
    assert fact.ownership == "occurrence_direct"
