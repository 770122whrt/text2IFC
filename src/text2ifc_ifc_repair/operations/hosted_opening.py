"""Family-neutral IFC2X3 hosted Opening geometry and topology primitives."""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass
from typing import Any, Mapping

import ifcopenshell.api.geometry
import ifcopenshell.guid
import ifcopenshell.util.unit

from text2ifc_ifc_repair.geometry import (
    UNSUPPORTED_WALL_GEOMETRY,
    opening_dimensions_mm,
    opening_position_in_wall_mm,
    straight_wall_axis,
    wall_dimensions_mm,
)
from text2ifc_ifc_repair.registry import OperationRegistryError
from text2ifc_ifc_repair.spatial import resolve_opening_storey


@dataclass(frozen=True)
class HostedOpeningFootprint:
    host_wall_global_id: str
    center_offset_mm: float
    width_mm: float
    sill_height_mm: float
    height_mm: float

    @property
    def horizontal_interval_mm(self) -> tuple[float, float]:
        half = self.width_mm / 2.0
        return self.center_offset_mm - half, self.center_offset_mm + half

    @property
    def vertical_interval_mm(self) -> tuple[float, float]:
        return self.sill_height_mm, self.sill_height_mm + self.height_mm

    def to_dict(self) -> dict[str, Any]:
        return {
            "host_wall_global_id": self.host_wall_global_id,
            "center_offset_mm": self.center_offset_mm,
            "width_mm": self.width_mm,
            "sill_height_mm": self.sill_height_mm,
            "height_mm": self.height_mm,
            "horizontal_interval_mm": list(self.horizontal_interval_mm),
            "vertical_interval_mm": list(self.vertical_interval_mm),
        }


def footprint_from_operation(
    operation: Mapping[str, Any],
) -> HostedOpeningFootprint:
    target = operation.get("target", {})
    parameters = operation["parameters"]
    opening = parameters["opening"]
    wall_id = (
        target.get("wall_global_id")
        or parameters.get("host_wall_global_id")
        or opening.get("host_wall_global_id")
    )
    if not wall_id:
        raise OperationRegistryError(
            "HOSTED_OPENING_WALL_REQUIRED",
            str(operation.get("operation_id", "")),
        )
    return HostedOpeningFootprint(
        host_wall_global_id=str(wall_id),
        center_offset_mm=float(parameters["position"]["center_offset_mm"]),
        width_mm=float(opening["width_mm"]),
        sill_height_mm=float(opening["sill_height_mm"]),
        height_mm=float(opening["height_mm"]),
    )


def footprints_overlap(
    first: HostedOpeningFootprint,
    second: HostedOpeningFootprint,
    *,
    tolerance_mm: float = 1e-6,
) -> bool:
    if first.host_wall_global_id != second.host_wall_global_id:
        return False
    horizontal = _interval_overlap(
        first.horizontal_interval_mm,
        second.horizontal_interval_mm,
        tolerance_mm=tolerance_mm,
    )
    vertical = _interval_overlap(
        first.vertical_interval_mm,
        second.vertical_interval_mm,
        tolerance_mm=tolerance_mm,
    )
    return horizontal and vertical


def hosted_opening_conflict_checker(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
) -> list[dict[str, str]]:
    first = footprint_from_operation(previous)
    second = footprint_from_operation(current)
    if not footprints_overlap(first, second):
        return []
    return [
        {
            "code": "BATCH_OPENING_OVERLAP",
            "path": "/parameters/position/center_offset_mm",
            "message": (
                "Opening overlaps another operation in the hosted_opening "
                f"domain: {previous['operation_id']}."
            ),
        }
    ]


