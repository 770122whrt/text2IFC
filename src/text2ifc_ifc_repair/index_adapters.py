from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Protocol

import ifcopenshell.util.placement
import ifcopenshell.util.unit

from .geometry import (
    UNSUPPORTED_WALL_GEOMETRY,
    opening_dimensions_mm,
    opening_position_in_wall_mm,
    straight_wall_axis,
    wall_dimensions_mm,
)
from .index_models import RelationshipFact


@dataclass(frozen=True)
class AdapterResult:
    geometry_capability: str
    geometry_summary: dict[str, Any] = field(default_factory=dict)
    facets: dict[str, Any] = field(default_factory=dict)
    relationships: tuple[RelationshipFact, ...] = ()
    warnings: tuple[tuple[str, str, dict[str, Any]], ...] = ()


class ElementIndexAdapter(Protocol):
    ifc_classes: tuple[str, ...]

    def extract(self, entity: Any) -> AdapterResult: ...


class IndexAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: list[ElementIndexAdapter] = []

    def register(self, adapter: ElementIndexAdapter) -> None:
        if not adapter.ifc_classes:
            raise ValueError("INDEX_ADAPTER_CLASSES_REQUIRED")
        registered = set(adapter.ifc_classes)
        self._adapters = [
            existing
            for existing in self._adapters
            if not registered.intersection(existing.ifc_classes)
        ]
        self._adapters.append(adapter)

    @property
    def ifc_classes(self) -> tuple[str, ...]:
        return tuple(
            ifc_class
            for adapter in self._adapters
            for ifc_class in adapter.ifc_classes
        )

    def adapter_for(self, entity: Any) -> ElementIndexAdapter | None:
        for adapter in reversed(self._adapters):
            if any(entity.is_a(ifc_class) for ifc_class in adapter.ifc_classes):
                return adapter
        return None


class WallIndexAdapter:
    ifc_classes = ("IfcWall",)

    def extract(self, entity: Any) -> AdapterResult:
        relationships = list(
            RelationshipFact(
                kind="voids_opening",
                target_global_id=str(relation.RelatedOpeningElement.GlobalId),
                provenance="IfcRelVoidsElement",
            )
            for relation in getattr(entity, "HasOpenings", ())
            if getattr(relation.RelatedOpeningElement, "GlobalId", None)
        )
        space_names: set[str] = set()
        for boundary in getattr(entity, "ProvidesBoundaries", ()):
            space = getattr(boundary, "RelatingSpace", None)
            space_id = getattr(space, "GlobalId", None)
            if space_id:
                relationships.append(
                    RelationshipFact(
                        "bounds_space", str(space_id), "IfcRelSpaceBoundary"
                    )
                )
            name = getattr(space, "Name", None)
            if name:
                space_names.add(str(name))
        wall_facets = {
            "editable_target": True,
            "space_names": sorted(space_names),
        }
        try:
            start, end = straight_wall_axis(entity)
            millimetres_per_project_unit = (
                ifcopenshell.util.unit.calculate_unit_scale(entity.file)
                * 1000.0
            )
            start_mm = [
                value * millimetres_per_project_unit for value in start
            ]
            end_mm = [
                value * millimetres_per_project_unit for value in end
            ]
            delta = [end[index] - start[index] for index in range(3)]
            length = math.sqrt(sum(value * value for value in delta))
            direction = [value / length for value in delta]
            try:
                matrix = ifcopenshell.util.placement.get_local_placement(
                    entity.ObjectPlacement
                )
                millimetres_per_project_unit = (
                    ifcopenshell.util.unit.calculate_unit_scale(entity.file)
                    * 1000.0
                )
                world_start_raw = matrix @ [*start, 1.0]
                world_end_raw = matrix @ [*end, 1.0]
                world_start = [
                    float(world_start_raw[index])
                    * millimetres_per_project_unit
                    for index in range(3)
                ]
                world_end = [
                    float(world_end_raw[index])
                    * millimetres_per_project_unit
                    for index in range(3)
                ]
                world_delta = [
                    world_end[index] - world_start[index]
                    for index in range(3)
                ]
                world_length = math.sqrt(
                    sum(value * value for value in world_delta)
                )
                world_direction = [
                    value / world_length for value in world_delta
                ]
            except Exception:
                world_start = start
                world_direction = direction
            summary = {
                "coordinate_basis": {
                    "reference": "wall_local_start",
                    "axis_start_mm": start_mm,
                    "axis_end_mm": end_mm,
                    "axis_direction": direction,
                    "vertical_direction": [0.0, 0.0, 1.0],
                    "world_axis_start_mm": world_start,
                    "world_axis_direction": world_direction,
                },
                "orientation": _readable_orientation(world_direction),
            }
            try:
                summary["dimensions_mm"] = wall_dimensions_mm(entity)
            except Exception as error:
                return AdapterResult(
                    geometry_capability="straight_wall",
                    geometry_summary=summary,
                    facets=wall_facets,
                    relationships=tuple(relationships),
                    warnings=(("INDEX_WALL_DIMENSIONS_UNAVAILABLE", str(error), {}),),
                )
            return AdapterResult(
                geometry_capability="straight_wall",
                geometry_summary=summary,
                facets=wall_facets,
                relationships=tuple(relationships),
            )
        except ValueError as error:
            if str(error) != UNSUPPORTED_WALL_GEOMETRY:
                raise
            return AdapterResult(
                geometry_capability="unsupported_or_approximate",
                facets=wall_facets,
                relationships=tuple(relationships),
                warnings=((UNSUPPORTED_WALL_GEOMETRY, str(error), {}),),
            )


