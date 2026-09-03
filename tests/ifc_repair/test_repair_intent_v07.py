from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.prompt_profiles import (
    compact_profile_catalog,
    load_prompt_profiles,
    select_prompt_profiles,
)
from text2ifc_ifc_repair.repair_intent import (
    RepairIntent,
    fingerprint_text,
    hash_request,
    load_repair_intent_body_schema,
    load_repair_intent_schema,
)
from text2ifc_ifc_repair.request_stage import generate_repair_intent


BODY_VERSION = "text2ifc/ifc-repair-intent-body/0.7"
ENVELOPE_VERSION = "text2ifc/ifc-repair-intent/0.7"
PROMPT_ID = "ifc-repair-intent.v0.7"
PROFILE_SCHEMA_VERSION = "text2ifc/ifc-repair-prompt-profile/0.2"
PROFILE_IDS = ("beam.add.v0.3", "column.add.v0.3")
CASES_PATH = Path(__file__).parent / "fixtures" / "phase12_type_intent_cases.json"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE = {
    "source_kind": "user_request",
    "reference": "request:/text",
    "excerpt": "EXAMPLE_ONLY",
}


class Provider:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls: list[dict] = []

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        self.calls.append(kwargs)
        return ProviderOutput(
            text=json.dumps(self.response, ensure_ascii=False),
            metadata={"provider": "fixture", "model": "type-intent-red"},
        )


def _routing(family: str) -> dict:
    return {
        "component_family": family,
        "action": "add",
        "operation_profile": f"{family}.add.v0.3",
        "source": SOURCE,
    }


def _operation(
    family: str,
    *,
    operation_id: str | None = None,
    prototype_intent: dict | None = None,
) -> dict:
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
                "width_mm": 500,
                "depth_mm": 500,
            },
        }
    return {
        "operation_id": operation_id or f"{family}-1",
        "operation_type": f"add_{family}",
        "routing_intent": _routing(family),
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
        "prototype_intent": prototype_intent,
        "provenance": [SOURCE],
    }


def _body(*operations: dict) -> dict:
    return {
        "schema_version": BODY_VERSION,
        "operations": list(operations),
        "unsupported_requests": [],
        "semantic_bundles": [],
        "provenance": [SOURCE],
    }


def _envelope(body: dict) -> dict:
    return {
        "schema_version": ENVELOPE_VERSION,
        "request_id": "type-intent-request",
        "source_request_hash": hash_request("EXAMPLE_ONLY"),
        "model_fingerprint": fingerprint_text("model"),
        "prompt_fingerprint": fingerprint_text("prompt"),
        "operations": body["operations"],
        "unsupported_requests": body["unsupported_requests"],
        "semantic_bundles": body["semantic_bundles"],
        "provenance": body["provenance"],
    }


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_type_intent_failure_family_is_frozen_with_the_live_phrase() -> None:
    matrix = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = matrix["cases"]
    assert matrix["schema_version"] == "text2ifc/phase12-type-intent-cases/0.1"
    assert len(cases) == 7
    assert len({case["case_id"] for case in cases}) == 7
    live = next(
        case
        for case in cases
        if case["case_id"] == "live-complete-dedicated-structural-types"
    )
    assert "generate dedicated structural Types" in live["user_text"]
    assert live["expected_prototype_intent"] == [None, None]
    assert {case["expected_state"] for case in cases} == {
        "generated_type",
        "exact_reuse",
        "selection_required",
    }


def test_v07_is_append_only_and_preserves_v06_registered_bytes() -> None:
    assert load_repair_intent_schema(ENVELOPE_VERSION)["$id"] == ENVELOPE_VERSION
    assert load_repair_intent_body_schema(BODY_VERSION)["$id"] == BODY_VERSION
    assert load_repair_intent_schema("text2ifc/ifc-repair-intent/0.6")["$id"] == (
        "text2ifc/ifc-repair-intent/0.6"
    )
    assert _sha256(
        PROJECT_ROOT / "prompts" / "agent" / "ifc-repair-intent-v0.6.md"
    ) == "sha256:997a59854ea34ba5bdc6993900da1d7c1b98b8232bbf02c719acff61bacde754"
    assert _sha256(
        PROJECT_ROOT
        / "prompts"
        / "agent"
        / "ifc-repair-profiles"
        / "beam.add.v0.2.json"
    ) == "sha256:3cd48523388f4b020b4a76f190d9e9ea17045910a9637e61dec869316b763f86"


@pytest.mark.parametrize(
    ("family", "prototype_intent"),
    [
        ("beam", None),
        ("column", None),
        (
            "beam",
            {
                "reference_kind": "type_name",
                "reference": "BEAM_TYPE_EXAMPLE",
                "source": SOURCE,
            },
        ),
        (
            "column",
            {
                "reference_kind": "global_id",
                "reference": "0COLUMN_TYPE_EXAMPLE01",
                "source": SOURCE,
            },
        ),
        (
            "beam",
            {
                "reference_kind": "selection_required",
                "reference": "existing Beam Type",
                "source": SOURCE,
            },
        ),
    ],
)
def test_v07_round_trips_all_three_representation_states(
    family: str, prototype_intent: dict | None
) -> None:
    document = _envelope(_body(_operation(family, prototype_intent=prototype_intent)))
    intent = RepairIntent.from_dict(
        document,
        registry=create_default_registry(),
        require_complete=False,
    )
    assert intent.to_dict()["operations"][0]["prototype_intent"] == prototype_intent


