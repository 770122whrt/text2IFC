from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.operations import create_default_registry


INTENT_VERSION = "text2ifc/ifc-repair-intent/0.3"
BODY_VERSION = "text2ifc/ifc-repair-intent-body/0.3"


def _source(excerpt: str) -> dict:
    return {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": excerpt,
    }


def _operation(claim: dict) -> dict:
    return {
        "operation_id": "property-operation-1",
        "operation_type": "add_window_with_opening_to_wall",
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcWall"],
            "names": ["North wall"],
        },
        "parameters": {
            "position": {
                "reference": "wall_local_start",
                "center_offset_mm": 1000.0,
            },
            "opening": {
                "width_mm": 915.0,
                "height_mm": 1830.0,
                "sill_height_mm": 305.0,
            },
            "window": {"fit_opening": True},
        },
        "attribute_intents": [],
        "property_intents": [claim],
        "prototype_intent": None,
        "provenance": [_source("在 North wall 添加一个窗户")],
    }


def _natural_claim() -> dict:
    return {
        "intent_kind": "natural_language_property",
        "property_phrase": "标记为外窗",
        "raw_value": True,
        "raw_unit": None,
        "scope": None,
        "source": _source("把这个窗户标记为外窗"),
    }


def _exact_claim() -> dict:
    return {
        "intent_kind": "exact_property",
        "set_name": "Pset_WindowCommon",
        "property_name": "IsExternal",
        "raw_value": True,
        "raw_unit": None,
        "requested_value_type": None,
        "scope": None,
        "source": _source("Pset_WindowCommon.IsExternal=true"),
    }


def _envelope(claim: dict) -> dict:
    module = importlib.import_module("text2ifc_ifc_repair.repair_intent")
    return {
        "schema_version": INTENT_VERSION,
        "request_id": "property-request-03",
        "source_request_hash": module.hash_request("把这个窗户标记为外窗"),
        "model_fingerprint": module.fingerprint_text("recording-model"),
        "prompt_fingerprint": module.fingerprint_text("prompt-0.3"),
        "operations": [_operation(claim)],
        "provenance": [_source("把这个窗户标记为外窗")],
    }


def test_v03_schemas_are_strict_discriminated_contracts() -> None:
    project_root = Path(__file__).resolve().parents[2]
    envelope = json.loads(
        (project_root / "schemas/agent/ifc-repair-intent-0.3.schema.json").read_text(
            encoding="utf-8"
        )
    )
    body = json.loads(
        (
            project_root
            / "schemas/agent/ifc-repair-intent-body-0.3.schema.json"
        ).read_text(encoding="utf-8")
    )

    Draft202012Validator.check_schema(envelope)
    Draft202012Validator.check_schema(body)
    assert envelope["$id"] == INTENT_VERSION
    assert body["$id"] == BODY_VERSION

    valid = {
        "schema_version": BODY_VERSION,
        "operations": [_operation(_natural_claim())],
        "provenance": [_source("把这个窗户标记为外窗")],
    }
    assert not list(Draft202012Validator(body).iter_errors(valid))

    invalid = json.loads(json.dumps(valid))
    invalid["operations"][0]["property_intents"][0][
        "canonical_property_name"
    ] = "IsExternal"
    assert list(Draft202012Validator(body).iter_errors(invalid))


@pytest.mark.parametrize("claim", [_exact_claim(), _natural_claim()])
def test_v03_claims_round_trip_without_authority(claim: dict) -> None:
    module = importlib.import_module("text2ifc_ifc_repair.repair_intent")
    payload = _envelope(claim)

    intent = module.RepairIntent.from_dict(
        payload,
        registry=create_default_registry(),
    )

    assert intent.to_dict() == payload
    parsed = intent.operations[0].property_intents[0]
    assert parsed.intent_kind == claim["intent_kind"]
    if claim["intent_kind"] == "natural_language_property":
        assert parsed.property_phrase == "标记为外窗"
        assert not hasattr(parsed, "set_name")


def test_v03_request_stage_uses_new_prompt_and_keeps_natural_claim(
    tmp_path: Path,
) -> None:
    body = {
        "schema_version": BODY_VERSION,
        "operations": [_operation(_natural_claim())],
        "provenance": [_source("把这个窗户标记为外窗")],
    }

    class Provider:
        def generate_candidate(self, **kwargs) -> ProviderOutput:
            assert kwargs["schema"]["$id"] == BODY_VERSION
            assert "Never choose a canonical Pset" in kwargs["prompt"]
            return ProviderOutput(
                text=json.dumps(body, ensure_ascii=False),
                metadata={"provider": "recording", "model": "recording-model"},
            )

    request_stage = importlib.import_module("text2ifc_ifc_repair.request_stage")
    result = request_stage.generate_repair_intent(
        provider=Provider(),
        request_id="property-request-03",
        repair_request="把这个窗户标记为外窗",
        registry=create_default_registry(),
        output_dir=tmp_path,
        intent_schema_version=INTENT_VERSION,
    )

    assert result["valid"] is True
    assert result["classification"] == "repair_intent"
    claim = result["intent"].operations[0].property_intents[0]
    assert claim.intent_kind == "natural_language_property"
    assert claim.property_phrase == "标记为外窗"
