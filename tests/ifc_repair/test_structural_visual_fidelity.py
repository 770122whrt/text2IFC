from __future__ import annotations

import uuid
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid
import pytest
from ifcopenshell.api.material.add_material import add_material

from text2ifc_ifc_repair.geometry import measure_straight_rectangular_member
from text2ifc_ifc_repair.operations.hosted_opening import body_context
from text2ifc_ifc_repair.operations.structural_member import (
    bind_structural_type,
    create_straight_rectangular_member,
)
from text2ifc_presentation import (
    AppearanceSpec,
    assign_material_appearance,
    item_appearance_signatures,
)


ROOT = Path(__file__).resolve().parents[2]
D7N = ROOT / "dataset" / "external" / "bimnet" / "d7n.ifc"


def _global_id(label: str) -> str:
    return ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL, label).hex)


def _model_fixture():
    model = ifcopenshell.open(str(D7N))
    storey = next(
        item for item in model.by_type("IfcBuildingStorey") if item.Name == "Level 1"
    )
    return model, model.by_type("IfcOwnerHistory")[0], storey, body_context(model)


def _generated_type_factory(**kwargs):
    raise AssertionError(f"exact existing Type must not generate a new Type: {kwargs}")


@pytest.mark.parametrize(
    ("occurrence_class", "type_class", "section", "expected_section"),
    (
        (
            "IfcBeam",
            "IfcBeamType",
            {"shape": "rectangle", "width_mm": 500.0, "height_mm": 800.0},
            {"shape": "rectangle", "width_mm": 500.0, "height_mm": 800.0},
        ),
        (
            "IfcColumn",
            "IfcColumnType",
            {
                "shape": "rectangle",
                "width_mm": 400.0,
                "depth_mm": 600.0,
                "orientation": {"x": 1.0, "y": 0.0},
            },
            {"shape": "rectangle", "width_mm": 400.0, "depth_mm": 600.0},
        ),
    ),
)
def test_exact_structural_type_preserves_type_material_appearance_without_geometry_change(
    occurrence_class: str,
    type_class: str,
    section: dict,
    expected_section: dict,
) -> None:
    model, owner_history, storey, representation_context = _model_fixture()
    type_object = model.create_entity(
        type_class,
        GlobalId=_global_id(f"{type_class}-styled"),
        OwnerHistory=owner_history,
        Name=f"Styled {type_class}",
        PredefinedType="NOTDEFINED",
    )
    material = add_material(model, name="Authoritative structural material")
    model.create_entity(
        "IfcRelAssociatesMaterial",
        GlobalId=_global_id(f"{type_class}-material"),
        OwnerHistory=owner_history,
        RelatedObjects=[type_object],
        RelatingMaterial=material,
    )
    assign_material_appearance(
        model,
        material=material,
        context=representation_context,
        spec=AppearanceSpec(
            name="authoritative-blue",
            red=0.18,
            green=0.34,
            blue=0.62,
            transparency=0.0,
        ),
    )
    axis_end = (
        (6000.0, 0.0, 3000.0)
        if occurrence_class == "IfcBeam"
        else (0.0, 0.0, 3200.0)
    )
    axis_start = (
        (0.0, 0.0, 3000.0)
        if occurrence_class == "IfcBeam"
        else (0.0, 0.0, 0.0)
    )
    created = create_straight_rectangular_member(
        model=model,
        occurrence_class=occurrence_class,
        occurrence_global_id=_global_id(f"{occurrence_class}-styled-occurrence"),
        operation_id=f"styled-{occurrence_class.lower()}",
        axis_start_mm=axis_start,
        axis_end_mm=axis_end,
        section=section,
        storey=storey,
        owner_history=owner_history,
        representation_context=representation_context,
    )
    occurrence = created["occurrence"]
    before_measurement = measure_straight_rectangular_member(
        occurrence, relative_to=storey
    )
    assert item_appearance_signatures(created["representation"].Items[0]) == ()

    binding = bind_structural_type(
        model=model,
        occurrence=occurrence,
        assignment={
            "value": str(type_object.GlobalId),
            "value_type": type_class,
            "source_kind": "surviving_type",
        },
        owner_history=owner_history,
        operation_id=f"styled-{occurrence_class.lower()}",
        expected_ifc_class=type_class,
        generated_type_factory=_generated_type_factory,
        factory_context={"section": section},
    )

    assert binding["type"] == type_object
    assert binding["appearance"]["applied"] is True
    assert item_appearance_signatures(created["representation"].Items[0]) == (
        {
            "style_name": "authoritative-blue",
            "red": 0.18,
            "green": 0.34,
            "blue": 0.62,
            "transparency": 0.0,
        },
    )
    after_measurement = measure_straight_rectangular_member(
        occurrence, relative_to=storey
    )
    assert after_measurement["axis_start_mm"] == pytest.approx(
        before_measurement["axis_start_mm"]
    )
    assert after_measurement["axis_end_mm"] == pytest.approx(
        before_measurement["axis_end_mm"]
    )
    assert after_measurement["section"] == expected_section