def test_v07_stage1_exposes_type_rules_in_compact_profiles_not_few_shots(
    tmp_path: Path,
) -> None:
    body = _body(_operation("beam"), _operation("column"))
    provider = Provider(body)
    result = generate_repair_intent(
        provider=provider,
        request_id="type-intent-stage1",
        repair_request=(
            "Add the specified Beam and Column on Level 1 and generate "
            "dedicated structural Types."
        ),
        registry=create_default_registry(),
        output_dir=tmp_path,
        max_attempts=1,
        intent_schema_version=ENVELOPE_VERSION,
    )

    assert result["valid"] is True
    assert [
        operation.prototype_intent for operation in result["intent"].operations
    ] == [None, None]
    renderer_input = json.loads(
        (tmp_path / "renderer-input.json").read_text(encoding="utf-8")
    )
    catalog = renderer_input["SUPPORTED_OPERATIONS"]
    structural = {
        item["profile_id"]: item
        for item in catalog
        if item["operation_type"] in {"add_beam", "add_column"}
    }
    assert set(structural) == set(PROFILE_IDS)
    for profile in structural.values():
        assert profile["type_intent_rules"] == {
            "no_type_or_new_type": "prototype_intent_null",
            "exact_existing_type_reuse": "global_id_or_type_name",
            "unspecified_existing_type_reuse": "selection_required",
            "zero_candidate_policy": "missing_evidence",
        }
        assert "few_shots" not in profile
    serialized = json.dumps(renderer_input, ensure_ascii=False)
    assert "beam.add.v0.3.complete" not in serialized
    assert "column.add.v0.3.complete" not in serialized


def test_stage1_never_rewrites_selection_required_from_provider_output(
    tmp_path: Path,
) -> None:
    wrong_for_request = {
        "reference_kind": "selection_required",
        "reference": "dedicated structural Types",
        "source": SOURCE,
    }
    body = _body(
        _operation("beam", prototype_intent=wrong_for_request),
        _operation("column", prototype_intent=wrong_for_request),
    )
    result = generate_repair_intent(
        provider=Provider(body),
        request_id="type-intent-no-rewrite",
        repair_request=(
            "Add the specified Beam and Column on Level 1 and generate "
            "dedicated structural Types."
        ),
        registry=create_default_registry(),
        output_dir=tmp_path,
        max_attempts=1,
        intent_schema_version=ENVELOPE_VERSION,
    )

    assert result["valid"] is True
    assert [
        operation.to_dict()["prototype_intent"]
        for operation in result["intent"].operations
    ] == [wrong_for_request, wrong_for_request]
    assert result["attempts"][0]["normalizations"] == []


def test_v07_prompt_states_the_three_type_states_without_compatibility() -> None:
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
        "create, generate, or dedicate a new Type",
        "`prototype_intent` must be exactly `null`",
        "exact existing Type name or GlobalId",
        "`selection_required`",
        "candidates exist",
        "zero candidates",
        "`missing_evidence`",
        "Never rewrite or normalize",
    ):
        assert exact in rendered


def test_v03_profiles_use_new_schema_and_stage2_loads_only_bound_few_shots() -> None:
    profiles = load_prompt_profiles()
    compact = {
        item["profile_id"]: item
        for item in compact_profile_catalog(profiles, include_profile_ids=PROFILE_IDS)
    }
    assert set(compact) == set(PROFILE_IDS)
    for profile_id in PROFILE_IDS:
        profile = profiles[profile_id]
        assert profile.document["schema_version"] == PROFILE_SCHEMA_VERSION
        assert profile.profile_version == "0.3"
        assert "type_intent_rules" in compact[profile_id]

    selected = select_prompt_profiles(PROFILE_IDS)
    assert selected.profile_ids == PROFILE_IDS
    assert set(selected.few_shot_ids) == {
        "beam.add.v0.3.complete",
        "beam.add.v0.3.clarification",
        "beam.add.v0.3.type-reuse",
        "beam.add.v0.3.unsupported",
        "column.add.v0.3.complete",
        "column.add.v0.3.clarification",
        "column.add.v0.3.type-reuse",
        "column.add.v0.3.unsupported",
    }
    assert all(
        example["profile_id"] in PROFILE_IDS for example in selected.few_shots
    )


def test_default_registry_binds_current_structural_profiles_only() -> None:
    registry = create_default_registry()
    assert registry.require("add_beam").prompt_profile_id == "beam.add.v0.3"
    assert registry.require("add_column").prompt_profile_id == "column.add.v0.3"
    assert registry.require("add_door_with_opening_to_wall").prompt_profile_id == (
        "door.add-with-opening.v0.2"
    )
