import importlib
import importlib.util
import json
from pathlib import Path

import pytest

from text2ifc_agent.providers import FakeAgentProvider, ProviderOutputError
from text2ifc_agent.prompt_registry import PromptRegistryError


ROOT = Path(__file__).resolve().parents[2]
FORMAL_FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "minimal.json"


def _module(name):
    module_name = f"text2ifc_agent.{name}"
    assert importlib.util.find_spec(module_name) is not None, (
        f"{module_name} implementation is missing"
    )
    return importlib.import_module(module_name)


def _brief():
    return {
        "schema_version": "text2ifc/design-brief/1.0",
        "language": "zh-CN",
        "original_request": "创建一面长5米、高3米、厚0.2米的墙。",
        "known_facts": {
            "wall": {"length_mm": 5000, "height_mm": 3000, "thickness_mm": 200}
        },
        "missing_facts": [],
        "ambiguities": [],
        "user_corrections": [],
        "clarification_questions": [],
        "provenance": {"source": "user_request"},
    }


def _trace_paths():
    return {
        "renderer_input_path": "prompt-render-input.json",
        "rendered_prompt_path": "prompt-rendered.md",
        "raw_response_path": "raw-response.txt",
        "parsed_response_path": "candidate.json",
        "validation_feedback_path": "validation-feedback.json",
        "metrics_path": "metrics.json",
        "artifact_paths": {"input": "input.txt"},
    }


def _generate(provider, **overrides):
    generator = _module("generator")
    kwargs = {
        "session_id": "case-1",
        "provider": provider,
        "design_brief": _brief(),
        "schema_summary": {"schema_version": "bim-json/2.0"},
        "capability_profile": {"target": "IFC2X3"},
        "few_shots": [],
        "validation_feedback": [],
        "geometry_feedback": [],
        "trace_paths": _trace_paths(),
    }
    kwargs.update(overrides)
    return generator.generate_bim_json_candidate(**kwargs)


def test_generator_requires_prompt_trace():
    formal = FORMAL_FIXTURE.read_text(encoding="utf-8")
    provider = FakeAgentProvider({"case-1": {"text": formal}})

    with pytest.raises(PromptRegistryError, match="renderer_input_path"):
        _generate(provider, trace_paths={})


def test_generator_rejects_raw_ifc_output():
    provider = FakeAgentProvider(
        {"case-1": {"text": "ISO-10303-21; DATA; #1=IFCOWNERHISTORY(); ENDSEC;"}}
    )

    with pytest.raises(ProviderOutputError):
        _generate(provider)


def test_generator_accepts_formal_and_draft_provider_outputs():
    formal = json.loads(FORMAL_FIXTURE.read_text(encoding="utf-8"))
    formal_provider = FakeAgentProvider(
        {"case-1": {"text": json.dumps(formal, ensure_ascii=False)}}
    )
    formal_result = _generate(formal_provider)

    partial = json.loads(json.dumps(formal))
    partial["entities"][1]["attributes"]["ObjectPlacement"] = {
        "relative_to": "project-1"
    }
    draft = {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": partial,
        "missing_facts": [
            {
                "entity_id": "wall-1",
                "path": "/entities/1/attributes/ObjectPlacement/origin",
                "code": "MISSING_PLACEMENT_ORIGIN",
                "message": "用户尚未提供墙体原点。",
            }
        ],
        "losses": [],
        "clarification_targets": [
            {
                "entity_id": "wall-1",
                "path": "/entities/1/attributes/ObjectPlacement/origin",
                "question": "墙体原点相对楼层位于哪里？",
            }
        ],
        "provenance": {"source": "provider"},
    }
    draft_provider = FakeAgentProvider(
        {"case-1": {"text": json.dumps(draft, ensure_ascii=False)}}
    )
    draft_result = _generate(draft_provider)

    assert formal_result.status == "formal"
    assert formal_result.diagnostics == []
    assert draft_result.status == "draft"
    assert draft_result.diagnostics == []


def test_successful_first_pass_records_no_repair_needed():
    routing = _module("failure_routing")

    result = routing.route_generation_failure(
        previous_candidate={"schema_version": "bim-json/2.0"},
        validation_feedback=[],
        geometry_feedback=[],
        known_facts=_brief()["known_facts"],
    )

    assert result["route"] == "no_repair_needed"
    assert result["repair_attempts"] == []


def test_repair_attempt_decreases_issue_count():
    routing = _module("failure_routing")
    input_feedback = [
        {
            "code": "WALL_BBOX_MISMATCH",
            "required_fact_paths": ["/wall/length_mm"],
        },
        {
            "code": "WALL_ORIENTATION_MISMATCH",
            "required_fact_paths": ["/wall/length_mm"],
        },
    ]

    result = routing.route_generation_failure(
        previous_candidate={"schema_version": "bim-json/2.0"},
        validation_feedback=[],
        geometry_feedback=input_feedback,
        known_facts=_brief()["known_facts"],
        repaired_candidate={"schema_version": "bim-json/2.0"},
        repaired_feedback=[input_feedback[1]],
    )

    assert result["route"] == "repair_attempted"
    attempt = result["repair_attempts"][0]
    assert attempt["input_issue_count"] == 2
    assert attempt["output_issue_count"] == 1
    assert attempt["fixed_issue_codes"] == ["WALL_BBOX_MISMATCH"]


def test_missing_known_fact_routes_to_draft_without_invention():
    routing = _module("failure_routing")

    result = routing.route_generation_failure(
        previous_candidate={"schema_version": "bim-json/2.0"},
        validation_feedback=[
            {
                "code": "ROOM_WIDTH_MISSING",
                "required_fact_paths": ["/space/width_mm"],
                "question": "房间宽度是多少？",
            }
        ],
        geometry_feedback=[],
        known_facts={"object_kind": "room"},
    )

    assert result["route"] == "draft_required"
    assert result["repair_attempts"] == []
    assert result["missing_fact_paths"] == ["/space/width_mm"]
