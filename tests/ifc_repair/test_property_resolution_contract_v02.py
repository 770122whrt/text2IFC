from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from text2ifc_agent.prompt_registry import load_prompt_registry, render_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATHS = {
    "query": PROJECT_ROOT
    / "schemas/agent/ifc-property-resolution-query-0.2.schema.json",
    "candidate_set": PROJECT_ROOT
    / "schemas/agent/ifc-property-candidate-set-0.1.schema.json",
    "decision": PROJECT_ROOT
    / "schemas/agent/ifc-property-rerank-decision-0.1.schema.json",
    "admissibility": PROJECT_ROOT
    / "schemas/agent/ifc-property-admissibility-0.1.schema.json",
    "policy": PROJECT_ROOT
    / "schemas/ifc/knowledge/property_resolution_policy.schema.json",
}
SCHEMA_IDS = {
    "query": "text2ifc/ifc-property-resolution-query/0.2",
    "candidate_set": "text2ifc/ifc-property-candidate-set/0.1",
    "decision": "text2ifc/ifc-property-rerank-decision/0.1",
    "admissibility": "text2ifc/ifc-property-admissibility/0.1",
    "policy": "text2ifc/property-resolution-policy/0.2",
}
PROMPT_ID = "ifc-property-resolution.v0.1"


def _load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_PATHS[name]
    assert path.is_file(), f"missing additive Phase 12.1 schema: {path}"
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def _errors(name: str, payload: dict[str, Any]) -> list[Any]:
    return list(Draft202012Validator(_load_schema(name)).iter_errors(payload))


def _query() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_IDS["query"],
        "query_id": "query:run-1:beam-1:claim-1",
        "run_id": "run-1",
        "request_id": "request-1",
        "model_id": "model-1",
        "operation_id": "beam-1",
        "operation_type": "add_beam",
        "claim_id": "claim-1",
        "property_phrase": "load bearing",
        "target_ifc_class": "IfcBeam",
        "raw_value": True,
        "raw_value_kind": "boolean",
        "raw_unit": None,
        "scope": "occurrence_direct",
        "corpus_version": "ifc2x3-property-records/0.2",
    }


def _candidate(candidate_id: str = "candidate:Pset_BeamCommon.LoadBearing") -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "record_id": "ifc2x3:Pset_BeamCommon.LoadBearing",
        "rank": 1,
        "score": 0.82,
        "canonical_path": "Pset_BeamCommon.LoadBearing",
        "set_name": "Pset_BeamCommon",
        "property_name": "LoadBearing",
        "definition": "Whether the beam is intended to carry loads.",
        "applicable_classes": ["IfcBeam"],
        "template_type": "TypePropertySingleValue",
        "value_type": "IfcBoolean",
        "unit": None,
        "standard_status": "standard",
        "source": {
            "kind": "ifc2x3_psd",
            "reference": "ifc2x3:Pset_BeamCommon.LoadBearing",
        },
    }


def _candidate_set() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_IDS["candidate_set"],
        "candidate_set_id": "candidates:run-1:beam-1:claim-1",
        "query_id": "query:run-1:beam-1:claim-1",
        "corpus_version": "ifc2x3-property-records/0.2",
        "embedding_model": {
            "model_id": "BAAI/bge-m3",
            "model_version": "configured",
        },
        "document_renderer_version": "property-record-text/0.1",
        "collection_version": "ifc2x3-property-vector/0.2",
        "candidates": [_candidate()],
    }


def _decision(decision: str = "confirmed") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_IDS["decision"],
        "decision": decision,
        "selected_candidate_id": (
            "candidate:Pset_BeamCommon.LoadBearing"
            if decision == "confirmed"
            else None
        ),
        "conflicting_candidate_ids": [],
        "clarification_question": None,
    }


