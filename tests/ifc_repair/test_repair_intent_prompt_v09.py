from __future__ import annotations

import json
from pathlib import Path

from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_ifc_repair.repair_intent import REPAIR_INTENT_SCHEMA_VERSION_0_8
from text2ifc_ifc_repair.request_stage import _INTENT_CONTRACTS


PROMPT_ID = "ifc-repair-intent.v0.9"
CASES_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "phase12_stage1_property_value_contract_cases.json"
)


def test_v09_is_current_for_v08_schema_and_freezes_property_value_contract() -> None:
    assert _INTENT_CONTRACTS[REPAIR_INTENT_SCHEMA_VERSION_0_8][1] == PROMPT_ID

    rendered = render_prompt(
        template_id=PROMPT_ID,
        inputs={
            "REPAIR_REQUEST": "EXAMPLE_ONLY",
            "SUPPORTED_OPERATIONS": [],
            "REPAIR_INTENT_SCHEMA": {},
            "VALIDATION_FEEDBACK": [],
        },
    )["text"]

    for exact in (
        "Property identity and requested value are independent claims",
        "Never replace an explicitly stated scalar with `null`",
        "Unambiguous affirmative Boolean property assertions",
        "Explicitly negated Boolean property assertions",
        "If a property is named but no value is stated",
        "Do not infer a value from a property name alone",
    ):
        assert exact in rendered


def test_property_value_failure_family_covers_boolean_literal_and_missing_value() -> None:
    matrix = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    assert matrix["schema_version"] == (
        "text2ifc/phase12-stage1-property-value-contract-cases/0.1"
    )
    cases = matrix["cases"]
    assert {item["family"] for item in cases} == {
        "window",
        "door",
        "wall",
        "beam",
        "column",
    }
    assert {type(item["expected_raw_value"]) for item in cases} == {
        bool,
        str,
        int,
        type(None),
    }
    assert {item["expected_route"] for item in cases} == {
        "property_resolution",
        "value_clarification",
    }
