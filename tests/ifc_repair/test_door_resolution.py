from __future__ import annotations

from dataclasses import replace

import pytest

from text2ifc_ifc_repair.door_resolution import canonicalize_door_intent
from text2ifc_ifc_repair.index_models import ElementRecord, TypeRecord


def _wall() -> ElementRecord:
    return ElementRecord(
        record_id="ifc:wall",
        ifc_global_id="0WALLAAAAAAAAAAAAAAAAA",
        identity_reliable=True,
        ifc_class="IfcWall",
        name="South wall",
        long_name=None,
        tag="W-01",
        object_type=None,
        type_name="Basic Wall",
        type_global_id=None,
        storey_name="Level 1",
        storey_global_id="0STOREYAAAAAAAAAAAAAAA",
        geometry_capability="straight_wall",
        geometry_summary={"dimensions_mm": {"length": 6000.0}},
        facets={"editable_target": True},
    )


def _opening(*, filled: bool = False) -> ElementRecord:
    return ElementRecord(
        record_id="ifc:opening",
        ifc_global_id="0OPENINGAAAAAAAAAAAAAA",
        identity_reliable=True,
        ifc_class="IfcOpeningElement",
        name="Door opening 01",
        long_name=None,
        tag=None,
        object_type=None,
        type_name=None,
        type_global_id=None,
        storey_name="Level 1",
        storey_global_id="0STOREYAAAAAAAAAAAAAAA",
        geometry_capability="measured_hosted_opening",
        geometry_summary={
            "dimensions_mm": {
                "width": 900.0,
                "height": 2100.0,
                "depth": 200.0,
            },
            "wall_local_position_mm": {
                "reference": "wall_local_start",
                "center_offset_mm": 2200.0,
                "sill_height_mm": 0.0,
            },
        },
        facets={
            "editable_target": True,
            "host_wall_global_ids": ["0WALLAAAAAAAAAAAAAAAAA"],
            "filling_global_ids": ["0DOORAAAAAAAAAAAAAAAAA"] if filled else [],
            "fill_state": "filled" if filled else "empty",
        },
    )


def _style(operation_type: str, *, name: str = "Style label") -> TypeRecord:
    return TypeRecord(
        record_id="type:door",
        ifc_global_id="0STYLEAAAAAAAAAAAAAAAA",
        identity_reliable=True,
        ifc_class="IfcDoorStyle",
        name=name,
        applicable_occurrence=None,
        predefined_type=None,
        element_type=None,
        formal_attributes={
            "OperationType": operation_type,
            "ConstructionType": "NOTDEFINED",
            "ParameterTakesPrecedence": False,
            "Sizeable": False,
        },
    )


def _complete_parameters() -> dict:
    return {
        "position": {"reference": "wall_midpoint"},
        "opening": {
            "width_mm": 900.0,
            "height_mm": 2100.0,
            "sill_height_mm": 0.0,
            "dimension_meaning": "overall_opening",
        },
        "door": {
            "operation_type": "SINGLE_SWING_LEFT",
            "formal_enum_explicit": True,
        },
    }


def test_explicit_overall_dimensions_and_midpoint_canonicalize() -> None:
    decision = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=_complete_parameters(),
        target_record=_wall(),
    )
    assert decision.status == "resolved"
    assert decision.parameters["position"] == {
        "reference": "wall_local_start",
        "center_offset_mm": 3000.0,
    }
    assert decision.parameters["opening"]["width_mm"] == 900.0
    assert decision.parameters["opening"]["height_mm"] == 2100.0
    assert decision.parameters["derivation"]["digest"].startswith("sha256:")


@pytest.mark.parametrize("meaning", ["clear_passage", "door_leaf", "rough_opening"])
def test_non_overall_dimension_meanings_are_preserved_but_not_converted(
    meaning: str,
) -> None:
    parameters = _complete_parameters()
    parameters["opening"]["dimension_meaning"] = meaning
    decision = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=parameters,
        target_record=_wall(),
    )
    assert decision.status == "clarification_required"
    assert decision.reason_code == "DOOR_OVERALL_DIMENSIONS_REQUIRED"
    assert "/parameters/opening/width_mm" in decision.missing_slots


def test_generic_door_dimensions_and_ambiguous_wall_end_group_questions() -> None:
    parameters = _complete_parameters()
    parameters["opening"].pop("dimension_meaning")
    parameters["position"] = {
        "reference": "wall_end",
        "anchor": "start",
        "offset_mm": 1000.0,
    }
    decision = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=parameters,
        target_record=_wall(),
    )
    assert decision.status == "clarification_required"
    assert decision.reason_code == "DOOR_BLOCKING_FACTS_REQUIRED"
    assert set(decision.missing_slots) >= {
        "/parameters/opening/dimension_meaning",
        "/parameters/position/measure_to",
    }


def test_center_and_nearest_edge_wall_end_forms_have_explicit_formula() -> None:
    center_parameters = _complete_parameters()
    center_parameters["position"] = {
        "reference": "wall_end",
        "anchor": "start",
        "measure_to": "center",
        "offset_mm": 1000.0,
    }
    center = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=center_parameters,
        target_record=_wall(),
    )
    assert center.parameters["position"]["center_offset_mm"] == 1000.0
    assert center.parameters["derivation"]["position"]["formula"] == "offset_mm"

    edge_parameters = _complete_parameters()
    edge_parameters["position"] = {
        "reference": "wall_end",
        "anchor": "end",
        "measure_to": "nearest_edge",
        "offset_mm": 500.0,
    }
    edge = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=edge_parameters,
        target_record=_wall(),
    )
    assert edge.parameters["position"]["center_offset_mm"] == 5050.0
    assert "overall_width_mm / 2" in edge.parameters["derivation"]["position"][
        "formula"
    ]


