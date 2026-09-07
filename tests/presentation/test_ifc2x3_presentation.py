from __future__ import annotations

from pathlib import Path

import ifcopenshell
import ifcopenshell.guid
from ifcopenshell.api.context.add_context import add_context
from ifcopenshell.api.material.add_material import add_material
from ifcopenshell.api.project.create_file import create_file

from text2ifc_presentation import (
    AppearanceSpec,
    appearance_fingerprint,
    apply_repair_appearance_on_occurrence,
    assign_item_appearance,
    assign_material_appearance,
    item_appearance_signatures,
    material_appearance_signatures,
    type_surface_styles,
)


def _body_context(model):
    if not model.by_type("IfcProject"):
        model.create_entity(
            "IfcProject",
            GlobalId=ifcopenshell.guid.new(),
            Name="Presentation Test Project",
        )
    model_context = add_context(model, context_type="Model")
    return add_context(
        model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=model_context,
    )


def test_material_surface_style_survives_ifc2x3_reopen(tmp_path: Path) -> None:
    model = create_file(version="IFC2X3")
    body = _body_context(model)
    material = add_material(model, name="Warm concrete")
    spec = AppearanceSpec(
        name="warm-concrete",
        red=0.72,
        green=0.63,
        blue=0.54,
        transparency=0.0,
    )

    assign_material_appearance(model, material=material, context=body, spec=spec)

    before = material_appearance_signatures(material)
    assert before == (
        {
            "style_name": "warm-concrete",
            "red": 0.72,
            "green": 0.63,
            "blue": 0.54,
            "transparency": 0.0,
        },
    )
    before_fingerprint = appearance_fingerprint(material)

    output = tmp_path / "material-style.ifc"
    model.write(str(output))
    reopened = ifcopenshell.open(str(output))
    reopened_material = next(
        item for item in reopened.by_type("IfcMaterial") if item.Name == "Warm concrete"
    )

    assert material_appearance_signatures(reopened_material) == before
    assert appearance_fingerprint(reopened_material) == before_fingerprint


def test_type_representation_item_style_precedes_type_material_style() -> None:
    model = create_file(version="IFC2X3")
    body = _body_context(model)
    material = add_material(model, name="Blue structural material")
    assign_material_appearance(
        model,
        material=material,
        context=body,
        spec=AppearanceSpec(
            name="material-blue",
            red=0.18,
            green=0.34,
            blue=0.62,
        ),
    )
    block = model.create_entity(
        "IfcBlock",
        Position=model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity(
                "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
            ),
        ),
        XLength=1.0,
        YLength=1.0,
        ZLength=1.0,
    )
    assign_item_appearance(
        model,
        item=block,
        spec=AppearanceSpec(
            name="representation-red",
            red=0.75,
            green=0.20,
            blue=0.18,
        ),
    )
    representation = model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=body,
        RepresentationIdentifier="Body",
        RepresentationType="CSG",
        Items=[block],
    )
    representation_map = model.create_entity(
        "IfcRepresentationMap",
        MappingOrigin=model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity(
                "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
            ),
        ),
        MappedRepresentation=representation,
    )
    type_object = model.create_entity(
        "IfcBeamType",
        GlobalId=ifcopenshell.guid.new(),
        Name="Styled Beam Type",
        PredefinedType="NOTDEFINED",
        RepresentationMaps=[representation_map],
    )
    model.create_entity(
        "IfcRelAssociatesMaterial",
        GlobalId=ifcopenshell.guid.new(),
        RelatedObjects=[type_object],
        RelatingMaterial=material,
    )

    styles = type_surface_styles(type_object)

    assert len(styles) == 1
    assert item_appearance_signatures(block) == (
        {
            "style_name": "representation-red",
            "red": 0.75,
            "green": 0.20,
            "blue": 0.18,
            "transparency": 0.0,
        },
    )
    assert styles[0].Name == "representation-red"


def _beam_occurrence(model, body, *, name: str):
    block = model.create_entity(
        "IfcBlock",
        Position=model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity(
                "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
            ),
        ),
        XLength=1.0,
        YLength=1.0,
        ZLength=1.0,
    )
    representation = model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=body,
        RepresentationIdentifier="Body",
        RepresentationType="CSG",
        Items=[block],
    )
    product_shape = model.create_entity(
        "IfcProductDefinitionShape",
        Representations=[representation],
    )
    beam = model.create_entity(
        "IfcBeam",
        GlobalId=ifcopenshell.guid.new(),
        Name=name,
        Representation=product_shape,
    )
    return beam, block


def test_repair_explicit_user_appearance_precedes_reference_material_style() -> None:
    model = create_file(version="IFC2X3")
    body = _body_context(model)
    type_object = model.create_entity(
        "IfcBeamType",
        GlobalId=ifcopenshell.guid.new(),
        Name="Unstyled Beam Type",
        PredefinedType="NOTDEFINED",
    )
    reference, _ = _beam_occurrence(model, body, name="Reference Beam")
    restored, restored_block = _beam_occurrence(model, body, name="Restored Beam")
    model.create_entity(
        "IfcRelDefinesByType",
        GlobalId=ifcopenshell.guid.new(),
        RelatedObjects=[reference, restored],
        RelatingType=type_object,
    )
    material = add_material(model, name="Reference concrete")
    assign_material_appearance(
        model,
        material=material,
        context=body,
        spec=AppearanceSpec(
            name="reference-beige",
            red=0.75,
            green=0.70,
            blue=0.68,
        ),
    )
    model.create_entity(
        "IfcRelAssociatesMaterial",
        GlobalId=ifcopenshell.guid.new(),
        RelatedObjects=[reference],
        RelatingMaterial=material,
    )

    result = apply_repair_appearance_on_occurrence(
        model,
        type_object=type_object,
        occurrence=restored,
        explicit_appearance={
            "intent_kind": "surface_color_rgb",
            "red": 0.92,
            "green": 0.12,
            "blue": 0.18,
        },
    )

    assert result["source"] == "explicit_user"
    assert item_appearance_signatures(restored_block) == (
        {
            "style_name": "repair-user-rgb-0.920000-0.120000-0.180000",
            "red": 0.92,
            "green": 0.12,
            "blue": 0.18,
            "transparency": 0.0,
        },
    )
    assert material_appearance_signatures(material)[0]["style_name"] == "reference-beige"


