from dataclasses import dataclass
from typing import Any, Mapping

from ifcopenshell.api.aggregate.assign_object import assign_object
from ifcopenshell.api.context.add_context import add_context
from ifcopenshell.api.owner.add_application import add_application
from ifcopenshell.api.owner.add_organisation import add_organisation
from ifcopenshell.api.owner.add_person import add_person
from ifcopenshell.api.owner.add_person_and_organisation import (
    add_person_and_organisation,
)
from ifcopenshell.api.material.add_layer import add_layer
from ifcopenshell.api.material.add_material import add_material
from ifcopenshell.api.material.add_material_set import add_material_set
from ifcopenshell.api.material.assign_material import assign_material
from ifcopenshell.api.project.create_file import create_file
from ifcopenshell.api.root.create_entity import create_entity
from ifcopenshell.api.spatial.assign_container import assign_container
from ifcopenshell.api.unit.assign_unit import assign_unit

from .geometry import (
    add_element_geometry,
    add_v2_geometry,
    assign_v2_placement,
    element_x_extent_m,
)
from .identity import assign_identity
from .properties import apply_selected_properties, apply_v2_properties
from .relationships import add_v2_relationships


ELEMENT_CLASS_BY_KIND = {
    "wall": "IfcWall",
    "column": "IfcColumn",
    "beam": "IfcBeam",
    "slab": "IfcSlab",
    "door": "IfcDoor",
    "window": "IfcWindow",
    "stair": "IfcStair",
    "stair_flight": "IfcStairFlight",
    "roof": "IfcRoof",
}


@dataclass(frozen=True)
class BootstrapResult:
    ifc_file: Any
    body_context: Any


def _create_owner_metadata(ifc_file: Any) -> None:
    person = add_person(
        ifc_file,
        identification="TEXT2IFC",
        family_name="Compiler",
        given_name="text2IFC",
    )
    organisation = add_organisation(
        ifc_file,
        identification="TEXT2IFC",
        name="text2IFC",
    )
    add_person_and_organisation(
        ifc_file, person=person, organisation=organisation
    )
    add_application(
        ifc_file,
        application_developer=organisation,
        version="0.1.0",
        application_full_name="text2IFC",
        application_identifier="text2ifc",
    )


def _create_rooted(
    ifc_file: Any,
    data: Mapping[str, Any],
    *,
    ifc_class: str,
    object_kind: str,
    contract_version: str,
) -> Any:
    entity = create_entity(
        ifc_file, ifc_class=ifc_class, name=data["name"]
    )
    assign_identity(
        ifc_file,
        entity,
        contract_version=contract_version,
        object_kind=object_kind,
        bim_json_id=data["id"],
    )
    return entity