def test_project_coordinates_are_rejected_and_grid_is_not_position() -> None:
    parameters = _complete_parameters()
    parameters["position"] = {
        "reference": "project_coordinates",
        "coordinates": [1, 2, 3],
    }
    decision = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=parameters,
        target_record=_wall(),
    )
    assert decision.status == "unsupported"
    assert decision.reason_code == "PROJECT_COORDINATES_UNSUPPORTED"


def test_viewpoint_reversal_changes_formal_left_right_result() -> None:
    positive = _complete_parameters()
    positive["door"] = {
        "hinge_side": "left",
        "viewpoint": {
            "observation_side": "wall_positive",
            "destination": "Room 101",
        },
    }
    negative = _complete_parameters()
    negative["door"] = {
        "hinge_side": "left",
        "viewpoint": {
            "observation_side": "wall_negative",
            "destination": "Room 101",
        },
    }
    first = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=positive,
        target_record=_wall(),
    )
    second = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=negative,
        target_record=_wall(),
    )
    assert first.parameters["door"]["operation_type"] == "SINGLE_SWING_LEFT"
    assert second.parameters["door"]["operation_type"] == "SINGLE_SWING_RIGHT"


def test_hinge_word_without_viewpoint_clarifies() -> None:
    parameters = _complete_parameters()
    parameters["door"] = {"hinge_side": "right"}
    decision = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=parameters,
        target_record=_wall(),
    )
    assert decision.status == "clarification_required"
    assert decision.reason_code == "DOOR_VIEWPOINT_REQUIRED"
    assert "/parameters/door/viewpoint" in decision.missing_slots


def test_exact_type_formal_operation_is_authority_and_name_is_not() -> None:
    parameters = _complete_parameters()
    parameters["door"] = {}
    decision = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=parameters,
        target_record=_wall(),
        type_record=_style(
            "SINGLE_SWING_RIGHT",
            name="Misleading SINGLE_SWING_LEFT name",
        ),
    )
    assert decision.status == "resolved"
    assert decision.parameters["door"]["operation_type"] == "SINGLE_SWING_RIGHT"
    assert decision.parameters["door"]["operation_derivation"][
        "formal_attribute"
    ] == "OperationType"


def test_type_operation_conflict_clarifies_preserve_or_cancel_reuse() -> None:
    parameters = _complete_parameters()
    parameters["door"]["operation_type"] = "SINGLE_SWING_LEFT"
    decision = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=parameters,
        target_record=_wall(),
        type_record=_style("SINGLE_SWING_RIGHT"),
    )
    assert decision.status == "clarification_required"
    assert decision.reason_code == "DOOR_TYPE_OPERATION_CONFLICT"
    assert "/prototype_intent" in decision.missing_slots


def test_notdefined_requires_explicit_acceptance_and_complex_generation_fails() -> None:
    parameters = _complete_parameters()
    parameters["door"] = {"operation_type": "NOTDEFINED"}
    clarification = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=parameters,
        target_record=_wall(),
    )
    assert clarification.reason_code == "DOOR_NOTDEFINED_CONFIRMATION_REQUIRED"
    parameters["door"]["notdefined_accepted"] = True
    accepted = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=parameters,
        target_record=_wall(),
    )
    assert accepted.status == "resolved"
    parameters["door"] = {"operation_type": "REVOLVING"}
    unsupported = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=parameters,
        target_record=_wall(),
    )
    assert unsupported.status == "unsupported"
    assert unsupported.reason_code == "DOOR_OPERATION_TYPE_UNSUPPORTED"


def test_fill_exact_empty_opening_derives_dimensions_and_position() -> None:
    decision = canonicalize_door_intent(
        operation_type="fill_existing_opening_with_door",
        parameters={
            "fit_existing_opening": True,
            "door": {
                "operation_type": "SINGLE_SWING_RIGHT",
                "formal_enum_explicit": True,
            },
        },
        target_record=_opening(),
    )
    assert decision.status == "resolved"
    assert decision.parameters["opening"]["width_mm"] == 900.0
    assert decision.parameters["opening"]["height_mm"] == 2100.0
    assert decision.parameters["position"]["center_offset_mm"] == 2200.0
    assert decision.parameters["opening"]["derivation"]["formula"] == (
        "fit_existing_opening"
    )


def test_filled_or_invalid_opening_stops_before_generation() -> None:
    filled = canonicalize_door_intent(
        operation_type="fill_existing_opening_with_door",
        parameters={"fit_existing_opening": True, "door": {}},
        target_record=_opening(filled=True),
    )
    assert filled.status == "unsupported"
    assert filled.reason_code == "OPENING_ALREADY_FILLED"

    invalid = canonicalize_door_intent(
        operation_type="fill_existing_opening_with_door",
        parameters={"fit_existing_opening": True, "door": {}},
        target_record=replace(
            _opening(),
            geometry_capability="opening_geometry_unmeasurable",
        ),
    )
    assert invalid.reason_code == "OPENING_TARGET_INVALID"


def test_optional_door_facts_are_not_invented_or_asked() -> None:
    decision = canonicalize_door_intent(
        operation_type="add_door_with_opening_to_wall",
        parameters=_complete_parameters(),
        target_record=_wall(),
    )
    serialized = str(decision.to_dict())
    for optional in ("material", "transom", "threshold", "hardware", "FireRating"):
        assert optional not in serialized
