from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.repair_intent import (
    REPAIR_INTENT_SCHEMA_VERSION_0_4,
    RepairIntent,
    RepairIntentError,
    fingerprint_text,
)


ROOT = Path(__file__).resolve().parents[2]


def _source(excerpt: str = "copy the stated occurrence properties") -> dict:
    return {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": excerpt,
    }


def _property(name: str = "IsExternal", value: object = True) -> dict:
    return {
        "intent_kind": "exact_property",
        "set_name": "Pset_WindowCommon",
        "property_name": name,
        "raw_value": value,
        "raw_unit": None,
        "requested_value_type": None,
        "scope": "occurrence_direct",
        "source": _source(),
    }


def _quantity(name: str = "Width", value: float = 0.915) -> dict:
    return {
        "scope": "window_occurrence",
        "set_name": "BaseQuantities",
        "quantity_name": name,
        "value": value,
        "value_type": "IfcQuantityLength",
        "unit": "m",
        "source": _source(),
    }


def _operation() -> dict:
    return {
        "operation_id": "window-1",
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
        "property_intents": [_property("AcousticRating", "Rw 35")],
        "semantic_bundle_refs": ["window-standard"],
        "quantity_intents": [_quantity("Height", 1.83)],
        "occurrence_reuse_intent": {
            "mode": "exact_occurrence",
            "reference_kind": "global_id",
            "reference": "2abcPublicGuid",
            "include_patterns": ["Pset_WindowCommon.*", "BaseQuantities.*"],
            "source": _source("copy occurrence 2abcPublicGuid"),
        },
        "prototype_intent": None,
        "provenance": [_source()],
    }


def _payload() -> dict:
    return {
        "schema_version": REPAIR_INTENT_SCHEMA_VERSION_0_4,
        "request_id": "occurrence-semantics-04",
        "source_request_hash": fingerprint_text("request"),
        "model_fingerprint": fingerprint_text("model"),
        "prompt_fingerprint": fingerprint_text("prompt"),
        "operations": [_operation()],
        "semantic_bundles": [
            {
                "bundle_id": "window-standard",
                "property_intents": [_property()],
                "quantity_intents": [_quantity()],
                "provenance": [_source()],
            }
        ],
        "provenance": [_source()],
    }


def test_v04_round_trips_frozen_occurrence_semantics() -> None:
    payload = _payload()
    intent = RepairIntent.from_dict(payload, registry=create_default_registry())

    assert intent.to_dict() == payload
    assert intent.semantic_bundles[0].quantity_intents[0].quantity_name == "Width"
    assert intent.operations[0].occurrence_reuse_intent is not None
    assert intent.operations[0].occurrence_reuse_intent.mode == "exact_occurrence"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["semantic_bundles"].append(
            copy.deepcopy(value["semantic_bundles"][0])
        ),
        lambda value: value["operations"][0]["semantic_bundle_refs"].append(
            "window-standard"
        ),
        lambda value: value["operations"][0]["semantic_bundle_refs"].append(
            "missing-bundle"
        ),
    ],
)
def test_v04_rejects_duplicate_or_unknown_bundle_references(mutate) -> None:
    payload = _payload()
    mutate(payload)
    with pytest.raises(RepairIntentError):
        RepairIntent.from_dict(payload, registry=create_default_registry())


def test_v04_enforces_member_and_pattern_bounds_and_complete_quantities() -> None:
    schema = json.loads(
        (ROOT / "schemas/agent/ifc-repair-intent-0.4.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = Draft202012Validator(schema)

    too_many = _payload()
    too_many["semantic_bundles"][0]["property_intents"] = [
        _property(f"P{index}", index) for index in range(129)
    ]
    assert list(validator.iter_errors(too_many))

    too_many_patterns = _payload()
    too_many_patterns["operations"][0]["occurrence_reuse_intent"][
        "include_patterns"
    ] = [f"Pset_{index}.*" for index in range(33)]
    assert list(validator.iter_errors(too_many_patterns))

    incomplete = _payload()
    del incomplete["operations"][0]["quantity_intents"][0]["value"]
    assert list(validator.iter_errors(incomplete))


def test_historical_contracts_remain_loadable() -> None:
    operation = _operation()
    for field in (
        "semantic_bundle_refs",
        "quantity_intents",
        "occurrence_reuse_intent",
    ):
        operation.pop(field)
    payload = {
        "schema_version": "text2ifc/ifc-repair-intent/0.3",
        "request_id": "historical-03",
        "source_request_hash": fingerprint_text("request"),
        "model_fingerprint": fingerprint_text("model"),
        "prompt_fingerprint": fingerprint_text("prompt"),
        "operations": [operation],
        "provenance": [_source()],
    }
    intent = RepairIntent.from_dict(payload, registry=create_default_registry())
    assert intent.to_dict() == payload


def test_v04_prompts_and_registry_forbid_private_authority() -> None:
    intent_prompt = (
        ROOT / "prompts/agent/ifc-repair-intent-v0.4.md"
    ).read_text(encoding="utf-8")
    changeset_prompt = (
        ROOT / "prompts/agent/ifc-repair-changeset-v0.3.md"
    ).read_text(encoding="utf-8")
    registry = json.loads(
        (ROOT / "prompts/agent/registry.json").read_text(encoding="utf-8")
    )
    entries = {item["template_id"]: item for item in registry["templates"]}

    assert "Occurrence reuse is never inferred" in intent_prompt
    assert "never supplies a property value" in " ".join(intent_prompt.split())
    assert "private Ground Truth" in changeset_prompt
    assert "raw_cohort_candidates" in entries[
        "ifc-repair-changeset.v0.3"
    ]["forbidden_outputs"]
    for canary in ("private_original_ifc", "mutation_mapping", "benchmark_gold"):
        assert canary in entries["ifc-repair-intent.v0.4"]["forbidden_outputs"]


def test_bound_changeset_03_has_exact_source_authority_enum() -> None:
    schema = json.loads(
        (ROOT / "schemas/agent/ifc-repair-changeset-0.3.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert schema["$defs"]["assignment"]["properties"]["source_kind"]["enum"] == [
        "explicit_value",
        "deterministic_derived",
        "type_inherited",
        "approved_occurrence_prototype",
        "authorized_type_cohort",
    ]