def _admissibility() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_IDS["admissibility"],
        "admissibility_id": "admissibility:run-1:beam-1:claim-1",
        "query_id": "query:run-1:beam-1:claim-1",
        "candidate_set_id": "candidates:run-1:beam-1:claim-1",
        "decision_id": "decision:run-1:beam-1:claim-1:attempt-1",
        "policy_id": "ifc2x3.single-value.vector-reranker",
        "policy_version": "0.2",
        "status": "passed",
        "selected_candidate_id": "candidate:Pset_BeamCommon.LoadBearing",
        "authoritative_record_id": "ifc2x3:Pset_BeamCommon.LoadBearing",
        "checks": {
            "offered_candidate": True,
            "authoritative_record_present": True,
            "target_class_applicable": True,
            "scalar_template_supported": True,
            "value_type_compatible": True,
            "unit_compatible": True,
            "occurrence_scope_supported": True,
            "minimum_retrieval_quality_met": True,
            "conflict_resolved": True,
        },
        "reason_code": "PROPERTY_ADMISSIBLE",
    }


def _policy() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_IDS["policy"],
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


def test_additive_contract_schemas_are_closed_and_have_exact_ids() -> None:
    for name, expected_id in SCHEMA_IDS.items():
        schema = _load_schema(name)
        assert schema["$id"] == expected_id
        assert schema["additionalProperties"] is False

    serialized = json.dumps(
        {name: _load_schema(name) for name in SCHEMA_PATHS},
        ensure_ascii=False,
    ).lower()
    for forbidden in (
        "property_aliases",
        "reviewed_alias",
        "sha256",
        "fingerprint",
    ):
        assert forbidden not in serialized


def test_query_and_candidate_set_are_public_bounded_documents() -> None:
    assert not _errors("query", _query())
    assert not _errors("candidate_set", _candidate_set())

    extra_query = _query()
    extra_query["set_name"] = "Pset_BeamCommon"
    assert _errors("query", extra_query)

    private_candidate_set = _candidate_set()
    private_candidate_set["benchmark_gold"] = {"expected": "LoadBearing"}
    assert _errors("candidate_set", private_candidate_set)

    too_many = _candidate_set()
    too_many["candidates"] = [
        _candidate(f"candidate:Pset_BeamCommon.LoadBearing{i}")
        | {"rank": i}
        for i in range(1, 7)
    ]
    assert _errors("candidate_set", too_many)

    duplicate = _candidate_set()
    duplicate["candidates"] = [_candidate(), _candidate()]
    assert _errors("candidate_set", duplicate)


def test_reranker_decision_cannot_emit_executable_property_fields() -> None:
    assert not _errors("decision", _decision())

    clarification = _decision("clarification_required")
    clarification["conflicting_candidate_ids"] = [
        "candidate:Pset_BeamCommon.LoadBearing",
        "candidate:AcousticRating",
    ]
    clarification["clarification_question"] = (
        "Which of the offered properties do you mean?"
    )
    assert not _errors("decision", clarification)
    assert not _errors("decision", _decision("unsupported"))

    for forbidden_field, value in (
        ("set_name", "Pset_BeamCommon"),
        ("property_name", "LoadBearing"),
        ("value", False),
        ("value_type", "IfcBoolean"),
        ("scope", "type_owned"),
        ("operation_id", "other-operation"),
    ):
        invalid = _decision()
        invalid[forbidden_field] = value
        assert _errors("decision", invalid), forbidden_field

    missing_selection = _decision()
    missing_selection["selected_candidate_id"] = None
    assert _errors("decision", missing_selection)

    selection_on_unsupported = _decision("unsupported")
    selection_on_unsupported["selected_candidate_id"] = (
        "candidate:Pset_BeamCommon.LoadBearing"
    )
    assert _errors("decision", selection_on_unsupported)


def test_admissibility_and_policy_use_ids_versions_and_concrete_checks() -> None:
    assert not _errors("admissibility", _admissibility())
    assert not _errors("policy", _policy())

    extra = _admissibility()
    extra["candidate_hash"] = "not-part-of-the-contract"
    assert _errors("admissibility", extra)

    permissive = _policy()
    permissive["vector_top1_authority"] = True
    assert _errors("policy", permissive)
    permissive = _policy()
    permissive["alias_authority"] = True
    assert _errors("policy", permissive)


