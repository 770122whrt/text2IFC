from __future__ import annotations

import math
import uuid
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid
import pytest

from text2ifc_ifc_repair.geometry import measure_straight_rectangular_member
from text2ifc_ifc_repair.operations.hosted_opening import body_context
from text2ifc_ifc_repair.operations.structural_member import (
    create_straight_rectangular_member,
    resolve_structural_member_frame,
)


ROOT = Path(__file__).resolve().parents[2]
D7N = ROOT / "dataset" / "ifc" / "test" / "d7n.ifc"


def _model_context() -> tuple[object, object, object, object]:
    model = ifcopenshell.open(str(D7N))
    storey = next(
        item for item in model.by_type("IfcBuildingStorey") if item.Name == "Level 1"
    )
    return model, storey, model.by_type("IfcOwnerHistory")[0], body_context(model)


def _global_id(label: str) -> str:
    return ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL, label).hex)


def _create(
    *,
    occurrence_class: str,
    start: object,
    end: object,
    section: dict,
    label: str,
):
    model, storey, owner_history, context = _model_context()
    result = create_straight_rectangular_member(
        model=model,
        occurrence_class=occurrence_class,
        occurrence_global_id=_global_id(label),
        operation_id=label,
        axis_start_mm=start,
        axis_end_mm=end,
        section=section,
        storey=storey,
        owner_history=owner_history,
        representation_context=context,
    )
    return model, storey, owner_history, result


def test_pure_frames_preserve_frozen_axis_and_section_meanings() -> None:
    beam = resolve_structural_member_frame(
        occurrence_class="IfcBeam",
        axis_start_mm=(0.0, 0.0, 3000.0),
        axis_end_mm=(3000.0, 4000.0, 3000.0),
        section={"shape": "rectangle", "width_mm": 300, "height_mm": 500},
    )
    assert beam["axis_direction"] == pytest.approx((0.6, 0.8, 0.0))
    assert beam["profile_x_direction"] == pytest.approx((-0.8, 0.6, 0.0))
    assert beam["profile_y_direction"] == pytest.approx((0.0, 0.0, 1.0))
    assert beam["axis_extent_mm"] == 5000.0

    column = resolve_structural_member_frame(
        occurrence_class="IfcColumn",
        axis_start_mm=(1000.0, 2000.0, 0.0),
        axis_end_mm=(1000.0, 2000.0, 3200.0),
        section={
            "shape": "rectangle",
            "width_mm": 400,
            "depth_mm": 600,
            "orientation": {"x": 3, "y": 4},
        },
    )
    assert column["axis_direction"] == pytest.approx((0.0, 0.0, 1.0))
    assert column["profile_x_direction"] == pytest.approx((0.6, 0.8, 0.0))
    assert column["profile_y_direction"] == pytest.approx((-0.8, 0.6, 0.0))
    assert column["axis_extent_mm"] == 3200.0


def test_arbitrary_xy_beam_reopens_at_end_face_centers(tmp_path: Path) -> None:
    start = (1000.0, 2000.0, 3000.0)
    end = (4000.0, 6000.0, 3000.0)
    model, storey, owner_history, result = _create(
        occurrence_class="IfcBeam",
        start=start,
        end=end,
        section={"shape": "rectangle", "width_mm": 300, "height_mm": 500},
        label="phase12-beam-geometry",
    )

    beam = result["occurrence"]
    assert beam.is_a("IfcBeam")
    assert beam.OwnerHistory == owner_history
    assert beam.ObjectPlacement.PlacementRelTo == storey.ObjectPlacement
    assert beam.Representation.Representations == (result["representation"],)
    assert result["measurement"]["axis_start_mm"] == pytest.approx(start)
    assert result["measurement"]["axis_end_mm"] == pytest.approx(end)
    assert not model.by_type("IfcRelConnectsStructuralMember")

    output = tmp_path / "beam.ifc"
    model.write(str(output))
    reopened = ifcopenshell.open(str(output))
    measured = measure_straight_rectangular_member(
        reopened.by_guid(str(beam.GlobalId)), relative_to=reopened.by_guid(str(storey.GlobalId))
    )
    assert reopened.schema == "IFC2X3"
    assert measured["axis_start_mm"] == pytest.approx(start)
    assert measured["axis_end_mm"] == pytest.approx(end)
    assert measured["axis_extent_mm"] == pytest.approx(5000.0)
    assert measured["section"] == {
        "shape": "rectangle",
        "width_mm": 300.0,
        "height_mm": 500.0,
    }
    assert measured["orientation"] == pytest.approx((0.6, 0.8, 0.0))