def test_repair_type_owned_material_appearance_precedes_explicit_user_appearance() -> None:
    model = create_file(version="IFC2X3")
    body = _body_context(model)
    type_object = model.create_entity(
        "IfcBeamType",
        GlobalId=ifcopenshell.guid.new(),
        Name="Styled Beam Type",
        PredefinedType="NOTDEFINED",
    )
    material = add_material(model, name="Type-owned material")
    assign_material_appearance(
        model,
        material=material,
        context=body,
        spec=AppearanceSpec(
            name="type-blue",
            red=0.18,
            green=0.34,
            blue=0.62,
        ),
    )
    model.create_entity(
        "IfcRelAssociatesMaterial",
        GlobalId=ifcopenshell.guid.new(),
        RelatedObjects=[type_object],
        RelatingMaterial=material,
    )
    restored, restored_block = _beam_occurrence(model, body, name="Restored Beam")
    model.create_entity(
        "IfcRelDefinesByType",
        GlobalId=ifcopenshell.guid.new(),
        RelatedObjects=[restored],
        RelatingType=type_object,
    )

    result = apply_repair_appearance_on_occurrence(
        model,
        type_object=type_object,
        occurrence=restored,
        explicit_appearance={
            "intent_kind": "surface_color_rgb",
            "red": 0.92,
            "green": 0.12,
            "blue": 0.18,
        },
    )

    assert result["source"] == "type"
    assert item_appearance_signatures(restored_block) == (
        {
            "style_name": "type-blue",
            "red": 0.18,
            "green": 0.34,
            "blue": 0.62,
            "transparency": 0.0,
        },
    )

import pytest


@pytest.mark.parametrize("explicit", [None, {"intent_kind": "surface_color_rgb", "red": 1.0, "green": 0.0, "blue": 0.0}])
def test_exact_mapped_type_preserves_multiple_item_styles(tmp_path, explicit):
    from ifcopenshell.api.geometry.map_representation import map_representation
    from text2ifc_presentation import apply_repair_appearance_on_occurrence
    model = create_file(version="IFC2X3")
    body = _body_context(model)
    items = []
    for index, color in enumerate([(0.2, 0.3, 0.4), (0.8, 0.7, 0.6)]):
        occurrence, _ = _beam_occurrence(model, body, name=str(index))
        item = occurrence.Representation.Representations[0].Items[0]
        assign_item_appearance(model, item=item, spec=AppearanceSpec(name=str(index), red=color[0], green=color[1], blue=color[2]))
        items.append(item)
    representation = model.create_entity("IfcShapeRepresentation", ContextOfItems=body, RepresentationIdentifier="Body", RepresentationType="CSG", Items=items)
    mapped = map_representation(model, representation=representation)
    mapping = mapped.Items[0].MappingSource
    type_object = model.create_entity("IfcBeamType", GlobalId=ifcopenshell.guid.new(), PredefinedType="NOTDEFINED", RepresentationMaps=[mapping])
    occurrence = model.create_entity("IfcBeam", GlobalId=ifcopenshell.guid.new(), Representation=model.create_entity("IfcProductDefinitionShape", Representations=[mapped]))
    before = model.to_string()
    result = apply_repair_appearance_on_occurrence(model, type_object=type_object, occurrence=occurrence, explicit_appearance=explicit)
    assert result["source"] == "type_representation"
    assert result["preserved"] is True
    assert model.to_string() == before
    output = tmp_path / "multistyle.ifc"
    model.write(str(output))
    reopened = ifcopenshell.open(str(output))
    assert len(type_surface_styles(reopened.by_guid(type_object.GlobalId))) == 2


def test_unmapped_multistyle_type_remains_ambiguous():
    from text2ifc_presentation import apply_repair_appearance_on_occurrence
    model = create_file(version="IFC2X3")
    body = _body_context(model)
    items = []
    for index in range(2):
        source, _ = _beam_occurrence(model, body, name=str(index))
        item = source.Representation.Representations[0].Items[0]
        assign_item_appearance(model, item=item, spec=AppearanceSpec(name=str(index), red=float(index), green=0.0, blue=0.0))
        items.append(item)
    representation = model.create_entity("IfcShapeRepresentation", ContextOfItems=body, RepresentationIdentifier="Body", RepresentationType="CSG", Items=items)
    origin = model.create_entity("IfcAxis2Placement3D", Location=model.create_entity("IfcCartesianPoint", Coordinates=(0.0,0.0,0.0)))
    mapping = model.create_entity("IfcRepresentationMap", MappingOrigin=origin, MappedRepresentation=representation)
    type_object = model.create_entity("IfcBeamType", GlobalId=ifcopenshell.guid.new(), PredefinedType="NOTDEFINED", RepresentationMaps=[mapping])
    target, _ = _beam_occurrence(model, body, name="unmapped")
    with pytest.raises(ValueError, match="APPEARANCE_TYPE_STYLE_AMBIGUOUS"):
        apply_repair_appearance_on_occurrence(model, type_object=type_object, occurrence=target)
