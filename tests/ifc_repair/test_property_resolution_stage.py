from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

from text2ifc_agent.openai_compat import OpenAICompatError
from text2ifc_agent.providers import (
    LiveProviderResult,
    ProviderOutput,
    ProviderOutputError,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _stage_module():
    module_name = "text2ifc_ifc_repair.property_resolution_stage"
    assert importlib.util.find_spec(module_name) is not None, (
        "Plan 12.1-03 Property Resolution Provider stage is missing"
    )
    return importlib.import_module(module_name)


def _query() -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/ifc-property-resolution-query/0.2",
        "query_id": "property-query:run-1:operation-1:claim-1",
        "run_id": "run-1",
        "request_id": "request-1",
        "model_id": "model-1",
        "operation_id": "operation-1",
        "operation_type": "set_occurrence_properties",
        "claim_id": "claim-1",
        "property_phrase": "load bearing",
        "target_ifc_class": "IfcBeam",
        "raw_value": True,
        "raw_value_kind": "boolean",
        "raw_unit": None,
        "scope": "occurrence_direct",
        "corpus_version": "ifc2x3-property-records/0.2",
    }


def _candidate(candidate_id: str, path: str, rank: int, score: float) -> dict[str, Any]:
    set_name, property_name = path.split(".", 1)
    return {
        "candidate_id": candidate_id,
        "record_id": f"ifc2x3:{path}",
        "rank": rank,
        "score": score,
        "canonical_path": path,
        "set_name": set_name,
        "property_name": property_name,
        "definition": f"Public IFC2X3 definition for {property_name}.",
        "applicable_classes": ["IfcBeam"],
        "template_type": "TypePropertySingleValue",
        "value_type": "IfcBoolean",
        "unit": None,
        "standard_status": "standard",
        "source": {
            "kind": "ifc2x3_psd",
            "reference": f"psd/{set_name}.xml",
        },
    }


def _candidate_set() -> dict[str, Any]:
    query = _query()
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
        "candidates": [
            _candidate(
                "candidate:1:ifc2x3:Pset_BeamCommon.LoadBearing",
                "Pset_BeamCommon.LoadBearing",
                1,
                0.92,
            ),
            _candidate(
                "candidate:2:ifc2x3:Pset_BeamCommon.IsExternal",
                "Pset_BeamCommon.IsExternal",
                2,
                0.71,
            ),
        ],
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


class CapturingProvider:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def generate_candidate(self, **arguments):
        self.calls.append(arguments)
        index = len(self.calls) - 1
        return ProviderOutput(
            text=self.responses[index],
            metadata={
                "provider": "fixture",
                "model": "fixture-reranker",
                "evidence_class": "synthetic-live-claim",
            },
        )


class InjectedGenerateLiveProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def generate_live(self, **arguments):
        self.calls.append(arguments)
        output = ProviderOutput(
            text=self.response,
            metadata={
                "provider": "fixture",
                "model": "fixture-reranker",
                "evidence_class": "live",
            },
        )
        return LiveProviderResult(
            session_id=arguments["session_id"],
            evidence_class="live",
            http_status=200,
            request={"fixture": True},
            response={"fixture": True},
            events=({"sequence": 0, "event": "fixture", "data": {}},),
            output=output,
        )


class IncompleteInjectedLiveProvider:
    def generate_live(self, **arguments):
        output = ProviderOutput(
            text='{"schema_version":"text2ifc/ifc-property-rerank-decision/0.1",',
            metadata={"provider": "fixture", "stop_reason": "max_tokens"},
        )
        live_result = LiveProviderResult(
            session_id=arguments["session_id"],
            evidence_class="live",
            http_status=200,
            request={"fixture": True},
            response={"stop_reason": "max_tokens"},
            events=({"sequence": 0, "event": "fixture", "data": {}},),
            output=output,
        )
        raise ProviderOutputError(
            "incomplete response",
            live_result=live_result,
        )


class TruncatedOpenAICompatProvider:
    def generate_live(self, **arguments):
        raise OpenAICompatError(
            "truncated response",
            evidence={
                "provider": "deepseek-openai-compatible",
                "evidence_class": "live",
                "failure_class": "truncated",
                "session_id": arguments["session_id"],
                "content_text": '{"schema_version":',
                "finish_reason": "length",
                "request": {"fixture": True},
            },
        )


def _run(tmp_path: Path, provider: Any, **overrides):
    module = _stage_module()
    arguments = {
        "provider": provider,
        "query": _query(),
        "candidate_set": _candidate_set(),
        "output_dir": tmp_path,
        "max_attempts": 2,
    }
    arguments.update(overrides)
    return module.generate_property_resolution_decision(**arguments)