def build_ifc(document: Mapping[str, Any]) -> BootstrapResult:
    ifc_file = create_file(version="IFC2X3")
    _create_owner_metadata(ifc_file)
    contract_version = document["contract_version"]

    project = _create_rooted(
        ifc_file,
        document["project"],
        ifc_class="IfcProject",
        object_kind="project",
        contract_version=contract_version,
    )
    millimetre = ifc_file.createIfcSIUnit(
        None, "LENGTHUNIT", "MILLI", "METRE"
    )
    assign_unit(ifc_file, units=[millimetre])
    model_context = add_context(ifc_file, context_type="Model")
    body_context = add_context(
        ifc_file,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=model_context,
    )

    site = _create_rooted(
        ifc_file,
        document["site"],
        ifc_class="IfcSite",
        object_kind="site",
        contract_version=contract_version,
    )
    building = _create_rooted(
        ifc_file,
        document["building"],
        ifc_class="IfcBuilding",
        object_kind="building",
        contract_version=contract_version,
    )
    assign_object(ifc_file, products=[site], relating_object=project)
    assign_object(ifc_file, products=[building], relating_object=site)

    storeys: list[Any] = []
    storey_by_id: dict[str, Any] = {}
    for storey_data in document["storeys"]:
        storey = _create_rooted(
            ifc_file,
            storey_data,
            ifc_class="IfcBuildingStorey",
            object_kind="storey",
            contract_version=contract_version,
        )
        storey.Elevation = storey_data["elevation"]
        storeys.append(storey)
        storey_by_id[storey_data["id"]] = storey
    assign_object(
        ifc_file, products=storeys, relating_object=building
    )

    x_offset_m = 0.0
    for element_data in document["elements"]:
        kind = element_data["kind"]
        element = _create_rooted(
            ifc_file,
            element_data,
            ifc_class=ELEMENT_CLASS_BY_KIND[kind],
            object_kind=f"element:{kind}",
            contract_version=contract_version,
        )
        if kind == "stair":
            element.ShapeType = "NOTDEFINED"
        elif kind == "roof":
            element.ShapeType = "NOTDEFINED"
        assign_container(
            ifc_file,
            products=[element],
            relating_structure=storey_by_id[element_data["storey_id"]],
        )
        add_element_geometry(
            ifc_file,
            element,
            element_data,
            body_context,
            x_offset_m,
        )
        apply_selected_properties(ifc_file, element, element_data)
        x_offset_m += element_x_extent_m(element_data) + 1.0

    return BootstrapResult(
        ifc_file=ifc_file, body_context=body_context
    )


def _apply_v2_attributes(entity: Any, attributes: Mapping[str, Any]) -> None:
    for name, value in attributes.items():
        if name in {"ObjectPlacement", "Representation"}:
            continue
        setattr(entity, name, tuple(value) if isinstance(value, list) else value)
    if entity.is_a("IfcStair") and entity.ShapeType is None:
        entity.ShapeType = "NOTDEFINED"
    if entity.is_a("IfcRoof") and entity.ShapeType is None:
        entity.ShapeType = "NOTDEFINED"
    if entity.is_a("IfcRailing") and entity.PredefinedType is None:
        entity.PredefinedType = "NOTDEFINED"


def _nearest_spatial_parent(
    entity_id: str,
    records: Mapping[str, Mapping[str, Any]],
    entities: Mapping[str, Any],
) -> Any | None:
    seen: set[str] = set()
    current = entity_id
    while current not in seen:
        seen.add(current)
        placement = records[current]["attributes"].get("ObjectPlacement")
        if placement is None:
            return None
        parent_id = placement["relative_to"]
        parent = entities[parent_id]
        if parent.is_a("IfcSpatialStructureElement"):
            return parent
        current = parent_id
    return None


def _add_wall_standard_case_material(
    ifc_file: Any,
    wall: Any,
    representation: Mapping[str, Any] | None,
    material_assignment: Mapping[str, Any] | None = None,
) -> None:
    if representation is None:
        raise ValueError(
            "IfcWallStandardCase requires a generated material layer usage."
        )
    profile = representation["profile"]
    if profile["kind"] != "rectangle":
        raise ValueError(
            "IfcWallStandardCase material thickness requires a rectangle profile."
        )
    if material_assignment is None:
        material_assignment = {
            "layer_set_name": "text2IFC generated wall layer",
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "offset_from_reference_line": 0.0,
            "layers": [
                {
                    "name": "text2IFC generated material",
                    "thickness": float(profile["y"]),
                }
            ],
        }
    layer_set = add_material_set(
        ifc_file,
        name=material_assignment["layer_set_name"],
        set_type="IfcMaterialLayerSet",
    )
    for layer_data in material_assignment["layers"]:
        material = add_material(ifc_file, name=layer_data["name"])
        layer = add_layer(ifc_file, layer_set=layer_set, material=material)
        layer.LayerThickness = float(layer_data["thickness"])
    assign_material(
        ifc_file,
        products=[wall],
        type="IfcMaterialLayerSetUsage",
        material=layer_set,
    )
    usage = _material_layer_set_usage(wall)
    usage.LayerSetDirection = material_assignment["direction"]
    usage.DirectionSense = material_assignment["direction_sense"]
    usage.OffsetFromReferenceLine = float(
        material_assignment["offset_from_reference_line"]
    )