def check_hosted_opening_preconditions(
    *,
    operation: Mapping[str, Any],
    model: Any,
    ignore_opening_global_id: str | None = None,
) -> dict[str, Any]:
    footprint = footprint_from_operation(operation)
    try:
        wall = require_guid(model, footprint.host_wall_global_id, "IfcWall")
    except OperationRegistryError as error:
        return _issue(error.code, "/target", error.detail)
    try:
        straight_wall_axis(wall)
        dimensions = {
            key: round(float(value), 6)
            for key, value in wall_dimensions_mm(wall).items()
        }
    except ValueError as error:
        code = (
            UNSUPPORTED_WALL_GEOMETRY
            if str(error) == UNSUPPORTED_WALL_GEOMETRY
            else "WALL_GEOMETRY_UNAVAILABLE"
        )
        return _issue(code, "/target", footprint.host_wall_global_id)
    checks: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    horizontal = footprint.horizontal_interval_mm
    vertical = footprint.vertical_interval_mm
    _check(
        checks,
        issues,
        "OPENING_WITHIN_WALL_HORIZONTAL",
        horizontal[0] >= 0 and horizontal[1] <= dimensions["length"],
        "OPENING_OUTSIDE_WALL_HORIZONTAL",
        "/parameters/position/center_offset_mm",
        {"requested_interval_mm": list(horizontal)},
    )
    _check(
        checks,
        issues,
        "OPENING_WITHIN_WALL_VERTICAL",
        vertical[0] >= 0 and vertical[1] <= dimensions["height"],
        "OPENING_OUTSIDE_WALL_VERTICAL",
        "/parameters/opening",
        {"requested_interval_mm": list(vertical)},
    )
    _check(
        checks,
        issues,
        "WALL_VOID_DEPTH_RESOLVED",
        dimensions["thickness"] > 0,
        "WALL_VOID_DEPTH_UNRESOLVED",
        "/target",
        {"wall_thickness_mm": dimensions["thickness"]},
    )
    overlap = None
    existing_regions = []
    for relationship in wall.HasOpenings:
        existing = relationship.RelatedOpeningElement
        if str(existing.GlobalId) == ignore_opening_global_id:
            continue
        measured = opening_dimensions_mm(existing)
        positioned = opening_position_in_wall_mm(existing, wall)
        candidate = HostedOpeningFootprint(
            host_wall_global_id=footprint.host_wall_global_id,
            center_offset_mm=float(positioned["center_offset"]),
            width_mm=float(measured["width"]),
            sill_height_mm=float(positioned["sill_height"]),
            height_mm=float(measured["height"]),
        )
        existing_regions.append(candidate.to_dict())
        if footprints_overlap(footprint, candidate):
            overlap = candidate.to_dict()
    _check(
        checks,
        issues,
        "OPENING_INTERVAL_AVAILABLE",
        overlap is None,
        "OPENING_OVERLAP",
        "/parameters/position/center_offset_mm",
        {"overlapping_region_mm": overlap},
    )
    return {
        "checks": checks,
        "issues": issues,
        "evidence": {
            "footprint": footprint.to_dict(),
            "wall_dimensions_mm": dimensions,
            "existing_opening_regions_mm": sorted(
                existing_regions,
                key=lambda item: (
                    item["center_offset_mm"],
                    item["sill_height_mm"],
                ),
            ),
        },
    }


def create_hosted_opening(
    *,
    model: Any,
    operation: Mapping[str, Any],
    wall: Any,
    role_prefix: str = "",
) -> dict[str, Any]:
    footprint = footprint_from_operation(operation)
    thickness = float(wall_dimensions_mm(wall)["thickness"])
    prefix = f"{role_prefix}_" if role_prefix else ""
    opening_id = deterministic_global_id(operation, f"{prefix}opening")
    void_id = deterministic_global_id(operation, f"{prefix}voids_relationship")
    assert_ids_available(model, (opening_id, void_id))
    opening = model.create_entity(
        "IfcOpeningElement",
        GlobalId=opening_id,
        OwnerHistory=wall.OwnerHistory,
        Name=f"Text2IFC opening {operation['operation_id']}",
        ObjectType="Opening",
        Tag=str(operation["operation_id"]),
    )
    representation = ifcopenshell.api.geometry.add_wall_representation(
        model,
        context=body_context(model),
        length=footprint.width_mm / 1000.0,
        height=footprint.height_mm / 1000.0,
        thickness=thickness / 1000.0,
        offset=-thickness / 2000.0,
    )
    opening.Representation = model.create_entity(
        "IfcProductDefinitionShape", Representations=[representation]
    )
    opening.ObjectPlacement = opening_placement(
        model,
        wall=wall,
        center_mm=footprint.center_offset_mm,
        width_mm=footprint.width_mm,
        sill_mm=footprint.sill_height_mm,
    )
    void = model.create_entity(
        "IfcRelVoidsElement",
        GlobalId=void_id,
        OwnerHistory=wall.OwnerHistory,
        RelatingBuildingElement=wall,
        RelatedOpeningElement=opening,
    )
    return {
        "opening": opening,
        "voids_relationship": void,
        "opening_depth_mm": thickness,
        "footprint": footprint,
    }


