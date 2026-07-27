from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Protocol

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
        relationships = tuple(
            RelationshipFact(
                kind="voids_opening",
                target_global_id=str(relation.RelatedOpeningElement.GlobalId),
                provenance="IfcRelVoidsElement",
            )
            for relation in getattr(entity, "HasOpenings", ())
            if getattr(relation.RelatedOpeningElement, "GlobalId", None)
        )
        try:
            start, end = straight_wall_axis(entity)
            delta = [end[index] - start[index] for index in range(3)]
            length = math.sqrt(sum(value * value for value in delta))
            direction = [value / length for value in delta]
            summary = {
                "coordinate_basis": {
                    "reference": "wall_local_start",
                    "axis_start_mm": start,
                    "axis_end_mm": end,
                    "axis_direction": direction,
                    "vertical_direction": [0.0, 0.0, 1.0],
                },
                "orientation": _readable_orientation(direction),
            }
            try:
                summary["dimensions_mm"] = wall_dimensions_mm(entity)
            except Exception as error:
                return AdapterResult(
                    geometry_capability="straight_wall",
                    geometry_summary=summary,
                    facets={"editable_target": True},
                    relationships=relationships,
                    warnings=(("INDEX_WALL_DIMENSIONS_UNAVAILABLE", str(error), {}),),
                )
            return AdapterResult(
                geometry_capability="straight_wall",
                geometry_summary=summary,
                facets={"editable_target": True},
                relationships=relationships,
            )
        except ValueError as error:
            if str(error) != UNSUPPORTED_WALL_GEOMETRY:
                raise
            return AdapterResult(
                geometry_capability="unsupported_or_approximate",
                facets={"editable_target": True},
                relationships=relationships,
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
        dimensions = {
            "overall_width": _number_or_none(getattr(entity, "OverallWidth", None)),
            "overall_height": _number_or_none(getattr(entity, "OverallHeight", None)),
        }
        return AdapterResult(
            geometry_capability="opening_filling",
            geometry_summary={"dimensions_project_units": dimensions},
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
        relationships = tuple(
            RelationshipFact(
                "decomposes_from",
                str(relation.RelatingObject.GlobalId),
                "IfcRelAggregates",
            )
            for relation in getattr(entity, "Decomposes", ())
            if getattr(relation.RelatingObject, "GlobalId", None)
        )
        return AdapterResult(
            geometry_capability="spatial_context",
            facets={
                "editable_target": False,
                "role": "room_context",
                "boundary_evidence": "available"
                if getattr(entity, "BoundedBy", ())
                else "unavailable",
            },
            relationships=relationships,
        )


def default_index_adapter_registry() -> IndexAdapterRegistry:
    registry = IndexAdapterRegistry()
    for adapter in (
        WallIndexAdapter(),
        OpeningIndexAdapter(),
        DoorIndexAdapter(),
        WindowIndexAdapter(),
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


__all__ = [
    "AdapterResult",
    "ElementIndexAdapter",
    "IndexAdapterRegistry",
    "OpeningIndexAdapter",
    "default_index_adapter_registry",
]