class FillingIndexAdapter:
    def extract(self, entity: Any) -> AdapterResult:
        relationships: list[RelationshipFact] = []
        opening_ids: list[str] = []
        host_ids: list[str] = []
        for fill in getattr(entity, "FillsVoids", ()):
            opening = fill.RelatingOpeningElement
            opening_id = getattr(opening, "GlobalId", None)
            if opening_id:
                opening_ids.append(str(opening_id))
                relationships.append(
                    RelationshipFact(
                        "fills_opening", str(opening_id), "IfcRelFillsElement"
                    )
                )
            for void in getattr(opening, "VoidsElements", ()):
                host = void.RelatingBuildingElement
                host_id = getattr(host, "GlobalId", None)
                if host_id:
                    host_ids.append(str(host_id))
                    relationships.append(
                        RelationshipFact(
                            "hosted_by_wall", str(host_id), "IfcRelVoidsElement"
                        )
                    )
        millimetres_per_project_unit = (
            ifcopenshell.util.unit.calculate_unit_scale(entity.file) * 1000.0
        )
        dimensions = {
            "overall_width": (
                None
                if getattr(entity, "OverallWidth", None) is None
                else float(entity.OverallWidth) * millimetres_per_project_unit
            ),
            "overall_height": (
                None
                if getattr(entity, "OverallHeight", None) is None
                else float(entity.OverallHeight) * millimetres_per_project_unit
            ),
        }
        return AdapterResult(
            geometry_capability="opening_filling",
            geometry_summary={"dimensions_mm": dimensions},
            facets={
                "editable_target": True,
                "opening_global_ids": sorted(set(opening_ids)),
                "host_wall_global_ids": sorted(set(host_ids)),
            },
            relationships=tuple(sorted(relationships, key=lambda fact: (fact.kind, fact.target_global_id))),
        )


class DoorIndexAdapter(FillingIndexAdapter):
    ifc_classes = ("IfcDoor",)


class WindowIndexAdapter(FillingIndexAdapter):
    ifc_classes = ("IfcWindow",)


class _StructuralIndexAdapter:
    ifc_classes: tuple[str, ...]
    structural_family: str

    def extract(self, entity: Any) -> AdapterResult:
        axis = _structural_axis_capability(entity)
        section = _structural_section_capability(entity)
        measured = "measured_current_ifc"
        measured_count = sum(
            capability["status"] == measured for capability in (axis, section)
        )
        if measured_count == 2:
            geometry_capability = "measured_structural_member"
        elif measured_count == 1:
            geometry_capability = "structural_geometry_partial"
        else:
            geometry_capability = "structural_geometry_unmeasurable"

        warnings: tuple[tuple[str, str, dict[str, Any]], ...] = ()
        if measured_count != 2:
            warnings = (
                (
                    "INDEX_STRUCTURAL_GEOMETRY_UNAVAILABLE",
                    "Structural axis or rectangular section could not be measured "
                    "from explicit current-IFC representation evidence.",
                    {
                        "axis_status": axis["status"],
                        "section_status": section["status"],
                    },
                ),
            )

        return AdapterResult(
            geometry_capability=geometry_capability,
            geometry_summary={
                "axis_capability": axis,
                "section_capability": section,
                "representation_summary": _structural_representation_summary(
                    entity
                ),
            },
            facets={
                "editable_target": False,
                "structural_family": self.structural_family,
                "structural_evidence_authority": "diagnostic_only",
                "reference_resolution": "exact_identity_required",
            },
            warnings=warnings,
        )