def test_exact_structural_type_falls_back_to_unambiguous_same_type_occurrence_material_style() -> None:
    model, owner_history, storey, representation_context = _model_fixture()
    type_object = model.create_entity(
        "IfcBeamType",
        GlobalId=_global_id("IfcBeamType-reference-styled"),
        OwnerHistory=owner_history,
        Name="Reference-styled Beam Type",
        PredefinedType="NOTDEFINED",
    )
    reference = create_straight_rectangular_member(
        model=model,
        occurrence_class="IfcBeam",
        occurrence_global_id=_global_id("reference-styled-beam"),
        operation_id="reference-styled-beam",
        axis_start_mm=(0.0, 0.0, 3000.0),
        axis_end_mm=(4000.0, 0.0, 3000.0),
        section={"shape": "rectangle", "width_mm": 500.0, "height_mm": 800.0},
        storey=storey,
        owner_history=owner_history,
        representation_context=representation_context,
    )["occurrence"]
    model.create_entity(
        "IfcRelDefinesByType",
        GlobalId=_global_id("reference-styled-type-relation"),
        OwnerHistory=owner_history,
        RelatedObjects=[reference],
        RelatingType=type_object,
    )
    material = add_material(model, name="Reference occurrence material")
    model.create_entity(
        "IfcRelAssociatesMaterial",
        GlobalId=_global_id("reference-styled-material-relation"),
        OwnerHistory=owner_history,
        RelatedObjects=[reference],
        RelatingMaterial=material,
    )
    assign_material_appearance(
        model,
        material=material,
        context=representation_context,
        spec=AppearanceSpec(
            name="reference-cyan",
            red=0.0,
            green=0.384314,
            blue=0.52549,
        ),
    )

    created = create_straight_rectangular_member(
        model=model,
        occurrence_class="IfcBeam",
        occurrence_global_id=_global_id("new-reference-styled-beam"),
        operation_id="new-reference-styled-beam",
        axis_start_mm=(0.0, 1000.0, 3000.0),
        axis_end_mm=(6000.0, 1000.0, 3000.0),
        section={"shape": "rectangle", "width_mm": 500.0, "height_mm": 800.0},
        storey=storey,
        owner_history=owner_history,
        representation_context=representation_context,
    )

    binding = bind_structural_type(
        model=model,
        occurrence=created["occurrence"],
        assignment={
            "value": str(type_object.GlobalId),
            "value_type": "IfcBeamType",
            "source_kind": "surviving_type",
        },
        owner_history=owner_history,
        operation_id="new-reference-styled-beam",
        expected_ifc_class="IfcBeamType",
        generated_type_factory=_generated_type_factory,
        factory_context={
            "section": {
                "shape": "rectangle",
                "width_mm": 500.0,
                "height_mm": 800.0,
            }
        },
    )

    assert binding["appearance"]["source"] == "same_type_reference_occurrence"
    assert item_appearance_signatures(created["representation"].Items[0]) == (
        {
            "style_name": "reference-cyan",
            "red": 0.0,
            "green": 0.384314,
            "blue": 0.52549,
            "transparency": 0.0,
        },
    )
