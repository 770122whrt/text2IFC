"""Deterministic BIM JSON scaffold generation for explicit complex briefs."""

from __future__ import annotations

import re
import hashlib
from typing import Any, Mapping


PROVENANCE = {"source": "phase6.3-complex-scaffold"}


def build_scaffold_candidate(
    *,
    case_id: str,
    design_brief: Mapping[str, Any],
    expected_facts: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a compileable BIM JSON 2.0 scaffold from explicit expected facts.

    This helper is not a second BIM JSON schema and does not infer missing
    design facts. It only turns already-extracted Design Brief facts into
    low-level entities and relationships that the compiler requires.
    """

    known = design_brief.get("known_facts", {})
    known_facts = known if isinstance(known, Mapping) else {}
    building = known_facts.get("building", {})
    building_facts = building if isinstance(building, Mapping) else {}

    width = _required_number_alias(
        building_facts,
        ("width_x_mm", "overall_width_x", "x_dim_mm", "length_mm", "width_mm"),
    )
    depth = _required_number_alias(
        building_facts,
        ("depth_y_mm", "overall_depth_y", "y_dim_mm", "depth_mm", "width_mm"),
    )
    storey_height = _number_alias(building_facts, ("storey_height_mm",)) or _storey_height_from_expected(expected_facts)
    walls = known_facts.get("walls", {})
    wall_facts = walls if isinstance(walls, Mapping) else {}
    wall_thickness = (
        _number_alias(building_facts, ("wall_thickness_mm",))
        or _number_alias(known_facts, ("wall_thickness_mm",))
        or _required_number_alias(
            wall_facts,
            ("thickness_mm", "thickness"),
        )
    )
    default_slab_thickness = float(_number_alias(building_facts, ("slab_thickness_mm",)) or 150)

    entities: list[dict[str, Any]] = [
        _entity("project-1", "IfcProject", {"Name": f"{case_id} Project"}),
        _entity(
            "site-1",
            "IfcSite",
            {
                "Name": "Site",
                "ObjectPlacement": _placement("project-1"),
            },
        ),
        _entity(
            "building-1",
            "IfcBuilding",
            {
                "Name": "Building",
                "ObjectPlacement": _placement("site-1"),
            },
        ),
    ]
    relationships: list[dict[str, Any]] = []
    host_walls: dict[tuple[str, str], str] = {}

    storeys = _records(expected_facts.get("storeys"))
    for storey in storeys:
        storey_id = _required_text(storey, "id")
        elevation = float(storey.get("elevation_mm", 0))
        entities.append(
            _entity(
                storey_id,
                "IfcBuildingStorey",
                {
                    "Name": storey_id,
                    "Elevation": elevation,
                    "ObjectPlacement": _placement("building-1", [0, 0, elevation]),
                },
            )
        )
        for wall in _external_walls(
            storey_id=storey_id,
            width=width,
            depth=depth,
            wall_thickness=wall_thickness,
            storey_height=storey_height,
        ):
            entities.append(wall)

    for space in _records(expected_facts.get("spaces")):
        storey_id = _required_text(space, "storey")
        dimensions = _dimensions(space)
        if dimensions is None and isinstance(space.get("width_mm"), (int, float)):
            dimensions = (width, float(space["width_mm"]))
        if dimensions is None:
            dimensions = (width, min(depth, 1200))
        attributes: dict[str, Any] = {
            "Name": str(space.get("source_key", "Space")),
            "InteriorOrExteriorSpace": "INTERNAL",
            "ObjectPlacement": _placement(
                storey_id,
                _space_origin(space, width=width, depth=depth),
            ),
        }
        if dimensions is not None:
            attributes["Representation"] = _polygon_representation(
                [
                    [0, 0],
                    [dimensions[0], 0],
                    [dimensions[0], dimensions[1]],
                    [0, dimensions[1]],
                    [0, 0],
                ],
                float(_number_alias(space, ("height_mm", "height", "net_height")) or storey_height),
            )
        entities.append(
            _entity(
                _generated_id("space", space, len(entities)),
                "IfcSpace",
                attributes,
            )
        )

    for slab in _records(expected_facts.get("slabs")):
        storey_id = _storey_for_elevation(
            storeys,
            float(slab.get("elevation_mm", 0)),
        )
        thickness = float(slab.get("thickness_mm", default_slab_thickness))
        entities.append(
            _entity(
                _generated_id("slab", slab, len(entities)),
                "IfcSlab",
                {
                    "Name": str(slab.get("source_key", "Slab")),
                    "PredefinedType": "FLOOR",
                    "ObjectPlacement": _placement(storey_id),
                    "Representation": _polygon_representation(
                        [[0, 0], [width, 0], [width, depth], [0, depth], [0, 0]],
                        thickness,
                    ),
                },
            )
        )

    roof = expected_facts.get("roof")
    if isinstance(roof, Mapping):
        roof_elevation = float(roof.get("elevation_mm", len(storeys) * storey_height))
        roof_thickness = float(roof.get("thickness_mm", default_slab_thickness))
        entities.append(
            _entity(
                _generated_id("roof", roof, len(entities)),
                "IfcRoof",
                {
                    "Name": str(roof.get("source_key", "Roof")),
                    "ShapeType": "FLAT_ROOF",
                    "ObjectPlacement": _placement("building-1", [0, 0, roof_elevation]),
                    "Representation": _rectangle_representation(
                        width,
                        depth,
                        roof_thickness,
                    ),
                },
            )
        )

    for stair in _records(expected_facts.get("stairs")):
        storey_id = str(stair.get("storey") or storeys[0]["id"])
        entities.append(
            _entity(
                _generated_id("stair", stair, len(entities)),
                "IfcStair",
                {
                    "Name": str(stair.get("source_key", "Stair")),
                    "ShapeType": "STRAIGHT_RUN_STAIR",
                    "ObjectPlacement": _placement(
                        storey_id,
                        [wall_thickness, max(depth - 3500, wall_thickness), 0],
                    ),
                    "Representation": _rectangle_representation(
                        3500,
                        1200,
                        max(storey_height, float(stair.get("end_elevation_mm", 0)) - float(stair.get("start_elevation_mm", 0))),
                    ),
                },
            )
        )

    for collection, ifc_class in (("doors", "IfcDoor"), ("windows", "IfcWindow")):
        sequence = 0
        for record in _records(expected_facts.get(collection)):
            sequence += 1
            storey_id = _required_text(record, "storey")
            host_key = _required_text_alias(record, ("host_wall", "room", "name", "source_key"))
            host_id = _ensure_host_wall(
                entities=entities,
                host_walls=host_walls,
                storey_id=storey_id,
                host_key=host_key,
                width=width,
                depth=depth,
                wall_thickness=wall_thickness,
                storey_height=storey_height,
            )
            element_id = _generated_id(collection[:-1], record, sequence)
            opening_id = f"opening-{element_id}"
            element_width = _required_number(record, "width_mm")
            element_height = _required_number(record, "height_mm")
            sill = float(record.get("sill_height_mm", 0))
            entities.append(
                _entity(
                    opening_id,
                    "IfcOpeningElement",
                    {
                        "Name": f"Opening for {element_id}",
                        "ObjectPlacement": _placement(
                            host_id,
                            [wall_thickness, 0, sill],
                        ),
                        "Representation": _rectangle_representation(
                            element_width,
                            wall_thickness,
                            element_height,
                        ),
                    },
                )
            )
            entities.append(
                _entity(
                    element_id,
                    ifc_class,
                    {
                        "Name": element_id,
                        "OverallWidth": element_width,
                        "OverallHeight": element_height,
                        "ObjectPlacement": _placement(opening_id),
                        "Representation": _rectangle_representation(
                            element_width,
                            max(wall_thickness / 2, 50),
                            element_height,
                        ),
                    },
                )
            )
            relationships.extend(_opening_relationships(element_id, opening_id, host_id))

    return {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": entities,
        "relationships": relationships,
        "provenance": {
            **PROVENANCE,
            "case_id": case_id,
            "scaffold_role": "deterministic_candidate_from_explicit_design_brief_facts",
        },
    }


def _external_walls(
    *,
    storey_id: str,
    width: float,
    depth: float,
    wall_thickness: float,
    storey_height: float,
) -> list[dict[str, Any]]:
    return [
        _wall(
            f"{storey_id}-wall-south",
            storey_id,
            [0, 0, 0],
            width,
            wall_thickness,
            storey_height,
            [1, 0, 0],
        ),
        _wall(
            f"{storey_id}-wall-north",
            storey_id,
            [0, depth - wall_thickness, 0],
            width,
            wall_thickness,
            storey_height,
            [1, 0, 0],
        ),
        _wall(
            f"{storey_id}-wall-west",
            storey_id,
            [0, 0, 0],
            depth,
            wall_thickness,
            storey_height,
            [0, 1, 0],
        ),
        _wall(
            f"{storey_id}-wall-east",
            storey_id,
            [width - wall_thickness, 0, 0],
            depth,
            wall_thickness,
            storey_height,
            [0, 1, 0],
        ),
    ]


def _ensure_host_wall(
    *,
    entities: list[dict[str, Any]],
    host_walls: dict[tuple[str, str], str],
    storey_id: str,
    host_key: str,
    width: float,
    depth: float,
    wall_thickness: float,
    storey_height: float,
) -> str:
    key = (storey_id, host_key)
    existing = host_walls.get(key)
    if existing:
        return existing
    host_id = f"{storey_id}-wall-{_slug(host_key)}"
    axis = _host_axis(host_key)
    length = depth if axis == "y" else width
    origin = _host_origin(
        host_key,
        width=width,
        depth=depth,
        wall_thickness=wall_thickness,
    )
    ref_direction = [0, 1, 0] if axis == "y" else [1, 0, 0]
    entities.append(
        _wall(
            host_id,
            storey_id,
            origin,
            length,
            wall_thickness,
            storey_height,
            ref_direction,
        )
    )
    host_walls[key] = host_id
    return host_id


def _host_axis(host_key: str) -> str:
    return "y" if host_key.endswith("_east") or host_key.endswith("_west") else "x"


def _host_origin(
    host_key: str,
    *,
    width: float,
    depth: float,
    wall_thickness: float,
) -> list[float]:
    if host_key.endswith("_north"):
        return [0, depth - wall_thickness, 0]
    if host_key.endswith("_east"):
        return [width - wall_thickness, 0, 0]
    if host_key.endswith("_west"):
        return [0, 0, 0]
    if "_to_" in host_key:
        return [width / 2, depth / 2, 0]
    return [0, 0, 0]


def _space_origin(
    space: Mapping[str, Any],
    *,
    width: float,
    depth: float,
) -> list[float]:
    dimensions = _dimensions(space)
    space_width, space_depth = dimensions if dimensions is not None else (0, 0)
    location = str(space.get("location", "")).lower()
    if location == "southeast":
        return [max(width - space_width, 0), 0, 0]
    if location == "northeast":
        return [max(width - space_width, 0), max(depth - space_depth, 0), 0]
    if location == "northwest":
        return [0, max(depth - space_depth, 0), 0]
    return [0, 0, 0]


def _storey_for_elevation(
    storeys: list[Mapping[str, Any]],
    elevation: float,
) -> str:
    candidates = [
        (abs(float(storey.get("elevation_mm", 0)) - elevation), str(storey["id"]))
        for storey in storeys
    ]
    return min(candidates)[1]


def _storey_height_from_expected(expected_facts: Mapping[str, Any]) -> float:
    storeys = _records(expected_facts.get("storeys"))
    for storey in storeys:
        value = _number_alias(storey, ("height_mm", "height", "net_height"))
        if value is not None:
            return float(value)
    return 3000.0


def _dimensions(record: Mapping[str, Any]) -> tuple[float, float] | None:
    value = record.get("dimensions_mm")
    if (
        isinstance(value, list)
        and len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    ):
        return float(value[0]), float(value[1])
    width = _number_alias(record, ("width_mm", "width"))
    depth = _number_alias(record, ("depth_mm", "depth"))
    if width is not None and depth is not None:
        return float(width), float(depth)
    return None


def _wall(
    entity_id: str,
    relative_to: str,
    origin: list[float],
    length: float,
    thickness: float,
    height: float,
    ref_direction: list[float],
) -> dict[str, Any]:
    return _entity(
        entity_id,
        "IfcWall",
        {
            "Name": entity_id,
            "ObjectPlacement": _placement(relative_to, origin, ref_direction),
            "Representation": _rectangle_representation(length, thickness, height),
        },
    )


def _entity(entity_id: str, ifc_class: str, attributes: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entity_id,
        "ifc_class": ifc_class,
        "attributes": attributes,
        "property_sets": {},
        "provenance": dict(PROVENANCE),
    }


def _placement(
    relative_to: str,
    origin: list[float] | None = None,
    ref_direction: list[float] | None = None,
) -> dict[str, Any]:
    return {
        "relative_to": relative_to,
        "origin": origin or [0, 0, 0],
        "axis": [0, 0, 1],
        "ref_direction": ref_direction or [1, 0, 0],
    }


def _rectangle_representation(x: float, y: float, depth: float) -> dict[str, Any]:
    return {
        "kind": "extruded_profile",
        "profile": {"kind": "rectangle", "x": x, "y": y},
        "depth": depth,
        "direction": [0, 0, 1],
    }


def _polygon_representation(points: list[list[float]], depth: float) -> dict[str, Any]:
    return {
        "kind": "extruded_profile",
        "profile": {"kind": "polygon", "points": points},
        "depth": depth,
        "direction": [0, 0, 1],
    }


def _opening_relationships(
    element_id: str,
    opening_id: str,
    host_wall: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"void-{opening_id}",
            "ifc_class": "IfcRelVoidsElement",
            "attributes": {
                "RelatingBuildingElement": host_wall,
                "RelatedOpeningElement": opening_id,
            },
            "provenance": dict(PROVENANCE),
        },
        {
            "id": f"fill-{opening_id}",
            "ifc_class": "IfcRelFillsElement",
            "attributes": {
                "RelatingOpeningElement": opening_id,
                "RelatedBuildingElement": element_id,
            },
            "provenance": dict(PROVENANCE),
        },
    ]


def _generated_id(prefix: str, record: Mapping[str, Any], fallback_index: int) -> str:
    source_key = record.get("source_key")
    if isinstance(source_key, str) and source_key:
        return f"{prefix}-{_slug(source_key)}"
    explicit = record.get("id")
    if isinstance(explicit, str) and explicit:
        return explicit
    return f"{prefix}-{fallback_index}"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    if slug:
        return f"{slug}-{_short_hash(value)}" if slug != value.lower() else slug
    return _short_hash(value)


def _short_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]


def _records(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _required_number(record: Mapping[str, Any], key: str) -> float:
    value = record.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"scaffold requires numeric fact: {key}")
    return float(value)


def _required_number_alias(record: Mapping[str, Any], keys: tuple[str, ...]) -> float:
    value = _number_alias(record, keys)
    if value is None:
        raise ValueError(f"scaffold requires numeric fact: {'/'.join(keys)}")
    return float(value)


def _number_alias(record: Mapping[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = record.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    outer_dimensions = record.get("outer_dimensions_mm")
    if isinstance(outer_dimensions, Mapping):
        if any(key in keys for key in ("width_x_mm", "overall_width_x", "x_dim_mm", "length_mm")):
            value = outer_dimensions.get("x")
            if isinstance(value, (int, float)):
                return float(value)
        if any(key in keys for key in ("depth_y_mm", "overall_depth_y", "y_dim_mm", "depth_mm")):
            value = outer_dimensions.get("y")
            if isinstance(value, (int, float)):
                return float(value)
    return None


def _required_text(record: Mapping[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"scaffold requires text fact: {key}")
    return value


def _required_text_alias(record: Mapping[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    raise ValueError(f"scaffold requires text fact: {'/'.join(keys)}")