class BeamIndexAdapter(_StructuralIndexAdapter):
    ifc_classes = ("IfcBeam",)
    structural_family = "beam"


class ColumnIndexAdapter(_StructuralIndexAdapter):
    ifc_classes = ("IfcColumn",)
    structural_family = "column"


class OpeningIndexAdapter:
    ifc_classes = ("IfcOpeningElement",)

    def extract(self, entity: Any) -> AdapterResult:
        voids = tuple(getattr(entity, "VoidsElements", ()))
        fills = tuple(getattr(entity, "HasFillings", ()))
        relationships: list[RelationshipFact] = []
        host_ids: list[str] = []
        filling_ids: list[str] = []
        for relation in voids:
            host_id = getattr(relation.RelatingBuildingElement, "GlobalId", None)
            if host_id:
                host_ids.append(str(host_id))
                relationships.append(
                    RelationshipFact(
                        "hosted_by_wall", str(host_id), "IfcRelVoidsElement"
                    )
                )
        for relation in fills:
            filling_id = getattr(relation.RelatedBuildingElement, "GlobalId", None)
            if filling_id:
                filling_ids.append(str(filling_id))
                relationships.append(
                    RelationshipFact(
                        "filled_by", str(filling_id), "IfcRelFillsElement"
                    )
                )
        facets = {
            "editable_target": len(host_ids) == 1,
            "host_wall_global_ids": sorted(set(host_ids)),
            "filling_global_ids": sorted(set(filling_ids)),
            "fill_state": "empty" if not filling_ids else "filled",
        }
        warnings: list[tuple[str, str, dict[str, Any]]] = []
        summary: dict[str, Any] = {}
        if len(host_ids) != 1:
            warnings.append(
                (
                    "INDEX_OPENING_HOST_INVALID",
                    "Opening must have exactly one reliable host relationship.",
                    {"host_count": len(host_ids)},
                )
            )
            return AdapterResult(
                geometry_capability="opening_topology_invalid",
                geometry_summary=summary,
                facets={**facets, "editable_target": False},
                relationships=tuple(relationships),
                warnings=tuple(warnings),
            )
        host = voids[0].RelatingBuildingElement
        try:
            summary["dimensions_mm"] = opening_dimensions_mm(entity)
            position = opening_position_in_wall_mm(entity, host)
            summary["wall_local_position_mm"] = {
                "reference": "wall_local_start",
                "center_offset_mm": position["center_offset"],
                "sill_height_mm": position["sill_height"],
                "normal_offset_mm": position["normal_offset"],
            }
            summary["geometry_bounds_in_host_mm"] = position[
                "geometry_bounds_mm"
            ]
            capability = "measured_hosted_opening"
        except Exception as error:
            capability = "opening_geometry_unmeasurable"
            facets["editable_target"] = False
            warnings.append(
                (
                    "INDEX_OPENING_GEOMETRY_UNAVAILABLE",
                    str(error),
                    {"host_global_id": host_ids[0]},
                )
            )
        return AdapterResult(
            geometry_capability=capability,
            geometry_summary=summary,
            facets=facets,
            relationships=tuple(
                sorted(
                    relationships,
                    key=lambda fact: (fact.kind, fact.target_global_id),
                )
            ),
            warnings=tuple(warnings),
        )