def deterministic_global_id(
    operation: Mapping[str, Any],
    role: str,
) -> str:
    canonical = json.dumps(
        operation, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    value = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"https://text2ifc.local/ifc-repair/{role}/{canonical}",
    )
    return ifcopenshell.guid.compress(value.hex)


def assert_ids_available(model: Any, global_ids: Any) -> None:
    for global_id in global_ids:
        try:
            existing = model.by_guid(str(global_id))
        except RuntimeError:
            existing = None
        if existing is not None:
            raise OperationRegistryError(
                "DETERMINISTIC_GLOBAL_ID_COLLISION", str(global_id)
            )


def body_context(model: Any) -> Any:
    preferred = [
        context
        for context in model.by_type("IfcGeometricRepresentationSubContext")
        if context.ContextIdentifier == "Body"
        and context.TargetView == "MODEL_VIEW"
    ]
    if preferred:
        return min(preferred, key=lambda context: context.id())
    body_contexts = [
        context
        for context in model.by_type("IfcGeometricRepresentationSubContext")
        if context.ContextIdentifier == "Body"
    ]
    if body_contexts:
        return min(body_contexts, key=lambda context: context.id())
    model_contexts = [
        context
        for context in model.by_type("IfcGeometricRepresentationContext")
        if context.is_a() == "IfcGeometricRepresentationContext"
        and str(getattr(context, "ContextType", "")) == "Model"
        and int(getattr(context, "CoordinateSpaceDimension", 0) or 0) == 3
    ]
    if not model_contexts:
        raise OperationRegistryError("BODY_CONTEXT_NOT_FOUND", "Body/MODEL_VIEW")
    return min(model_contexts, key=lambda context: context.id())


def millimetres_to_project_units(model_or_entity: Any, value: float) -> float:
    return float(value) / _millimetres_per_project_unit(model_or_entity)


def project_units_to_millimetres(model_or_entity: Any, value: float) -> float:
    return float(value) * _millimetres_per_project_unit(model_or_entity)


def _millimetres_per_project_unit(model_or_entity: Any) -> float:
    model = (
        model_or_entity
        if hasattr(model_or_entity, "by_type")
        else model_or_entity.file
    )
    return float(ifcopenshell.util.unit.calculate_unit_scale(model)) * 1000.0


def opening_placement(
    model: Any,
    *,
    wall: Any,
    center_mm: float,
    width_mm: float,
    sill_mm: float,
) -> Any:
    start, end = straight_wall_axis(wall)
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    direction = (dx / length, dy / length, 0.0)
    left = millimetres_to_project_units(
        model, center_mm - width_mm / 2.0
    )
    sill = millimetres_to_project_units(model, sill_mm)
    location = (
        start[0] + direction[0] * left,
        start[1] + direction[1] * left,
        start[2] + sill,
    )
    return local_placement(
        model,
        relative_to=wall.ObjectPlacement,
        location=location,
        ref_direction=direction,
    )


def local_placement(
    model: Any,
    *,
    relative_to: Any,
    location: tuple[float, float, float],
    ref_direction: tuple[float, float, float] = (1.0, 0.0, 0.0),
) -> Any:
    point = model.create_entity("IfcCartesianPoint", Coordinates=location)
    axis = model.create_entity(
        "IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)
    )
    direction = model.create_entity(
        "IfcDirection", DirectionRatios=ref_direction
    )
    placement = model.create_entity(
        "IfcAxis2Placement3D",
        Location=point,
        Axis=axis,
        RefDirection=direction,
    )
    return model.create_entity(
        "IfcLocalPlacement",
        PlacementRelTo=relative_to,
        RelativePlacement=placement,
    )


