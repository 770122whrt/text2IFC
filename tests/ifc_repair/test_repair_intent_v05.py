from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.repair_intent import (
    REPAIR_INTENT_SCHEMA_VERSION_0_5,
    RepairIntent,
    RepairIntentError,
    fingerprint_text,
)


ROOT = Path(__file__).resolve().parents[2]


def _source() -> dict:
    return {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": "在北墙中部添加一扇窗",
    }


def _payload() -> dict:
    return {
        "schema_version": REPAIR_INTENT_SCHEMA_VERSION_0_5,
        "request_id": "routing-v05",
        "source_request_hash": fingerprint_text("request"),
        "model_fingerprint": fingerprint_text("model"),
        "prompt_fingerprint": fingerprint_text("prompt"),
        "operations": [
            {
                "operation_id": "window-1",
                "operation_type": "add_window_with_opening_to_wall",
                "routing_intent": {
                    "component_family": "window",
                    "action": "add_with_opening",
                    "operation_profile": "window.add-with-opening.v0.2",
                    "source": _source(),
                },
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
                "property_intents": [],
                "semantic_bundle_refs": [],
                "quantity_intents": [],
                "occurrence_reuse_intent": None,
                "prototype_intent": None,
                "provenance": [_source()],
            }
        ],
        "semantic_bundles": [],
        "provenance": [_source()],
    }


def test_v05_round_trips_routing_source_exactly() -> None:
    payload = _payload()
    intent = RepairIntent.from_dict(payload, registry=create_default_registry())
    assert intent.to_dict() == payload
    assert intent.operations[0].routing_intent is not None
    assert (
        intent.operations[0].routing_intent.operation_profile
        == "window.add-with-opening.v0.2"
    )


@pytest.mark.parametrize(
    ("mutate", "path"),
    [
        (lambda value: value["operations"][0].pop("routing_intent"), "/operations/0"),
        (
            lambda value: value["operations"][0]["routing_intent"].update(
                {"invented": True}
            ),
            "/operations/0/routing_intent",
        ),
        (
            lambda value: value["operations"][0]["routing_intent"].update(
                {"component_family": "Window"}
            ),
            "/operations/0/routing_intent/component_family",
        ),
    ],
)
def test_v05_rejects_missing_extra_or_malformed_routing(mutate, path) -> None:
    payload = _payload()
    mutate(payload)
    with pytest.raises(RepairIntentError) as captured:
        RepairIntent.from_dict(payload, registry=create_default_registry())
    assert captured.value.path == path


def test_v05_adds_door_scope_without_mutating_historical_contracts() -> None:
    manifest_03 = json.loads(
        (ROOT / "schemas/agent/ifc-repair-semantic-manifest-0.3.schema.json").read_text(
            encoding="utf-8"
        )
    )
    manifest_02 = json.loads(
        (ROOT / "schemas/agent/ifc-repair-semantic-manifest-0.2.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert "door_occurrence" in manifest_03["$defs"]["assignment"]["properties"][
        "scope"
    ]["enum"]
    assert "door_occurrence" not in manifest_02["$defs"]["assignment"]["properties"][
        "scope"
    ]["enum"]
    Draft202012Validator.check_schema(manifest_03)


def test_v04_still_rejects_routing_field() -> None:
    payload = copy.deepcopy(_payload())
    payload["schema_version"] = "text2ifc/ifc-repair-intent/0.4"
    with pytest.raises(RepairIntentError):
        RepairIntent.from_dict(payload, registry=create_default_registry())