def test_oriented_non_square_column_reopens_from_base_to_top(tmp_path: Path) -> None:
    base = (1000.0, 2000.0, 0.0)
    top = (1000.0, 2000.0, 3200.0)
    model, storey, _, result = _create(
        occurrence_class="IfcColumn",
        start=base,
        end=top,
        section={
            "shape": "rectangle",
            "width_mm": 400,
            "depth_mm": 600,
            "orientation": {"x": 3, "y": 4},
        },
        label="phase12-column-geometry",
    )
    column = result["occurrence"]
    assert column.ObjectPlacement.PlacementRelTo == storey.ObjectPlacement

    output = tmp_path / "column.ifc"
    model.write(str(output))
    reopened = ifcopenshell.open(str(output))
    measured = measure_straight_rectangular_member(
        reopened.by_guid(str(column.GlobalId)), relative_to=reopened.by_guid(str(storey.GlobalId))
    )
    assert measured["axis_start_mm"] == pytest.approx(base)
    assert measured["axis_end_mm"] == pytest.approx(top)
    assert measured["axis_extent_mm"] == pytest.approx(3200.0)
    assert measured["section"] == {
        "shape": "rectangle",
        "width_mm": 400.0,
        "depth_mm": 600.0,
    }
    assert measured["orientation"] == pytest.approx((0.6, 0.8, 0.0))


def test_square_column_serialization_does_not_claim_an_orientation() -> None:
    _, _, _, result = _create(
        occurrence_class="IfcColumn",
        start=(0.0, 0.0, 0.0),
        end=(0.0, 0.0, 3000.0),
        section={"shape": "rectangle", "width_mm": 500, "depth_mm": 500},
        label="phase12-square-column-geometry",
    )
    placement = result["occurrence"].ObjectPlacement.RelativePlacement
    assert placement.RefDirection is None
    assert result["measurement"]["orientation"] is None


@pytest.mark.parametrize(
    ("occurrence_class", "start", "end", "section", "code"),
    (
        (
            "IfcBeam",
            (0, 0, 0),
            (3000, 0, 50),
            {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
            "STRUCTURAL_BEAM_NOT_HORIZONTAL",
        ),
        (
            "IfcColumn",
            (0, 0, 0),
            (50, 0, 3000),
            {"shape": "rectangle", "width_mm": 400, "depth_mm": 400},
            "STRUCTURAL_COLUMN_NOT_VERTICAL",
        ),
        (
            "IfcBeam",
            (0, 0, 0),
            (0, 0, 0),
            {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
            "STRUCTURAL_AXIS_ZERO_LENGTH",
        ),
        (
            "IfcBeam",
            (0, 0, 0),
            (3000, 0, 0),
            {"shape": "round", "diameter_mm": 300},
            "STRUCTURAL_SECTION_UNSUPPORTED",
        ),
        (
            "IfcBeam",
            (0, 0, 0),
            (3000, 0, 0),
            {
                "shape": "rectangle",
                "width_mm": 300,
                "height_mm": 500,
                "rotation_degrees": 10,
            },
            "STRUCTURAL_SECTION_ROTATION_UNSUPPORTED",
        ),
        (
            "IfcBeam",
            (0, 0, 0),
            (3000, 0, 0),
            {
                "shape": "rectangle",
                "width_mm": 300,
                "height_mm": 500,
                "length_mm": 3000,
            },
            "STRUCTURAL_SCALAR_EXTENT_UNSUPPORTED",
        ),
        (
            "IfcColumn",
            (0, 0, 0),
            (0, 0, 3000),
            {"shape": "rectangle", "width_mm": 400, "depth_mm": 600},
            "STRUCTURAL_COLUMN_ORIENTATION_REQUIRED",
        ),
        (
            "IfcBeam",
            {"grid": "A/1"},
            (3000, 0, 0),
            {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
            "STRUCTURAL_AXIS_INVALID",
        ),
        (
            "IfcBeam",
            (0, 0, 0),
            (math.nan, 0, 0),
            {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
            "STRUCTURAL_AXIS_INVALID",
        ),
        (
            "IfcMember",
            (0, 0, 0),
            (3000, 0, 0),
            {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
            "STRUCTURAL_OCCURRENCE_CLASS_UNSUPPORTED",
        ),
    ),
)
def test_unsupported_boundary_fails_before_any_ifc_root_is_created(
    occurrence_class: str,
    start: object,
    end: object,
    section: dict,
    code: str,
) -> None:
    model, storey, owner_history, context = _model_context()
    roots_before = len(model.by_type("IfcRoot"))

    with pytest.raises(ValueError, match=f"^{code}$"):
        create_straight_rectangular_member(
            model=model,
            occurrence_class=occurrence_class,
            occurrence_global_id=_global_id(f"rejected-{code}"),
            operation_id=f"rejected-{code}",
            axis_start_mm=start,
            axis_end_mm=end,
            section=section,
            storey=storey,
            owner_history=owner_history,
            representation_context=context,
        )

    assert len(model.by_type("IfcRoot")) == roots_before