class SpaceIndexAdapter:
    ifc_classes = ("IfcSpace",)

    def extract(self, entity: Any) -> AdapterResult:
        relationships = list(
            RelationshipFact(
                "decomposes_from",
                str(relation.RelatingObject.GlobalId),
                "IfcRelAggregates",
            )
            for relation in getattr(entity, "Decomposes", ())
            if getattr(relation.RelatingObject, "GlobalId", None)
        )
        boundary_wall_ids: set[str] = set()
        for boundary in getattr(entity, "BoundedBy", ()):
            wall = getattr(boundary, "RelatedBuildingElement", None)
            wall_id = getattr(wall, "GlobalId", None)
            if wall_id:
                boundary_wall_ids.add(str(wall_id))
                relationships.append(
                    RelationshipFact(
                        "bounded_by_wall",
                        str(wall_id),
                        "IfcRelSpaceBoundary",
                    )
                )
        summary: dict[str, Any] = {}
        warnings: tuple[tuple[str, str, dict[str, Any]], ...] = ()
        try:
            import ifcopenshell.geom

            shape = ifcopenshell.geom.create_shape(
                ifcopenshell.geom.settings(), entity
            )
            vertices = shape.geometry.verts
            axes = [vertices[index::3] for index in range(3)]
            summary["centroid_mm"] = [
                (float(min(axis)) + float(max(axis))) * 500.0
                for axis in axes
            ]
            summary["bounds_mm"] = {
                axis_name: [
                    float(min(axes[index])) * 1000.0,
                    float(max(axes[index])) * 1000.0,
                ]
                for index, axis_name in enumerate(("x", "y", "z"))
            }
        except Exception as error:
            warnings = (
                (
                    "INDEX_SPACE_GEOMETRY_UNAVAILABLE",
                    str(error),
                    {},
                ),
            )
        return AdapterResult(
            geometry_capability="spatial_context",
            geometry_summary=summary,
            facets={
                "editable_target": False,
                "role": "room_context",
                "boundary_wall_global_ids": sorted(boundary_wall_ids),
                "boundary_evidence": "available"
                if getattr(entity, "BoundedBy", ())
                else "unavailable",
            },
            relationships=tuple(relationships),
            warnings=warnings,
        )


def default_index_adapter_registry() -> IndexAdapterRegistry:
    registry = IndexAdapterRegistry()
    for adapter in (
        WallIndexAdapter(),
        OpeningIndexAdapter(),
        DoorIndexAdapter(),
        WindowIndexAdapter(),
        BeamIndexAdapter(),
        ColumnIndexAdapter(),
        SpaceIndexAdapter(),
    ):
        registry.register(adapter)
    return registry


