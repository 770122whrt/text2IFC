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
from ifcopenshell.api.project.create_file import create_file
from ifcopenshell.api.root.create_entity import create_entity
from ifcopenshell.api.spatial.assign_container import assign_container
from ifcopenshell.api.unit.assign_unit import assign_unit

from .geometry import add_element_geometry, element_x_extent_m
from .identity import assign_identity
from .properties import apply_selected_properties


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
