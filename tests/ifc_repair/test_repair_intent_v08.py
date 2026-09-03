from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path
from typing import Any

from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.repair_intent import (
    load_repair_intent_body_schema,
    load_repair_intent_schema,
)
from text2ifc_ifc_repair.request_stage import generate_repair_intent


BODY_VERSION = "text2ifc/ifc-repair-intent-body/0.8"
ENVELOPE_VERSION = "text2ifc/ifc-repair-intent/0.8"
PROMPT_ID = "ifc-repair-intent.v0.8"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = (
    Path(__file__).parent / "fixtures" / "phase12_stage1_clause_role_cases.json"
)
SOURCE = {
    "source_kind": "user_request",
    "reference": "request:/text",
    "excerpt": "EXAMPLE_ONLY",
}
CURRENT_PROFILE_IDS = {
    "beam.add.v0.3",
    "column.add.v0.3",
    "door.add-with-opening.v0.2",
    "door.fill-existing-opening.v0.2",
    "occurrence.set-properties",
    "opening.add-to-wall",
    "window.add-with-opening",
}


class Provider:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def generate_candidate(self, **kwargs: Any) -> ProviderOutput:
        self.calls.append(kwargs)
        return ProviderOutput(
            text=json.dumps(self.response, ensure_ascii=False),
            metadata={"provider": "fixture", "model": "clause-role-red"},
        )


def _operation(family: str) -> dict[str, Any]:
    if family == "beam":
        parameters = {
            "axis": {
                "start": {"x_mm": 0, "y_mm": 0, "z_mm": 3000},
                "end": {"x_mm": 6000, "y_mm": 0, "z_mm": 3000},
            },
            "section": {
                "shape": "rectangle",
                "width_mm": 300,
                "height_mm": 500,
            },
        }
    else:
        parameters = {
            "axis": {
                "base": {"x_mm": 1000, "y_mm": 2000, "z_mm": 0},
                "top": {"x_mm": 1000, "y_mm": 2000, "z_mm": 3000},
            },
            "section": {
                "shape": "rectangle",
                "width_mm": 400,
                "depth_mm": 600,
                "orientation": {"x": 0, "y": 1},
            },
        }
    return {
        "operation_id": f"{family}-1",
        "operation_type": f"add_{family}",
        "routing_intent": {
            "component_family": family,
            "action": "add",
            "operation_profile": f"{family}.add.v0.3",
            "source": SOURCE,
        },
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcBuildingStorey"],
            "names": ["Level 1"],
        },
        "parameters": parameters,
        "attribute_intents": [],
        "property_intents": [],
        "semantic_bundle_refs": [],
        "quantity_intents": [],
        "occurrence_reuse_intent": None,
        "prototype_intent": None,
        "provenance": [SOURCE],
    }


def _body() -> dict[str, Any]:
    return {
        "schema_version": BODY_VERSION,
        "operations": [_operation("beam"), _operation("column")],
        "unsupported_requests": [],
        "semantic_bundles": [],
        "provenance": [SOURCE],
    }


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _normalized_version(document: dict[str, Any], version: str) -> dict[str, Any]:
    serialized = json.dumps(document, sort_keys=True)
    return json.loads(serialized.replace(version, "VERSION"))


def test_clause_role_failure_family_is_frozen_but_not_an_exhaustive_deny_list() -> None:
    matrix = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    assert matrix["schema_version"] == (
        "text2ifc/phase12-stage1-clause-role-cases/0.1"
    )
    assert matrix["negative_examples_are_exhaustive"] is False

    positives = matrix["positive_cases"]
    transaction_cases = [
        case
        for case in positives
        if case["clause_role"] == "compatible_transaction_constraint"
    ]
    assert len(transaction_cases) == 7
    assert all(case["expected_unsupported_count"] == 0 for case in positives)
    assert {
        "Create both in one atomic ChangeSet.",
        "Add the specified Beam and Column in the same ChangeSet.",
        "Add the specified Beam and Column in one transaction.",
        "Create the specified Beam and Column together atomically.",
        "Add the specified Beam and Column all-or-nothing.",
        "Publish both the specified Beam and Column or neither.",
    } <= {case["request"] for case in transaction_cases}

    four_family = next(
        case for case in positives if case["case_id"] == "four-family-atomic"
    )
    assert four_family["expected_operation_types"] == [
        "add_window_with_opening_to_wall",
        "add_door_with_opening_to_wall",
        "add_beam",
        "add_column",
    ]
    negatives = matrix["representative_negative_cases"]
    assert {case["expected_capability_id"] for case in negatives if "expected_capability_id" in case} >= {
        "structural_analysis_node",
        "curved",
        "grid_placement",
        "unregistered_operation",
    }