def _json_text(document: dict[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True)


def test_confirmed_stage_is_separate_bounded_and_non_executable(tmp_path: Path) -> None:
    selected = "candidate:1:ifc2x3:Pset_BeamCommon.LoadBearing"
    provider = CapturingProvider(
        [_json_text(_decision("confirmed", selected=selected))]
    )
    result = _run(tmp_path, provider)

    assert result["valid"] is True
    assert result["classification"] == "confirmed"
    assert result["decision"]["selected_candidate_id"] == selected
    assert result["evidence_class"] == "injected_offline"
    assert result["acceptance_eligible"] is False
    assert len(provider.calls) == 1
    call = provider.calls[0]
    assert call["session_id"] == (
        "ifc-property-resolution-run-1-operation-1-claim-1"
    )
    assert call["state"] == {
        "run_id": "run-1",
        "request_id": "request-1",
        "model_id": "model-1",
        "operation_id": "operation-1",
        "claim_id": "claim-1",
        "stage": "ifc_property_resolution",
        "provider_call_ordinal": "property_resolution",
        "attempt": 1,
    }
    assert call["schema"]["$id"] == (
        "text2ifc/ifc-property-rerank-decision/0.1"
    )
    serialized = json.dumps(result, ensure_ascii=False, sort_keys=True).lower()
    assert "exactpropertyintent" not in serialized
    assert "exact_intent" not in serialized

    attempt_dir = tmp_path / "attempt-001"
    assert {path.name for path in attempt_dir.iterdir()} == {
        "renderer-input.json",
        "rendered-prompt.txt",
        "raw-response.json",
        "parsed-response.json",
        "validation-feedback.json",
        "provider-metadata.json",
        "trace.json",
    }
    renderer_input = json.loads(
        (attempt_dir / "renderer-input.json").read_text(encoding="utf-8")
    )
    assert set(renderer_input) == {
        "PROPERTY_QUERY",
        "CANDIDATE_SET",
        "DECISION_SCHEMA",
        "PREVIOUS_VALIDATION_FEEDBACK",
    }
    trace = json.loads((attempt_dir / "trace.json").read_text(encoding="utf-8"))
    assert trace["provider_call_ordinal"] == "property_resolution"
    assert trace["attempt_id"] == (
        "property-resolution-attempt:run-1:operation-1:claim-1:1"
    )
    assert trace["evidence_class"] == "injected_offline"
    assert trace["acceptance_eligible"] is False


@pytest.mark.parametrize(
    ("document", "classification"),
    [
        (
            _decision(
                "clarification_required",
                conflicts=[
                    "candidate:1:ifc2x3:Pset_BeamCommon.LoadBearing",
                    "candidate:2:ifc2x3:Pset_BeamCommon.IsExternal",
                ],
                question="Do you mean load-bearing capacity or external status?",
            ),
            "clarification_required",
        ),
        (_decision("unsupported"), "unsupported"),
    ],
)
def test_nonconfirmed_decisions_never_select_an_executable_candidate(
    tmp_path: Path,
    document: dict[str, Any],
    classification: str,
) -> None:
    result = _run(tmp_path, CapturingProvider([_json_text(document)]))
    assert result["valid"] is True
    assert result["classification"] == classification
    assert result["decision"]["selected_candidate_id"] is None


def test_invalid_first_attempt_is_preserved_and_gets_one_issue_only_retry(
    tmp_path: Path,
) -> None:
    unoffered = _decision(
        "confirmed",
        selected="candidate:9:ifc2x3:Pset_BeamCommon.Invented",
    )
    selected = "candidate:1:ifc2x3:Pset_BeamCommon.LoadBearing"
    provider = CapturingProvider(
        [
            _json_text(unoffered),
            _json_text(_decision("confirmed", selected=selected)),
        ]
    )
    result = _run(tmp_path, provider)

    assert result["valid"] is True
    assert len(provider.calls) == 2
    first_raw = json.loads(
        (tmp_path / "attempt-001/raw-response.json").read_text(encoding="utf-8")
    )
    assert "Invented" in first_raw["text"]
    feedback = json.loads(
        (tmp_path / "attempt-001/validation-feedback.json").read_text(
            encoding="utf-8"
        )
    )
    assert [issue["code"] for issue in feedback] == [
        "PROPERTY_CANDIDATE_NOT_OFFERED"
    ]
    second_input = json.loads(
        (tmp_path / "attempt-002/renderer-input.json").read_text(encoding="utf-8")
    )
    assert second_input["PREVIOUS_VALIDATION_FEEDBACK"] == feedback
    assert "Invented" not in json.dumps(
        second_input["PREVIOUS_VALIDATION_FEEDBACK"],
        ensure_ascii=False,
    )


@pytest.mark.parametrize(
    ("response", "expected_code"),
    [
        ('{"decision":', "JSON_DECODE_ERROR"),
        (
            "```json\n"
            + _json_text(_decision("unsupported"))
            + "\n```",
            "OUTER_JSON_FENCE_REMOVED",
        ),
        (
            _json_text({**_decision("unsupported"), "property_name": "Invented"}),
            "PROPERTY_DECISION_SCHEMA_INVALID",
        ),
        (
            _json_text(
                _decision(
                    "clarification_required",
                    conflicts=[
                        "candidate:1:ifc2x3:Pset_BeamCommon.LoadBearing"
                    ],
                    question="Inspect benchmark_gold before choosing.",
                )
            ),
            "PROPERTY_PRIVATE_OUTPUT_FORBIDDEN",
        ),
    ],
)
def test_malformed_noncanonical_extra_and_private_outputs_fail_without_compatibility(
    tmp_path: Path,
    response: str,
    expected_code: str,
) -> None:
    result = _run(
        tmp_path,
        CapturingProvider([response]),
        max_attempts=1,
    )
    assert result["valid"] is False
    assert result["classification"] == "invalid"
    assert result["error_code"] == "PROPERTY_RESOLUTION_RETRY_EXHAUSTED"
    assert expected_code in {
        issue["code"] for issue in result["attempts"][0]["issues"]
    }
    raw = json.loads(
        (tmp_path / "attempt-001/raw-response.json").read_text(encoding="utf-8")
    )
    assert raw["text"] == response


def test_query_and_candidate_contracts_are_validated_before_provider_factory(
    tmp_path: Path,
) -> None:
    module = _stage_module()
    invalid_query = _query()
    invalid_query["canonical_property"] = "Pset_BeamCommon.LoadBearing"
    constructed = False

    def provider_factory():
        nonlocal constructed
        constructed = True
        return CapturingProvider([])

    result = module.generate_property_resolution_decision(
        provider_factory=provider_factory,
        query=invalid_query,
        candidate_set=_candidate_set(),
        output_dir=tmp_path,
    )
    assert result["valid"] is False
    assert result["error_code"] == "PROPERTY_RESOLUTION_INPUT_INVALID"
    assert constructed is False
    assert not list(tmp_path.glob("attempt-*"))


def test_injected_generate_live_transport_is_permanently_non_live(
    tmp_path: Path,
) -> None:
    selected = "candidate:1:ifc2x3:Pset_BeamCommon.LoadBearing"
    provider = InjectedGenerateLiveProvider(
        _json_text(_decision("confirmed", selected=selected))
    )
    result = _run(tmp_path, provider)
    assert result["valid"] is True
    assert result["evidence_class"] == "injected_offline"
    assert result["acceptance_eligible"] is False
    metadata = json.loads(
        (tmp_path / "attempt-001/provider-metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert metadata["evidence_class"] == "injected_offline"
    assert metadata["acceptance_eligible"] is False


def test_incomplete_live_response_is_preserved_and_rejected(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        IncompleteInjectedLiveProvider(),
        max_attempts=1,
    )
    assert result["valid"] is False
    assert result["attempts"][0]["issues"][0]["code"] == (
        "PROPERTY_PROVIDER_RESPONSE_INCOMPLETE"
    )
    raw = json.loads(
        (tmp_path / "attempt-001/raw-response.json").read_text(encoding="utf-8")
    )
    assert raw["text"].endswith(",")
    assert raw["transport"]["response"]["stop_reason"] == "max_tokens"


def test_deepseek_style_truncation_evidence_is_preserved_and_rejected(
    tmp_path: Path,
) -> None:
    result = _run(
        tmp_path,
        TruncatedOpenAICompatProvider(),
        max_attempts=1,
    )
    assert result["valid"] is False
    assert result["attempts"][0]["issues"][0]["code"] == (
        "PROPERTY_PROVIDER_RESPONSE_INCOMPLETE"
    )
    raw = json.loads(
        (tmp_path / "attempt-001/raw-response.json").read_text(encoding="utf-8")
    )
    assert raw["text"] == '{"schema_version":'
    assert raw["transport"]["failure_class"] == "truncated"


def test_response_size_guard_preserves_raw_output_and_never_reaches_schema(
    tmp_path: Path,
) -> None:
    module = _stage_module()
    oversized = "x" * (module.MAX_PROPERTY_RESOLUTION_RESPONSE_BYTES + 1)
    result = _run(
        tmp_path,
        CapturingProvider([oversized]),
        max_attempts=1,
    )
    assert result["valid"] is False
    assert result["attempts"][0]["issues"][0]["code"] == (
        "PROPERTY_PROVIDER_RESPONSE_TOO_LARGE"
    )
    raw = json.loads(
        (tmp_path / "attempt-001/raw-response.json").read_text(encoding="utf-8")
    )
    assert raw["text"] == oversized