def _readable_orientation(direction: list[float]) -> str:
    angle = math.degrees(math.atan2(direction[1], direction[0])) % 360.0
    names = ("east", "north_east", "north", "north_west", "west", "south_west", "south", "south_east")
    return names[int((angle + 22.5) // 45.0) % 8]


def _number_or_none(value: Any) -> float | None:
    return None if value is None else float(value)


def _structural_axis_capability(entity: Any) -> dict[str, Any]:
    representation = getattr(entity, "Representation", None)
    candidates: list[Any] = []
    for shape in getattr(representation, "Representations", ()) or ():
        if str(getattr(shape, "RepresentationIdentifier", "")) != "Axis":
            continue
        candidates.extend(
            item
            for item in getattr(shape, "Items", ()) or ()
            if item.is_a("IfcPolyline")
        )
    if len(candidates) != 1:
        return {
            "status": "unavailable",
            "reason": "explicit_single_axis_polyline_required",
            "candidate_count": len(candidates),
            "authority": "diagnostic_only",
        }

    points = tuple(getattr(candidates[0], "Points", ()) or ())
    if len(points) != 2:
        return {
            "status": "unavailable",
            "reason": "axis_polyline_must_have_two_points",
            "candidate_count": 1,
            "point_count": len(points),
            "authority": "diagnostic_only",
        }
    try:
        millimetres_per_project_unit = (
            ifcopenshell.util.unit.calculate_unit_scale(entity.file) * 1000.0
        )
        placement = getattr(entity, "ObjectPlacement", None)
        matrix = (
            ifcopenshell.util.placement.get_local_placement(placement)
            if placement is not None
            else None
        )
        local_points = [
            [
                float(coordinate)
                for coordinate in tuple(point.Coordinates) + (0.0,) * (3 - len(point.Coordinates))
            ][:3]
            for point in points
        ]
        world_points: list[list[float]] = []
        for point in local_points:
            transformed = [*point, 1.0] if matrix is None else matrix @ [*point, 1.0]
            world_points.append(
                [
                    float(transformed[index]) * millimetres_per_project_unit
                    for index in range(3)
                ]
            )
        delta = [
            world_points[1][index] - world_points[0][index]
            for index in range(3)
        ]
        length_mm = math.sqrt(sum(value * value for value in delta))
        if length_mm <= 0.0:
            raise ValueError("zero_length_axis")
        return {
            "status": "measured_current_ifc",
            "world_start_mm": world_points[0],
            "world_end_mm": world_points[1],
            "world_direction": [value / length_mm for value in delta],
            "length_mm": length_mm,
            "provenance": "IfcShapeRepresentation.Axis/IfcPolyline",
            "authority": "diagnostic_only",
        }
    except Exception as error:
        return {
            "status": "unavailable",
            "reason": "axis_measurement_failed",
            "error": str(error),
            "authority": "diagnostic_only",
        }


def _structural_section_capability(entity: Any) -> dict[str, Any]:
    solids = [
        item
        for item in _structural_representation_items(entity)
        if item.is_a("IfcExtrudedAreaSolid")
        and getattr(item, "SweptArea", None) is not None
        and item.SweptArea.is_a("IfcRectangleProfileDef")
    ]
    if len(solids) != 1:
        return {
            "status": "unavailable",
            "reason": "explicit_single_rectangular_extrusion_required",
            "candidate_count": len(solids),
            "authority": "diagnostic_only",
        }
    try:
        solid = solids[0]
        scale = ifcopenshell.util.unit.calculate_unit_scale(entity.file) * 1000.0
        return {
            "status": "measured_current_ifc",
            "shape": "rectangle",
            "profile_x_mm": float(solid.SweptArea.XDim) * scale,
            "profile_y_mm": float(solid.SweptArea.YDim) * scale,
            "extrusion_depth_mm": float(solid.Depth) * scale,
            "provenance": "IfcExtrudedAreaSolid/IfcRectangleProfileDef",
            "authority": "diagnostic_only",
        }
    except Exception as error:
        return {
            "status": "unavailable",
            "reason": "section_measurement_failed",
            "error": str(error),
            "authority": "diagnostic_only",
        }


def _structural_representation_items(entity: Any) -> tuple[Any, ...]:
    representation = getattr(entity, "Representation", None)
    pending = [
        item
        for shape in getattr(representation, "Representations", ()) or ()
        for item in getattr(shape, "Items", ()) or ()
    ]
    results: dict[int, Any] = {}
    visited: set[int] = set()
    while pending:
        item = pending.pop()
        step_id = int(item.id())
        if step_id in visited:
            continue
        visited.add(step_id)
        if item.is_a("IfcMappedItem"):
            mapped = item.MappingSource.MappedRepresentation
            pending.extend(getattr(mapped, "Items", ()) or ())
        elif item.is_a("IfcBooleanResult"):
            pending.extend((item.FirstOperand, item.SecondOperand))
        else:
            results[step_id] = item
    return tuple(results[step_id] for step_id in sorted(results))


def _structural_representation_summary(entity: Any) -> dict[str, Any]:
    representation = getattr(entity, "Representation", None)
    shapes = tuple(getattr(representation, "Representations", ()) or ())
    return {
        "representations": [
            {
                "identifier": str(getattr(shape, "RepresentationIdentifier", None)),
                "type": str(getattr(shape, "RepresentationType", None)),
                "item_classes": sorted(item.is_a() for item in shape.Items),
            }
            for shape in shapes
        ],
        "resolved_item_classes": sorted(
            item.is_a() for item in _structural_representation_items(entity)
        ),
        "provenance": "current_ifc_representation",
        "authority": "diagnostic_only",
    }


__all__ = [
    "AdapterResult",
    "BeamIndexAdapter",
    "ColumnIndexAdapter",
    "ElementIndexAdapter",
    "IndexAdapterRegistry",
    "OpeningIndexAdapter",
    "default_index_adapter_registry",
]