def wall_containment(wall: Any) -> Any:
    relationships = [
        relationship
        for relationship in wall.ContainedInStructure
        if relationship.RelatingStructure.is_a("IfcBuildingStorey")
    ]
    if len(relationships) != 1:
        raise OperationRegistryError(
            "TARGET_WALL_STOREY_AMBIGUOUS", str(wall.GlobalId)
        )
    return relationships[0]


def opening_storey(opening: Any, wall: Any) -> Any:
    """Resolve the retained Opening's spatial level from surviving geometry.

    Multi-storey walls may be contained at their base level while hosted doors
    belong to a higher level.  The closest storey elevation to the Opening
    base is the deterministic public fact available after the Door is removed.
    """

    try:
        return resolve_opening_storey(opening, wall)
    except ValueError as error:
        code, _, detail = str(error).partition(":")
        raise OperationRegistryError(
            code or "OPENING_STOREY_NOT_FOUND",
            detail or str(opening.GlobalId),
        ) from error


def opening_storey_containment(opening: Any, wall: Any) -> Any:
    storey = opening_storey(opening, wall)
    relationships = list(storey.ContainsElements)
    if len(relationships) != 1:
        raise OperationRegistryError(
            "OPENING_STOREY_CONTAINMENT_AMBIGUOUS",
            str(storey.GlobalId),
        )
    return relationships[0]


def add_to_containment(containment: Any, element: Any) -> None:
    containment.RelatedElements = sorted_roots(
        [*containment.RelatedElements, element]
    )


def sorted_roots(entities: list[Any]) -> list[Any]:
    unique = {entity.id(): entity for entity in entities}
    return sorted(
        unique.values(),
        key=lambda entity: (str(getattr(entity, "GlobalId", "")), entity.id()),
    )


def require_guid(model: Any, global_id: str, ifc_class: str) -> Any:
    try:
        entity = model.by_guid(global_id)
    except RuntimeError as error:
        raise OperationRegistryError("IFC_ENTITY_NOT_FOUND", global_id) from error
    if not entity.is_a(ifc_class):
        raise OperationRegistryError(
            "IFC_ENTITY_CLASS_MISMATCH",
            f"{global_id}:{entity.is_a()}",
        )
    return entity


def _interval_overlap(
    first: tuple[float, float],
    second: tuple[float, float],
    *,
    tolerance_mm: float,
) -> bool:
    return min(first[1], second[1]) - max(first[0], second[0]) > tolerance_mm


def _check(
    checks: list[dict[str, Any]],
    issues: list[dict[str, str]],
    code: str,
    passed: bool,
    failure_code: str,
    path: str,
    evidence: Mapping[str, Any],
) -> None:
    checks.append(
        {
            "code": code,
            "status": "passed" if passed else "failed",
            "evidence": dict(evidence),
        }
    )
    if not passed:
        issues.append(
            {
                "code": failure_code,
                "path": path,
                "message": failure_code.replace("_", " ").title(),
            }
        )


def _issue(code: str, path: str, detail: str) -> dict[str, Any]:
    return {
        "checks": [
            {"code": code, "status": "failed", "evidence": {"detail": detail}}
        ],
        "issues": [{"code": code, "path": path, "message": detail}],
        "evidence": {},
    }


__all__ = [
    "HostedOpeningFootprint",
    "add_to_containment",
    "assert_ids_available",
    "body_context",
    "check_hosted_opening_preconditions",
    "create_hosted_opening",
    "deterministic_global_id",
    "footprint_from_operation",
    "footprints_overlap",
    "hosted_opening_conflict_checker",
    "local_placement",
    "opening_placement",
    "require_guid",
    "sorted_roots",
    "wall_containment",
]
