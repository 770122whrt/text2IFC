"""Deterministic IFC -> description-oriented building facts.

The facts in this module are deliberately different from BIM JSON: they are a
read-only observation of an existing IFC.  Unsupported or unmeasurable facts are
recorded as issues instead of being synthesized.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit

from text2ifc_ifc_repair.geometry import opening_dimensions_mm, opening_position_in_wall_mm
from text2ifc_ifc_repair.index_adapters import WallIndexAdapter


FACTS_SCHEMA_VERSION = "text2ifc/ifc2text-facts/0.1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _name(entity: Any) -> str | None:
    value = getattr(entity, "Name", None)
    return None if value in (None, "") else str(value)


def _gid(entity: Any) -> str | None:
    value = getattr(entity, "GlobalId", None)
    return None if value in (None, "") else str(value)


def _round(value: float, digits: int = 3) -> float:
    result = round(float(value), digits)
    return 0.0 if result == -0.0 else result


def _vec(values: Any, digits: int = 3) -> list[float]:
    return [_round(value, digits) for value in values]


def _world_bounds_mm(entity: Any) -> dict[str, list[float]]:
    points = _world_vertices_mm(entity)
    axes = tuple([point[index] for point in points] for index in range(3))
    return {
        axis_name: [_round(min(axis)), _round(max(axis))]
        for axis_name, axis in zip(("x", "y", "z"), axes, strict=True)
    }


def _world_vertices_mm(entity: Any) -> list[list[float]]:
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    shape = ifcopenshell.geom.create_shape(settings, entity)
    geometry = getattr(shape, "geometry", shape)
    vertices = list(geometry.verts)
    if not vertices:
        raise ValueError("PRODUCT_GEOMETRY_EMPTY")
    return [
        [float(vertices[index + axis]) * 1000.0 for axis in range(3)]
        for index in range(0, len(vertices), 3)
    ]


def _mesh_wall_geometry(entity: Any) -> dict[str, Any]:
    """Measure a long vertical wall from its actual world-coordinate mesh."""
    points = _world_vertices_mm(entity)
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    cov_xx = sum((x - mean_x) ** 2 for x in xs) / len(xs)
    cov_yy = sum((y - mean_y) ** 2 for y in ys) / len(ys)
    cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / len(xs)
    angle = 0.5 * math.atan2(2.0 * cov_xy, cov_xx - cov_yy)
    direction = [math.cos(angle), math.sin(angle), 0.0]
    normal = [-direction[1], direction[0], 0.0]
    along = [point[0] * direction[0] + point[1] * direction[1] for point in points]
    across = [point[0] * normal[0] + point[1] * normal[1] for point in points]
    length = max(along) - min(along)
    thickness = max(across) - min(across)
    if length < thickness:
        direction, normal = normal, [-normal[1], normal[0], 0.0]
        along, across = across, along
        length, thickness = thickness, length
    if length <= 0.0 or thickness <= 0.0 or length / thickness < 1.25:
        raise ValueError("WALL_MESH_NOT_LONG_RECTILINEAR_ENOUGH")
    normal_mid = (min(across) + max(across)) / 2.0
    z_base = min(zs)

    def point_at(along_value: float) -> list[float]:
        return [
            along_value * direction[0] + normal_mid * normal[0],
            along_value * direction[1] + normal_mid * normal[1],
            z_base,
        ]

    return {
        "axis_start_mm": _vec(point_at(min(along))),
        "axis_end_mm": _vec(point_at(max(along))),
        "axis_direction": _vec(direction, 6),
        "length_mm": _round(length),
        "thickness_mm": _round(thickness),
        "height_mm": _round(max(zs) - min(zs)),
    }


def _centroid_from_bounds(bounds: dict[str, list[float]]) -> list[float]:
    return [
        _round((bounds[axis][0] + bounds[axis][1]) / 2.0)
        for axis in ("x", "y", "z")
    ]


def _direct_storey(entity: Any) -> Any | None:
    for relation in getattr(entity, "ContainedInStructure", ()) or ():
        structure = getattr(relation, "RelatingStructure", None)
        if structure is not None and structure.is_a("IfcBuildingStorey"):
            return structure
    if entity.is_a("IfcSpace"):
        for relation in getattr(entity, "Decomposes", ()) or ():
            parent = getattr(relation, "RelatingObject", None)
            if parent is not None and parent.is_a("IfcBuildingStorey"):
                return parent
    return None


def _storey_for(entity: Any) -> Any | None:
    direct = _direct_storey(entity)
    if direct is not None:
        return direct
    if entity.is_a("IfcOpeningElement"):
        for relation in getattr(entity, "VoidsElements", ()) or ():
            host = getattr(relation, "RelatingBuildingElement", None)
            if host is not None:
                result = _storey_for(host)
                if result is not None:
                    return result
    for fill in getattr(entity, "FillsVoids", ()) or ():
        opening = getattr(fill, "RelatingOpeningElement", None)
        if opening is not None:
            result = _storey_for(opening)
            if result is not None:
                return result
    return None


def _storey_elevation_mm(storey: Any, scale_mm: float) -> float | None:
    elevation = getattr(storey, "Elevation", None)
    if elevation is not None:
        return _round(float(elevation) * scale_mm)
    placement = getattr(storey, "ObjectPlacement", None)
    if placement is None:
        return None
    matrix = ifcopenshell.util.placement.get_local_placement(placement)
    return _round(float(matrix[2, 3]) * scale_mm)


def _wall_fact(entity: Any, label: str, storey_label: str | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fact: dict[str, Any] = {
        "label": label,
        "source_global_id": _gid(entity),
        "name": _name(entity),
        "ifc_class": entity.is_a(),
        "storey": storey_label,
        "spaces": [],
        "openings": [],
        "measurement_status": "partial",
    }
    issues: list[dict[str, Any]] = []
    try:
        result = WallIndexAdapter().extract(entity)
        summary = result.geometry_summary
        basis = summary.get("coordinate_basis", {})
        dimensions = summary.get("dimensions_mm", {})
        if basis.get("world_axis_start_mm") and basis.get("world_axis_direction") and dimensions.get("length") is not None:
            start = list(basis["world_axis_start_mm"])
            direction = list(basis["world_axis_direction"])
            length = float(dimensions["length"])
            end = [start[index] + direction[index] * length for index in range(3)]
            fact.update(
                {
                    "axis_start_mm": _vec(start),
                    "axis_end_mm": _vec(end),
                    "axis_direction": _vec(direction, 6),
                    "length_mm": _round(length),
                    "thickness_mm": _round(dimensions["thickness"]),
                    "height_mm": _round(dimensions["height"]),
                    "orientation": summary.get("orientation"),
                    "measurement_method": "explicit_ifc_axis_plus_geometry",
                    "measurement_status": "measured",
                }
            )
        for relationship in result.relationships:
            if relationship.kind == "bounds_space":
                fact.setdefault("space_global_ids", []).append(relationship.target_global_id)
            elif relationship.kind == "voids_opening":
                fact.setdefault("opening_global_ids", []).append(relationship.target_global_id)
        for code, message, evidence in result.warnings:
            issues.append({"code": code, "message": message, "entity": label, "evidence": evidence})
    except Exception as error:
        issues.append({"code": "WALL_MEASUREMENT_FAILED", "message": str(error), "entity": label})
    if fact["measurement_status"] != "measured":
        try:
            fact.update(_mesh_wall_geometry(entity))
            fact["measurement_method"] = "world_mesh_principal_axis"
            fact["measurement_status"] = "measured"
        except Exception as error:
            issues.append({"code": "WALL_MESH_AXIS_FAILED", "message": str(error), "entity": label})
    try:
        bounds = _world_bounds_mm(entity)
        fact["bounds_mm"] = bounds
        fact["centroid_mm"] = _centroid_from_bounds(bounds)
    except Exception as error:
        issues.append({"code": "WALL_WORLD_GEOMETRY_FAILED", "message": str(error), "entity": label})
    return fact, issues


def _opening_fact(entity: Any, label: str, storey_label: str | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fact: dict[str, Any] = {
        "label": label,
        "source_global_id": _gid(entity),
        "name": _name(entity),
        "ifc_class": entity.is_a(),
        "storey": storey_label,
        "measurement_status": "partial",
    }
    issues: list[dict[str, Any]] = []
    voids = list(getattr(entity, "VoidsElements", ()) or ())
    fills = list(getattr(entity, "HasFillings", ()) or ())
    host = voids[0].RelatingBuildingElement if len(voids) == 1 else None
    filling = fills[0].RelatedBuildingElement if len(fills) == 1 else None
    fact["host_global_id"] = _gid(host) if host is not None else None
    fact["filling_global_id"] = _gid(filling) if filling is not None else None
    try:
        dimensions = opening_dimensions_mm(entity)
        fact["dimensions_mm"] = {key: _round(value) for key, value in dimensions.items()}
        if host is not None:
            position = opening_position_in_wall_mm(entity, host)
            fact["host_position_mm"] = {
                "center_offset_mm": _round(position["center_offset"]),
                "normal_offset_mm": _round(position["normal_offset"]),
                "sill_height_mm": _round(position["sill_height"]),
            }
        fact["measurement_status"] = "measured"
    except Exception as error:
        issues.append({"code": "OPENING_MEASUREMENT_FAILED", "message": str(error), "entity": label})
    try:
        bounds = _world_bounds_mm(entity)
        fact["bounds_mm"] = bounds
        fact["centroid_mm"] = _centroid_from_bounds(bounds)
    except Exception as error:
        issues.append({"code": "OPENING_WORLD_GEOMETRY_FAILED", "message": str(error), "entity": label})
    return fact, issues


def _filling_fact(entity: Any, label: str, storey_label: str | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scale_mm = ifcopenshell.util.unit.calculate_unit_scale(entity.file) * 1000.0
    fact: dict[str, Any] = {
        "label": label,
        "source_global_id": _gid(entity),
        "name": _name(entity),
        "ifc_class": entity.is_a(),
        "storey": storey_label,
        "overall_width_mm": None if getattr(entity, "OverallWidth", None) is None else _round(float(entity.OverallWidth) * scale_mm),
        "overall_height_mm": None if getattr(entity, "OverallHeight", None) is None else _round(float(entity.OverallHeight) * scale_mm),
        "measurement_status": "partial",
    }
    issues: list[dict[str, Any]] = []
    fills = list(getattr(entity, "FillsVoids", ()) or ())
    opening = fills[0].RelatingOpeningElement if len(fills) == 1 else None
    host = None
    if opening is not None:
        voids = list(getattr(opening, "VoidsElements", ()) or ())
        host = voids[0].RelatingBuildingElement if len(voids) == 1 else None
    fact["opening_global_id"] = _gid(opening) if opening is not None else None
    fact["host_global_id"] = _gid(host) if host is not None else None
    if opening is not None and host is not None:
        try:
            position = opening_position_in_wall_mm(opening, host)
            fact["host_position_mm"] = {
                "center_offset_mm": _round(position["center_offset"]),
                "normal_offset_mm": _round(position["normal_offset"]),
                "sill_height_mm": _round(position["sill_height"]),
            }
        except Exception as error:
            issues.append({"code": "FILLING_HOST_POSITION_FAILED", "message": str(error), "entity": label})
    try:
        bounds = _world_bounds_mm(entity)
        fact["bounds_mm"] = bounds
        fact["centroid_mm"] = _centroid_from_bounds(bounds)
        fact["geometry_size_mm"] = {
            axis: _round(bounds[axis][1] - bounds[axis][0]) for axis in ("x", "y", "z")
        }
        fact["measurement_status"] = "measured"
    except Exception as error:
        issues.append({"code": "FILLING_WORLD_GEOMETRY_FAILED", "message": str(error), "entity": label})
    return fact, issues


def _space_fact(entity: Any, label: str, storey_label: str | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fact: dict[str, Any] = {
        "label": label,
        "source_global_id": _gid(entity),
        "name": _name(entity),
        "long_name": None if getattr(entity, "LongName", None) in (None, "") else str(entity.LongName),
        "storey": storey_label,
        "source_kind": "ifc_space",
        "boundary_wall_global_ids": [],
    }
    issues: list[dict[str, Any]] = []
    for boundary in getattr(entity, "BoundedBy", ()) or ():
        element = getattr(boundary, "RelatedBuildingElement", None)
        if element is not None and element.is_a("IfcWall") and _gid(element):
            fact["boundary_wall_global_ids"].append(_gid(element))
    fact["boundary_wall_global_ids"] = sorted(set(fact["boundary_wall_global_ids"]))
    try:
        bounds = _world_bounds_mm(entity)
        fact["bounds_mm"] = bounds
        fact["centroid_mm"] = _centroid_from_bounds(bounds)
        fact["size_mm"] = {
            axis: _round(bounds[axis][1] - bounds[axis][0]) for axis in ("x", "y", "z")
        }
    except Exception as error:
        issues.append({"code": "SPACE_GEOMETRY_FAILED", "message": str(error), "entity": label})
    return fact, issues


def _infer_enclosed_regions(storey: dict[str, Any], *, snap_tolerance_mm: float = 20.0, min_area_m2: float = 1.0) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Polygonize straight wall centrelines as a conservative no-IfcSpace baseline.

    These are geometric enclosed regions, not semantic rooms.  A wall opening in
    normal IFC authoring does not cut the wall Axis, so no artificial wall is
    introduced merely to close a door gap.
    """
    walls = [wall for wall in storey["walls"] if wall.get("axis_start_mm") and wall.get("axis_end_mm")]
    if len(walls) < 3:
        return [], [{"code": "SPACE_INFERENCE_INSUFFICIENT_WALLS", "storey": storey["label"]}]
    try:
        from shapely import set_precision
        from shapely.geometry import LineString
        from shapely.ops import polygonize, unary_union
    except Exception as error:
        return [], [{"code": "SPACE_INFERENCE_TOOL_UNAVAILABLE", "storey": storey["label"], "message": str(error)}]
    lines = []
    for wall in walls:
        start = wall["axis_start_mm"]
        end = wall["axis_end_mm"]
        dx = float(end[0]) - float(start[0])
        dy = float(end[1]) - float(start[1])
        length = math.hypot(dx, dy)
        if length <= 0.0:
            continue
        ux, uy = dx / length, dy / length
        # BIM wall axes often stop at the face of a perpendicular wall rather
        # than meeting its centreline. Extend only by half the measured wall
        # thickness plus the explicit snap tolerance so normal corner joints can
        # be noded without inventing long missing boundaries.
        thickness = float(wall.get("thickness_mm") or 0.0)
        extension = max(float(snap_tolerance_mm), thickness / 2.0 + float(snap_tolerance_mm))
        lines.append(
            LineString(
                [
                    (float(start[0]) - ux * extension, float(start[1]) - uy * extension),
                    (float(end[0]) + ux * extension, float(end[1]) + uy * extension),
                ]
            )
        )
    if len(lines) < 3:
        return [], [{"code": "SPACE_INFERENCE_INSUFFICIENT_MEASURABLE_WALLS", "storey": storey["label"]}]
    try:
        network = set_precision(unary_union(lines), grid_size=float(snap_tolerance_mm), mode="valid_output")
        polygons = [polygon for polygon in polygonize(network) if polygon.area >= min_area_m2 * 1_000_000.0]
    except Exception as error:
        return [], [{"code": "SPACE_INFERENCE_FAILED", "storey": storey["label"], "message": str(error)}]
    regions: list[dict[str, Any]] = []
    for index, polygon in enumerate(sorted(polygons, key=lambda item: (item.centroid.y, item.centroid.x, item.area)), 1):
        coords = [[_round(x), _round(y)] for x, y in polygon.exterior.coords]
        regions.append(
            {
                "label": f"G{index:02d}",
                "source_kind": "derived_enclosed_region",
                "name": None,
                "area_m2": _round(polygon.area / 1_000_000.0, 4),
                "centroid_xy_mm": [_round(polygon.centroid.x), _round(polygon.centroid.y)],
                "outline_xy_mm": coords,
                "method": "straight_wall_axis_endpoint_extension_polygonize",
                "semantic_use": "unknown",
            }
        )
    if not regions:
        return [], [{"code": "SPACE_INFERENCE_NO_CLOSED_REGION", "storey": storey["label"]}]
    return regions, []


