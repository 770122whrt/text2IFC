from __future__ import annotations

from text2ifc_ifc_repair.operations.hosted_opening import (
    HostedOpeningFootprint,
    deterministic_global_id,
    footprint_from_operation,
    footprints_overlap,
    hosted_opening_conflict_checker,
)


def _operation(operation_id: str, center: float, sill: float = 0.0) -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "fixture_hosted_opening",
        "target": {"wall_global_id": "0WALLAAAAAAAAAAAAAAAAA"},
        "parameters": {
            "position": {
                "reference": "wall_local_start",
                "center_offset_mm": center,
            },
            "opening": {
                "width_mm": 900.0,
                "height_mm": 1200.0,
                "sill_height_mm": sill,
            },
        },
    }


def test_footprint_is_family_neutral_and_deterministic() -> None:
    operation = _operation("first", 1000.0)
    footprint = footprint_from_operation(operation)
    assert footprint == HostedOpeningFootprint(
        host_wall_global_id="0WALLAAAAAAAAAAAAAAAAA",
        center_offset_mm=1000.0,
        width_mm=900.0,
        sill_height_mm=0.0,
        height_mm=1200.0,
    )
    assert footprint.horizontal_interval_mm == (550.0, 1450.0)
    assert footprint.vertical_interval_mm == (0.0, 1200.0)
    assert deterministic_global_id(operation, "opening") == (
        deterministic_global_id(operation, "opening")
    )


def test_true_2d_overlap_rejects_but_one_axis_overlap_is_allowed() -> None:
    first = footprint_from_operation(_operation("first", 1000.0))
    horizontal_only = footprint_from_operation(
        _operation("vertical-separated", 1100.0, sill=1300.0)
    )
    vertical_only = footprint_from_operation(
        _operation("horizontal-separated", 2000.0)
    )
    true_overlap = footprint_from_operation(_operation("overlap", 1200.0))
    assert footprints_overlap(first, horizontal_only) is False
    assert footprints_overlap(first, vertical_only) is False
    assert footprints_overlap(first, true_overlap) is True


def test_cross_family_checker_uses_shared_hosted_opening_domain() -> None:
    previous = _operation("window", 1000.0)
    previous["operation_type"] = "add_window_with_opening_to_wall"
    current = _operation("door", 1200.0)
    current["operation_type"] = "add_door_with_opening_to_wall"
    issues = hosted_opening_conflict_checker(previous, current)
    assert issues[0]["code"] == "BATCH_OPENING_OVERLAP"
    assert "window" in issues[0]["message"]
