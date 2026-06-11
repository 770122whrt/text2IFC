from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.util.element
from ifcopenshell.validate import json_logger, validate

from .identity import IDENTITY_PROPERTY, IDENTITY_PSET


@dataclass(frozen=True, order=True)
class IfcValidationIssue:
    code: str
    entity: str
    attribute: str
    message: str


def open_ifc(path: str | Path) -> Any:
    return ifcopenshell.open(str(Path(path)))


def _as_file(source: Any) -> Any:
    if isinstance(source, (str, Path)):
        return open_ifc(source)
    return source


def _entity_name(instance: Any) -> str:
    if instance is None:
        return ""
    try:
        return instance.is_a()
    except (AttributeError, RuntimeError):
        return type(instance).__name__


def _stable_message(value: Any) -> str:
    return str(value).splitlines()[0].strip()


def verify_ifc(source: Any) -> tuple[IfcValidationIssue, ...]:
    logger = json_logger()
    validate(_as_file(source), logger, express_rules=True)
    issues = {
        IfcValidationIssue(
            code=(
                "IFC_EXPRESS_RULE"
                if statement.get("type") == "express"
                else "IFC_SCHEMA_ERROR"
            ),
            entity=_entity_name(statement.get("instance")),
            attribute=str(statement.get("attribute") or ""),
            message=_stable_message(statement.get("message") or ""),
        )
        for statement in logger.statements
        if statement.get("level") == "error"
    }
    return tuple(sorted(issues))


def _bim_json_id(entity: Any) -> str:
    psets = ifcopenshell.util.element.get_psets(entity)
    return str(psets[IDENTITY_PSET][IDENTITY_PROPERTY])


def _children(entity: Any, ifc_class: str) -> list[Any]:
    return [
        child
        for relation in getattr(entity, "IsDecomposedBy", ())
        for child in relation.RelatedObjects
        if child.is_a(ifc_class)
    ]


def _only(items: list[Any], label: str) -> Any:
    if len(items) != 1:
        raise ValueError(f"Expected one {label}, found {len(items)}.")
    return items[0]


def hierarchy_snapshot(source: Any) -> dict[str, Any]:
    ifc_file = _as_file(source)
    project = _only(ifc_file.by_type("IfcProject"), "IfcProject")
    site = _only(_children(project, "IfcSite"), "aggregated IfcSite")
    building = _only(
        _children(site, "IfcBuilding"), "aggregated IfcBuilding"
    )
    storeys = sorted(
        _children(building, "IfcBuildingStorey"),
        key=lambda storey: (
            float(storey.Elevation or 0.0),
            _bim_json_id(storey),
        ),
    )
    return {
        "project": {
            "id": _bim_json_id(project),
            "name": project.Name,
        },
        "site": {"id": _bim_json_id(site), "name": site.Name},
        "building": {
            "id": _bim_json_id(building),
            "name": building.Name,
        },
        "storeys": [
            {
                "id": _bim_json_id(storey),
                "name": storey.Name,
                "elevation": storey.Elevation,
            }
            for storey in storeys
        ],
    }


def containment_map(source: Any) -> dict[str, str]:
    ifc_file = _as_file(source)
    result: dict[str, str] = {}
    for element in ifc_file.by_type("IfcElement"):
        storeys = [
            relation.RelatingStructure
            for relation in getattr(element, "ContainedInStructure", ())
            if relation.RelatingStructure.is_a("IfcBuildingStorey")
        ]
        storey = _only(storeys, f"storey for {_bim_json_id(element)}")
        result[_bim_json_id(element)] = _bim_json_id(storey)
    return result


def identity_map(source: Any) -> dict[str, str]:
    ifc_file = _as_file(source)
    entities = [
        *ifc_file.by_type("IfcProject"),
        *ifc_file.by_type("IfcSite"),
        *ifc_file.by_type("IfcBuilding"),
        *ifc_file.by_type("IfcBuildingStorey"),
        *ifc_file.by_type("IfcElement"),
    ]
    return {
        _bim_json_id(entity): str(entity.GlobalId)
        for entity in entities
    }


def measure_element_dimensions(
    source: Any, bim_json_id: str
) -> dict[str, float]:
    del source, bim_json_id
    raise NotImplementedError("IFC dimension measurement is not implemented.")