def extract_building_facts(path: str | Path, *, infer_spaces: bool = True) -> dict[str, Any]:
    """Extract a description-oriented, loss-reporting fact representation."""
    source = Path(path).resolve()
    model = ifcopenshell.open(str(source))
    scale_mm = ifcopenshell.util.unit.calculate_unit_scale(model) * 1000.0
    storey_entities = sorted(
        model.by_type("IfcBuildingStorey"),
        key=lambda entity: (_storey_elevation_mm(entity, scale_mm) is None, _storey_elevation_mm(entity, scale_mm) or 0.0, entity.id()),
    )
    storey_label_by_step = {storey.id(): f"S{index:02d}" for index, storey in enumerate(storey_entities, 1)}
    storey_label_by_gid = {_gid(storey): storey_label_by_step[storey.id()] for storey in storey_entities if _gid(storey)}
    storeys = [
        {
            "label": storey_label_by_step[storey.id()],
            "source_global_id": _gid(storey),
            "name": _name(storey),
            "elevation_mm": _storey_elevation_mm(storey, scale_mm),
            "walls": [],
            "openings": [],
            "doors": [],
            "windows": [],
            "spaces": [],
            "derived_spaces": [],
            "stairs": [],
        }
        for storey in storey_entities
    ]
    by_storey = {item["label"]: item for item in storeys}
    unassigned = {"walls": [], "openings": [], "doors": [], "windows": [], "spaces": [], "stairs": []}
    issues: list[dict[str, Any]] = []

    def target_for(entity: Any) -> tuple[str | None, dict[str, Any] | None]:
        storey = _storey_for(entity)
        label = storey_label_by_step.get(storey.id()) if storey is not None else None
        return label, by_storey.get(label) if label is not None else None

    categories = (
        ("walls", "IfcWall", "W", _wall_fact),
        ("openings", "IfcOpeningElement", "O", _opening_fact),
        ("doors", "IfcDoor", "D", _filling_fact),
        ("windows", "IfcWindow", "N", _filling_fact),
        ("spaces", "IfcSpace", "R", _space_fact),
    )
    facts_by_gid: dict[str, dict[str, Any]] = {}
    for category, ifc_class, prefix, builder in categories:
        entities = sorted(model.by_type(ifc_class), key=lambda entity: entity.id())
        for index, entity in enumerate(entities, 1):
            storey_label, target = target_for(entity)
            fact, item_issues = builder(entity, f"{prefix}{index:03d}", storey_label)
            (target[category] if target is not None else unassigned[category]).append(fact)
            issues.extend(item_issues)
            if _gid(entity):
                facts_by_gid[_gid(entity)] = fact

    for index, stair in enumerate(sorted(model.by_type("IfcStair"), key=lambda entity: entity.id()), 1):
        storey_label, target = target_for(stair)
        fact: dict[str, Any] = {
            "label": f"T{index:03d}",
            "source_global_id": _gid(stair),
            "name": _name(stair),
            "storey": storey_label,
            "geometry_source": None,
            "component_classes": [],
        }
        bounds = None
        try:
            bounds = _world_bounds_mm(stair)
            fact["geometry_source"] = "ifc_stair_representation"
        except Exception:
            child_bounds: list[dict[str, list[float]]] = []
            component_classes: list[str] = []
            for relation in getattr(stair, "IsDecomposedBy", ()) or ():
                for child in getattr(relation, "RelatedObjects", ()) or ():
                    component_classes.append(child.is_a())
                    try:
                        child_bounds.append(_world_bounds_mm(child))
                    except Exception:
                        continue
            fact["component_classes"] = sorted(component_classes)
            if child_bounds:
                bounds = {
                    axis: [
                        min(item[axis][0] for item in child_bounds),
                        max(item[axis][1] for item in child_bounds),
                    ]
                    for axis in ("x", "y", "z")
                }
                fact["geometry_source"] = "decomposed_stair_components"
        if bounds is not None:
            fact["bounds_mm"] = bounds
            fact["centroid_mm"] = _centroid_from_bounds(bounds)
            z_min, z_max = bounds["z"]
            fact["spans_storeys_by_geometry"] = [
                candidate["label"]
                for candidate in storeys
                if candidate.get("elevation_mm") is not None
                and z_min - 100.0 <= float(candidate["elevation_mm"]) <= z_max + 100.0
            ]
        else:
            issues.append({"code": "STAIR_GEOMETRY_FAILED", "message": "No measurable stair or decomposed component geometry", "entity": fact["label"]})
        (target["stairs"] if target is not None else unassigned["stairs"]).append(fact)

    # Replace IFC identities in relationships with local readable labels while
    # preserving identities in the machine facts for traceability.
    for storey in storeys:
        for wall in storey["walls"]:
            wall["spaces"] = [facts_by_gid[gid]["label"] for gid in wall.pop("space_global_ids", []) if gid in facts_by_gid]
            wall["openings"] = [facts_by_gid[gid]["label"] for gid in wall.pop("opening_global_ids", []) if gid in facts_by_gid]
        for item in storey["openings"] + storey["doors"] + storey["windows"]:
            host_gid = item.get("host_global_id")
            opening_gid = item.get("opening_global_id")
            filling_gid = item.get("filling_global_id")
            item["host_wall"] = facts_by_gid.get(host_gid, {}).get("label")
            if "opening_global_id" in item:
                item["opening"] = facts_by_gid.get(opening_gid, {}).get("label")
            if "filling_global_id" in item:
                item["filling"] = facts_by_gid.get(filling_gid, {}).get("label")
        for space in storey["spaces"]:
            space["boundary_walls"] = [facts_by_gid[gid]["label"] for gid in space.pop("boundary_wall_global_ids", []) if gid in facts_by_gid]
        if infer_spaces and not storey["spaces"]:
            regions, inference_issues = _infer_enclosed_regions(storey)
            storey["derived_spaces"] = regions
            issues.extend(inference_issues)

    projects = model.by_type("IfcProject")
    buildings = model.by_type("IfcBuilding")
    return {
        "schema_version": FACTS_SCHEMA_VERSION,
        "source": {
            "path": str(source),
            "sha256": _sha256(source),
            "ifc_schema": str(model.schema),
            "size_bytes": source.stat().st_size,
        },
        "units": {"length": "millimetre", "area": "square_metre"},
        "coordinate_system": {
            "frame": "ifc_world",
            "axis_convention": "source IFC placement; no inferred north",
        },
        "building": {
            "project_name": _name(projects[0]) if projects else None,
            "building_name": _name(buildings[0]) if buildings else None,
            "storey_count": len(storeys),
        },
        "storeys": storeys,
        "unassigned": unassigned,
        "issues": issues,
        "capability": {
            "explicit_space_count": sum(len(storey["spaces"]) for storey in storeys),
            "derived_space_count": sum(len(storey["derived_spaces"]) for storey in storeys),
            "wall_count": sum(len(storey["walls"]) for storey in storeys) + len(unassigned["walls"]),
            "door_count": sum(len(storey["doors"]) for storey in storeys) + len(unassigned["doors"]),
            "window_count": sum(len(storey["windows"]) for storey in storeys) + len(unassigned["windows"]),
            "opening_count": sum(len(storey["openings"]) for storey in storeys) + len(unassigned["openings"]),
            "measurement_issue_count": len(issues),
        },
    }
