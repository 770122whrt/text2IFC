"""Deterministic BIM JSON 1.0 to BIM JSON 2.0 Draft migration."""

from __future__ import annotations

import copy
from typing import Any


KIND_TO_CLASS = {
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


def _entity(
    source: dict[str, Any],
    ifc_class: str,
    source_ref: str,
    *,
    parent_id: str | None = None,
    attributes: dict[str, Any] | None = None,
    property_sets: dict[str, Any] | None = None,
) -> dict[str, Any]:
    native = {"Name": source["name"], **(attributes or {})}
    if parent_id is not None:
        native["ObjectPlacement"] = {"relative_to": parent_id}
    return {
        "id": source["id"],
        "ifc_class": ifc_class,
        "attributes": native,
        "property_sets": property_sets or {},
        "provenance": {
            "source": source_ref,
            "source_contract": "bim-json/1.0",
            "source_id": source["id"],
        },
    }


def _element_properties(element: dict[str, Any], ifc_class: str):
    legacy = element.get("properties", {})
    result: dict[str, dict[str, Any]] = {}
    common_name = {
        "IfcWall": "Pset_WallCommon",
        "IfcColumn": "Pset_ColumnCommon",
        "IfcBeam": "Pset_BeamCommon",
    }.get(ifc_class)
    if common_name:
        values = {}
        if "is_external" in legacy:
            values["IsExternal"] = legacy["is_external"]
        if "load_bearing" in legacy:
            values["LoadBearing"] = legacy["load_bearing"]
        if values:
            result[common_name] = values
    if "predefined_type" in legacy:
        result["custom:text2ifc.Legacy"] = {
            "predefined_type": legacy["predefined_type"]
        }
    return result


def migrate_v1_document(document: dict[str, Any], source_ref: str):
    source = copy.deepcopy(document)
    entities: list[dict[str, Any]] = []
    entities.append(_entity(source["project"], "IfcProject", source_ref))
    entities.append(
        _entity(
            source["site"],
            "IfcSite",
            source_ref,
            parent_id=source["project"]["id"],
        )
    )
    entities.append(
        _entity(
            source["building"],
            "IfcBuilding",
            source_ref,
            parent_id=source["site"]["id"],
        )
    )
    for storey in source["storeys"]:
        entities.append(
            _entity(
                storey,
                "IfcBuildingStorey",
                source_ref,
                parent_id=source["building"]["id"],
                attributes={"Elevation": storey["elevation"]},
            )
        )
    for element in source["elements"]:
        ifc_class = KIND_TO_CLASS[element["kind"]]
        attributes = {
            "Representation": {
                "kind": "legacy_dimensions",
                "dimensions": copy.deepcopy(element["dimensions"]),
            }
        }
        if ifc_class in {"IfcDoor", "IfcWindow"}:
            attributes["OverallWidth"] = element["dimensions"]["width"]
            attributes["OverallHeight"] = element["dimensions"]["height"]
        legacy_type = element.get("properties", {}).get("predefined_type")
        if legacy_type and ifc_class == "IfcSlab":
            attributes["PredefinedType"] = legacy_type
        elif legacy_type and ifc_class in {"IfcStair", "IfcRoof"}:
            attributes["ShapeType"] = legacy_type
        entities.append(
            _entity(
                element,
                ifc_class,
                source_ref,
                parent_id=element["storey_id"],
                attributes=attributes,
                property_sets=_element_properties(element, ifc_class),
            )
        )

    missing = []
    clarifications = []
    for index, entity in enumerate(entities):
        if entity["ifc_class"] == "IfcProject":
            continue
        path = f"/entities/{index}/attributes/ObjectPlacement/origin"
        missing.append(
            {
                "entity_id": entity["id"],
                "path": path,
                "code": "MISSING_OBJECT_PLACEMENT",
                "message": "BIM JSON 1.0 did not contain source coordinates.",
            }
        )
        clarifications.append(
            {
                "entity_id": entity["id"],
                "path": path,
                "question": f"What is the parent-relative origin of {entity['id']}?",
            }
        )
    missing.append(
        {
            "entity_id": "document",
            "path": "/entities",
            "code": "UNKNOWN_SPACE_COVERAGE",
            "message": "BIM JSON 1.0 did not contain an IfcSpace inventory.",
        }
    )
    return {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": {
            "schema_version": "bim-json/2.0",
            "ifc_schema": "IFC2X3",
            "units": copy.deepcopy(source["units"]),
            "entities": entities,
            "relationships": [],
            "provenance": {
                "source": source_ref,
                "source_contract": "bim-json/1.0",
            },
        },
        "missing_facts": missing,
        "losses": [],
        "clarification_targets": clarifications,
        "provenance": {
            "source": source_ref,
            "migration": "bim-json/1.0-to-draft/1.0",
        },
    }