def test_v08_is_append_only_and_has_the_same_json_shape_as_v07() -> None:
    envelope_v08 = load_repair_intent_schema(ENVELOPE_VERSION)
    body_v08 = load_repair_intent_body_schema(BODY_VERSION)
    assert envelope_v08["$id"] == ENVELOPE_VERSION
    assert body_v08["$id"] == BODY_VERSION

    envelope_v07 = load_repair_intent_schema(
        "text2ifc/ifc-repair-intent/0.7"
    )
    body_v07 = load_repair_intent_body_schema(
        "text2ifc/ifc-repair-intent-body/0.7"
    )
    assert _normalized_version(envelope_v08, "0.8") == _normalized_version(
        envelope_v07, "0.7"
    )
    assert _normalized_version(body_v08, "0.8") == _normalized_version(
        body_v07, "0.7"
    )
    assert "transaction_constraints" not in json.dumps(body_v08)

    assert _sha256(
        PROJECT_ROOT / "prompts" / "agent" / "ifc-repair-intent-v0.7.md"
    ) == "sha256:49a518ec482eddb7d187584232d81602514f7e7ced97ee1eabaf79b8e88938bb"
    assert _sha256(
        PROJECT_ROOT
        / "schemas"
        / "agent"
        / "ifc-repair-intent-0.7.schema.json"
    ) == "sha256:8658fa486b44513bdb2fd14a36c01e1657f47e879ed0f25b3a7e36c32c6a412d"
    assert _sha256(
        PROJECT_ROOT
        / "schemas"
        / "agent"
        / "ifc-repair-intent-body-0.7.schema.json"
    ) == "sha256:441402349e205848456cda76a51d82ebc8f2967258f3104da7495fd751091f80"


def test_v08_prompt_teaches_roles_with_representative_micro_shapes() -> None:
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
        "semantic object",
        "Registered model operation",
        "Operation content or modifier",
        "Compatible transaction or execution constraint",
        "Unsupported requested result",
        "one atomic ChangeSet",
        "same ChangeSet",
        "one transaction",
        "together atomically",
        "all-or-nothing",
        "publish both or neither",
        "operations=[add_beam, add_column]",
        "unsupported_requests=[]",
        "structural_analysis_node",
        "unregistered_operation",
        "representative, not exhaustive",
        "user may say `rectangular`",
        "Provider JSON must emit `rectangle`",
    ):
        assert exact in rendered
    assert "beam.add.v0.2" not in rendered
    assert "beam.add.v0.3.complete" not in rendered
    assert "column.add.v0.3.complete" not in rendered


def test_v08_stage1_uses_every_current_compact_profile_without_full_fewshots(
    tmp_path: Path,
) -> None:
    provider = Provider(_body())
    result = generate_repair_intent(
        provider=provider,
        request_id="clause-role-stage1",
        repair_request=(
            "Add the specified Beam and Column on Level 1 in one atomic "
            "ChangeSet."
        ),
        registry=create_default_registry(),
        output_dir=tmp_path,
        max_attempts=1,
        intent_schema_version=ENVELOPE_VERSION,
    )

    assert result["valid"] is True
    assert [
        operation.operation_type for operation in result["intent"].operations
    ] == ["add_beam", "add_column"]
    assert result["intent"].unsupported_requests == ()
    assert len(provider.calls) == 1

    renderer_input = json.loads(
        (tmp_path / "renderer-input.json").read_text(encoding="utf-8")
    )
    catalog = renderer_input["SUPPORTED_OPERATIONS"]
    assert {item["profile_id"] for item in catalog} == CURRENT_PROFILE_IDS
    assert all("few_shots" not in item for item in catalog)
    serialized = json.dumps(renderer_input, ensure_ascii=False)
    assert "beam.add.v0.3.complete" not in serialized
    assert "door.add-with-opening.v0.2.complete" not in serialized


def test_repair_api_defaults_to_v08_without_mutating_v07_callers() -> None:
    default = inspect.signature(RepairAPI.__init__).parameters[
        "intent_schema_version"
    ].default
    assert default == ENVELOPE_VERSION