def _material_layer_set_usage(wall: Any) -> Any:
    for relation in wall.HasAssociations:
        if not relation.is_a("IfcRelAssociatesMaterial"):
            continue
        material = relation.RelatingMaterial
        if material.is_a("IfcMaterialLayerSetUsage"):
            return material
    raise ValueError("IfcWallStandardCase material layer usage was not created.")


def _first_material_assignment(record: Mapping[str, Any]) -> Mapping[str, Any] | None:
    assignments = record.get("materials") or []
    if not assignments:
        return None
    return assignments[0]


def build_ifc_v2(document: Mapping[str, Any]) -> BootstrapResult:
    ifc_file = create_file(version="IFC2X3")
    _create_owner_metadata(ifc_file)

    records = {record["id"]: record for record in document["entities"]}
    entities: dict[str, Any] = {}
    for record in document["entities"]:
        attributes = record["attributes"]
        entity = create_entity(
            ifc_file,
            ifc_class=record["ifc_class"],
            name=attributes.get("Name"),
        )
        assign_identity(
            ifc_file,
            entity,
            contract_version="bim-json/2.0",
            object_kind=record["ifc_class"],
            bim_json_id=record["id"],
            global_id=record.get("global_id"),
        )
        _apply_v2_attributes(entity, attributes)
        apply_v2_properties(
            ifc_file, entity, record.get("property_sets", {})
        )
        entities[record["id"]] = entity

    millimetre = ifc_file.createIfcSIUnit(
        None, "LENGTHUNIT", "MILLI", "METRE"
    )
    assign_unit(ifc_file, units=[millimetre])
    model_context = add_context(ifc_file, context_type="Model")
    body_context = add_context(
        ifc_file,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=model_context,
    )

    pending = {
        record["id"]
        for record in document["entities"]
        if "ObjectPlacement" in record["attributes"]
    }
    while pending:
        progressed = False
        for entity_id in sorted(pending):
            placement = records[entity_id]["attributes"]["ObjectPlacement"]
            parent_id = placement["relative_to"]
            parent = entities[parent_id]
            if (
                parent.is_a("IfcProduct")
                and parent.ObjectPlacement is None
                and not parent.is_a("IfcProject")
            ):
                continue
            assign_v2_placement(
                ifc_file, entities[entity_id], placement, parent
            )
            pending.remove(entity_id)
            progressed = True
            break
        if not progressed:
            raise ValueError("cannot resolve BIM JSON 2.0 placement order")

    for record in document["entities"]:
        entity = entities[record["id"]]
        representation = record["attributes"].get("Representation")
        if representation is not None:
            add_v2_geometry(
                ifc_file,
                entity,
                representation,
                body_context,
            )
        if entity.is_a() == "IfcWallStandardCase":
            _add_wall_standard_case_material(
                ifc_file,
                entity,
                representation,
                _first_material_assignment(record),
            )

    for record in document["entities"]:
        entity = entities[record["id"]]
        if not entity.is_a("IfcProduct") or entity.is_a("IfcProject"):
            continue
        placement = record["attributes"].get("ObjectPlacement")
        if placement is None:
            continue
        parent = entities[placement["relative_to"]]
        if entity.is_a("IfcSpatialStructureElement"):
            if parent.is_a("IfcObjectDefinition"):
                assign_object(
                    ifc_file, products=[entity], relating_object=parent
                )
        elif not entity.is_a("IfcOpeningElement"):
            container = _nearest_spatial_parent(
                record["id"], records, entities
            )
            if container is not None:
                assign_container(
                    ifc_file,
                    products=[entity],
                    relating_structure=container,
                )

    add_v2_relationships(
        ifc_file, document["relationships"], entities
    )
    return BootstrapResult(ifc_file=ifc_file, body_context=body_context)