def test_stage1_natural_language_claim_preserves_user_facts_only() -> None:
    body_schema = json.loads(
        (
            PROJECT_ROOT
            / "schemas/agent/ifc-repair-intent-body-0.8.schema.json"
        ).read_text(encoding="utf-8")
    )
    claim_schema = {
        "$schema": body_schema["$schema"],
        "$defs": body_schema["$defs"],
        "$ref": "#/$defs/natural_language_property",
    }
    validator = Draft202012Validator(claim_schema)
    claim = {
        "intent_kind": "natural_language_property",
        "property_phrase": "load bearing",
        "raw_value": True,
        "raw_unit": None,
        "scope": "occurrence_direct",
        "source": {
            "source_kind": "user_request",
            "reference": "request:/text",
            "excerpt": "load bearing",
        },
    }
    assert not list(validator.iter_errors(claim))

    for forbidden_field, value in (
        ("set_name", "Pset_BeamCommon"),
        ("property_name", "LoadBearing"),
        ("candidate_id", "candidate:Pset_BeamCommon.LoadBearing"),
        ("value_type", "IfcBoolean"),
        ("authorized", True),
    ):
        invalid = copy.deepcopy(claim)
        invalid[forbidden_field] = value
        assert list(validator.iter_errors(invalid)), forbidden_field


def test_registered_prompt_is_bounded_repair_only_and_has_no_phrase_mapping() -> None:
    registry = load_prompt_registry()
    template = registry[PROMPT_ID]
    assert template["required_inputs"] == [
        "PROPERTY_QUERY",
        "CANDIDATE_SET",
        "DECISION_SCHEMA",
        "PREVIOUS_VALIDATION_FEEDBACK",
    ]
    assert {
        "canonical_property",
        "canonical_pset",
        "value_override",
        "scope_override",
        "operation_override",
        "private_original_ifc",
        "benchmark_gold",
        "mutation_mapping",
    } <= set(template["forbidden_outputs"])

    rendered = render_prompt(
        template_id=PROMPT_ID,
        inputs={
            "PROPERTY_QUERY": _query(),
            "CANDIDATE_SET": _candidate_set(),
            "DECISION_SCHEMA": _load_schema("decision"),
            "PREVIOUS_VALIDATION_FEEDBACK": [],
        },
    )["text"]
    for contract_text in (
        "repair-only",
        "one property claim",
        "offered candidate",
        "confirmed",
        "clarification_required",
        "unsupported",
        "No candidate is executable authority",
        "Return exactly one JSON object",
    ):
        assert contract_text in rendered

    aliases = json.loads(
        (
            PROJECT_ROOT / "schemas/ifc/knowledge/property_aliases.json"
        ).read_text(encoding="utf-8")
    )["aliases"]
    prompt_template = (
        PROJECT_ROOT / "prompts/agent/ifc-property-resolution-v0.1.md"
    ).read_text(encoding="utf-8")
    assert "load bearing" not in prompt_template.lower()
    for alias in aliases:
        assert alias["alias"] not in prompt_template


def test_released_alias_policy_remains_historical_and_unmodified_in_shape() -> None:
    policy = json.loads(
        (
            PROJECT_ROOT
            / "schemas/ifc/knowledge/property_resolution_policy.json"
        ).read_text(encoding="utf-8")
    )
    aliases = json.loads(
        (
            PROJECT_ROOT / "schemas/ifc/knowledge/property_aliases.json"
        ).read_text(encoding="utf-8")
    )
    assert policy["schema_version"] == "text2ifc/property-resolution-policy/0.1"
    assert "reviewed_alias_exact" in policy["rules"]
    assert aliases["schema_version"] == "text2ifc/property-aliases/0.1"
    assert aliases["review_policy"].startswith("human-reviewed seed aliases")
