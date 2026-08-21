from __future__ import annotations

import json
from pathlib import Path

from text2ifc_agent.prompt_registry import load_prompt_registry, render_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ID = "ifc-property-resolution.v0.1"


def test_property_resolution_prompt_has_exactly_four_public_inputs() -> None:
    entry = load_prompt_registry()[TEMPLATE_ID]
    assert entry["required_inputs"] == [
        "PROPERTY_QUERY",
        "CANDIDATE_SET",
        "DECISION_SCHEMA",
        "PREVIOUS_VALIDATION_FEEDBACK",
    ]
    rendered = render_prompt(
        template_id=TEMPLATE_ID,
        inputs={
            "PROPERTY_QUERY": {"property_phrase": "test phrase"},
            "CANDIDATE_SET": {"candidates": []},
            "DECISION_SCHEMA": {"type": "object"},
            "PREVIOUS_VALIDATION_FEEDBACK": [],
            "IGNORED_PRIVATE_INPUT": "benchmark_gold",
        },
    )
    assert set(rendered["inputs"]) == set(entry["required_inputs"])
    assert "benchmark_gold" not in rendered["text"]
    assert "IGNORED_PRIVATE_INPUT" not in rendered["text"]


def test_prompt_contains_no_family_phrase_mapping_or_compatibility_instruction() -> None:
    prompt = (
        PROJECT_ROOT / "prompts/agent/ifc-property-resolution-v0.1.md"
    ).read_text(encoding="utf-8")
    casefolded = prompt.casefold()
    for forbidden in (
        "外窗",
        "load bearing",
        "loadbearing",
        "reviewed alias",
        "property_aliases",
        "compatibility mapping",
    ):
        assert forbidden not in casefolded
    assert "select exactly one" in casefolded
    assert "offered candidate" in casefolded
    assert "fix only the listed validation errors" in casefolded
    assert "do not rename" in casefolded


def test_decision_schema_cannot_carry_executable_property_fields() -> None:
    schema = json.loads(
        (
            PROJECT_ROOT
            / "schemas/agent/ifc-property-rerank-decision-0.1.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert schema["additionalProperties"] is False
    properties = set(schema["properties"])
    assert properties == {
        "schema_version",
        "decision",
        "selected_candidate_id",
        "conflicting_candidate_ids",
        "clarification_question",
    }
    assert not properties.intersection(
        {
            "set_name",
            "property_name",
            "value_type",
            "value",
            "unit",
            "scope",
            "operation",
            "exact_intent",
        }
    )
