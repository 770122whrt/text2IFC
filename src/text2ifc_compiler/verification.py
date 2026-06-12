from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.geom
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
        entity_type = instance.is_a()
    except (AttributeError, RuntimeError):
        return type(instance).__name__
    global_id = getattr(instance, "GlobalId", None)
    if global_id:
        return f"{entity_type}:{global_id}"
    try:
        return f"{entity_type}:#{instance.id()}"
    except (AttributeError, RuntimeError):
        return entity_type


def _stable_message(value: Any) -> str:
    return str(value).splitlines()[0].strip()


def verify_ifc(
    source: Any, *, express_rules: bool = True
) -> tuple[IfcValidationIssue, ...]:
    logger = json_logger()
    validate(_as_file(source), logger, express_rules=express_rules)
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
        *ifc_file.by_type("IfcProduct"),
    ]
    return {
        _bim_json_id(entity): str(entity.GlobalId)
        for entity in entities
    }


def measure_element_dimensions(
    source: Any, bim_json_id: str
) -> dict[str, float]:
    ifc_file = _as_file(source)
    try:
        global_id = identity_map(ifc_file)[bim_json_id]
    except KeyError as exc:
        raise KeyError(f"Unknown BIM JSON ID: {bim_json_id}") from exc
    element = ifc_file.by_guid(global_id)

    if element.is_a("IfcDoor") or element.is_a("IfcWindow"):
        return {
            "width": float(element.OverallWidth),
            "height": float(element.OverallHeight),
        }

    dimension_names_by_class = {
        "IfcWall": ("length", "thickness", "height"),
        "IfcColumn": ("width", "depth", "height"),
        "IfcBeam": ("length", "width", "height"),
        "IfcSlab": ("length", "width", "thickness"),
        "IfcStair": ("length", "width", "height"),
        "IfcStairFlight": ("run", "width", "rise"),
        "IfcRoof": ("length", "width", "thickness"),
    }
    try:
        dimension_names = dimension_names_by_class[element.is_a()]
    except KeyError as exc:
        raise ValueError(
            f"Element {bim_json_id!r} has unsupported IFC class "
            f"{element.is_a()!r}."
        ) from exc

    settings = ifcopenshell.geom.settings()
    shape = ifcopenshell.geom.create_shape(settings, element)
    vertices = shape.geometry.verts
    axes = (vertices[0::3], vertices[1::3], vertices[2::3])
    extents_mm = tuple(
        (max(axis) - min(axis)) * 1000.0 for axis in axes
    )
    return dict(zip(dimension_names, extents_mm, strict=True))
