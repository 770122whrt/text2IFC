from __future__ import annotations

import json
from pathlib import Path

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.provider_stage import generate_bound_changeset
from text2ifc_ifc_repair.request_stage import generate_repair_intent


class Provider:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls: list[dict] = []

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        self.calls.append(kwargs)
        return ProviderOutput(
            text=json.dumps(self.response, ensure_ascii=False),
            metadata={"provider": "fixture", "model": "fixture-model"},
        )


def _source() -> dict:
    return {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": "add a 900 by 1200 window to North wall",
    }


def _v05_body() -> dict:
    return {
        "schema_version": "text2ifc/ifc-repair-intent-body/0.5",
        "operations": [
            {
                "operation_id": "window-1",
                "operation_type": "add_window_with_opening_to_wall",
                "routing_intent": {
                    "component_family": "window",
                    "action": "add_with_opening",
                    "operation_profile": "window.add-with-opening",
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
                        "center_offset_mm": 1000,
                    },
                    "opening": {
                        "width_mm": 900,
                        "height_mm": 1200,
                        "sill_height_mm": 900,
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


def _v05_fill_body(*, parameters: dict | None = None) -> dict:
    source = {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": "fill Opening OPENING-GUID using DoorStyle DOOR-TYPE-GUID",
    }
    return {
        "schema_version": "text2ifc/ifc-repair-intent-body/0.5",
        "operations": [
            {
                "operation_id": "door-fill-1",
                "operation_type": "fill_existing_opening_with_door",
                "routing_intent": {
                    "component_family": "door",
                    "action": "fill_existing_opening",
                    "operation_profile": "door.fill-existing-opening.v0.2",
                    "source": source,
                },
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": ["IfcOpeningElement"],
                    "global_id": "OPENING-GUID",
                },
                "parameters": {} if parameters is None else parameters,
                "attribute_intents": [],
                "property_intents": [],
                "semantic_bundle_refs": [],
                "quantity_intents": [],
                "occurrence_reuse_intent": None,
                "prototype_intent": {
                    "reference_kind": "global_id",
                    "reference": "DOOR-TYPE-GUID",
                    "source": source,
                },
                "provenance": [source],
            }
        ],
        "semantic_bundles": [],
        "provenance": [source],
    }


def _v05_unsupported_door_body() -> dict:
    body = _v05_fill_body(
        parameters={"door": {"operation_type": "REVOLVING"}}
    )
    operation = body["operations"][0]
    operation["operation_type"] = "add_door_with_opening_to_wall"
    operation["routing_intent"].update(
        {
            "action": "add_with_opening",
            "operation_profile": "door.add-with-opening.v0.2",
        }
    )
    operation["target_query"] = {
        "schema_version": "text2ifc/ifc-target-query/0.1",
        "allowed_ifc_classes": ["IfcWall"],
        "global_id": "WALL-GUID",
    }
    operation["prototype_intent"] = None
    return body


def test_stage1_routes_and_extracts_in_exactly_one_provider_call(
    tmp_path: Path,
) -> None:
    provider = Provider(_v05_body())
    result = generate_repair_intent(
        provider=provider,
        request_id="profile-stage1",
        repair_request="add a 900 by 1200 window to North wall",
        registry=create_default_registry(),
        output_dir=tmp_path,
        intent_schema_version="text2ifc/ifc-repair-intent/0.5",
    )
    assert result["valid"] is True
    assert len(provider.calls) == 1
    renderer_input = json.loads(
        (tmp_path / "renderer-input.json").read_text(encoding="utf-8")
    )
    catalog = renderer_input["SUPPORTED_OPERATIONS"]
    assert {item["profile_id"] for item in catalog} == {
        "window.add-with-opening",
        "opening.add-to-wall",
        "door.add-with-opening.v0.2",
        "door.fill-existing-opening.v0.2",
        "occurrence.set-properties",
        "beam.add",
        "column.add",
    }
    serialized = json.dumps(catalog)
    assert "EXAMPLE_ONLY" not in serialized
    assert "user_text" not in serialized


def test_stage1_fill_uses_retained_opening_as_program_derived_geometry(
    tmp_path: Path,
) -> None:
    provider = Provider(_v05_fill_body())

    result = generate_repair_intent(
        provider=provider,
        request_id="profile-stage1-fill",
        repair_request=(
            "fill Opening OPENING-GUID using DoorStyle DOOR-TYPE-GUID"
        ),
        registry=create_default_registry(),
        output_dir=tmp_path,
        intent_schema_version="text2ifc/ifc-repair-intent/0.5",
    )

    assert result["valid"] is True
    assert result["classification"] == "repair_intent"
    assert result["missing_parameters"] == []
    assert result["intent"].operations[0].to_dict()["parameters"] == {
        "fit_existing_opening": True
    }
    catalog = json.loads(
        (tmp_path / "renderer-input.json").read_text(encoding="utf-8")
    )["SUPPORTED_OPERATIONS"]
    fill = next(
        item
        for item in catalog
        if item["operation_type"] == "fill_existing_opening_with_door"
    )
    assert fill["intent_parameter_schema"]["additionalProperties"] is False
    assert fill["intent_parameter_schema"]["required"] == [
        "fit_existing_opening"
    ]
    assert "/parameters/position" in fill["program_derived_slots"]
    assert "/parameters/opening" in fill["program_derived_slots"]


def test_stage1_fill_rejects_non_contract_door_parameter_aliases(
    tmp_path: Path,
) -> None:
    body = _v05_fill_body(
        parameters={
            "opening": {"center_offset_from_wall_start_mm": 1657.5},
            "door": {"threshold_height_mm": 0},
        }
    )

    result = generate_repair_intent(
        provider=Provider(body),
        request_id="profile-stage1-fill-alias",
        repair_request="fill the retained Opening with a Door",
        registry=create_default_registry(),
        output_dir=tmp_path,
        max_attempts=1,
        intent_schema_version="text2ifc/ifc-repair-intent/0.5",
    )

    assert result["valid"] is False
    assert result["attempts"][0]["issues"][0]["code"] == (
        "REPAIR_INTENT_PARAMETER_SCHEMA_INVALID"
    )
    assert "Additional properties are not allowed" in result["attempts"][0][
        "issues"
    ][0]["message"]


def test_stage1_unsupported_door_capability_precedes_missing_geometry(
    tmp_path: Path,
) -> None:
    result = generate_repair_intent(
        provider=Provider(_v05_unsupported_door_body()),
        request_id="profile-stage1-door-unsupported",
        repair_request="add a REVOLVING door to WALL-GUID",
        registry=create_default_registry(),
        output_dir=tmp_path,
        max_attempts=1,
        intent_schema_version="text2ifc/ifc-repair-intent/0.5",
    )

    assert result["valid"] is True
    assert result["classification"] == "unsupported"
    assert result["reason_code"] == "DOOR_OPERATION_TYPE_UNSUPPORTED"
    assert result["unsupported_operations"] == [
        {
            "operation_id": "door-fill-1",
            "reason_code": "DOOR_OPERATION_TYPE_UNSUPPORTED",
        }
    ]


def test_stage1_profile_mismatch_stops_without_a_second_stage(
    tmp_path: Path,
) -> None:
    body = _v05_body()
    body["operations"][0]["routing_intent"]["operation_profile"] = (
        "occurrence.set-properties"
    )
    provider = Provider(body)
    result = generate_repair_intent(
        provider=provider,
        request_id="profile-mismatch",
        repair_request="add a 900 by 1200 window to North wall",
        registry=create_default_registry(),
        output_dir=tmp_path,
        max_attempts=1,
        intent_schema_version="text2ifc/ifc-repair-intent/0.5",
    )
    assert result["valid"] is False
    assert len(provider.calls) == 1
    assert result["attempts"][0]["issues"][0]["code"] == (
        "OPERATION_PROFILE_MISMATCH"
    )


def test_stage2_receives_only_used_full_profile_and_records_hashes(
    tmp_path: Path,
) -> None:
    model = "sha256:" + "a" * 64
    request_hash = "sha256:" + "b" * 64
    target = "0AAAAAAAAAAAAAAAAAAAAA"
    pointer = "resolved:/operations/window-1/context/candidate_targets/0"
    operation = {
        "operation_id": "window-1",
        "operation_type": "add_window_with_opening_to_wall",
        "target_global_id": target,
        "scope_ids": [target],
        "evidence_pointers": [pointer],
        "parameters": {
            "position": {
                "reference": "wall_local_start",
                "center_offset_mm": 1000,
            },
            "opening": {
                "width_mm": 900,
                "height_mm": 1200,
                "sill_height_mm": 900,
            },
            "window": {"fit_opening": True},
        },
        "authorized_semantics": [],
        "context": {
            "model_fingerprint": model,
            "candidate_targets": [
                {"ifc_global_id": target, "ifc_class": "IfcWall"}
            ],
        },
    }
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-window-1",
        "base_model_fingerprint": model,
        "source_request_hash": request_hash,
        "scope": {"target_ids": [target], "forbidden_ids": []},
        "evidence_refs": [pointer],
        "preconditions": ["target_exists"],
        "postconditions": ["window_fills_opening"],
        "operations": [
            {
                "operation_id": "window-1",
                "operation_type": "add_window_with_opening_to_wall",
                "target": {"wall_global_id": target},
                "parameters": operation["parameters"],
                "evidence_refs": [pointer],
            }
        ],
    }
    provider = Provider(changeset)
    result = generate_bound_changeset(
        provider=provider,
        case_id="selected-stage2",
        repair_request="add a window",
        source_request_hash=request_hash,
        resolved_operations=(operation,),
        model_fingerprint=model,
        registry=create_default_registry(),
        output_dir=tmp_path,
        max_attempts=1,
    )
    assert result["valid"] is True
    selection = json.loads(
        (tmp_path / "prompt-profile-selection.json").read_text(encoding="utf-8")
    )
    assert selection["profile_ids"] == ["window.add-with-opening"]
    assert selection["few_shot_ids"] == []
    assert selection["profile_hashes"][0].startswith("sha256:")
    prompt = provider.calls[0]["prompt"]
    assert '"profile_id": "window.add-with-opening"' in prompt
    assert "door.add.complete" not in prompt
