"""Deterministic Door-to-Opening placement and geometric L1 evidence."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Mapping

import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from .geometry import (
    product_geometry_bounds_in_host_mm,
    product_local_geometry_bounds_mm,
    wall_dimensions_mm,
)


MIN_PROJECTED_OVERLAP_RATIO = 0.95
MAX_CENTER_DEVIATION_MM = 5.0
MAX_AXIS_DEVIATION_DEGREES = 0.1
MAX_DIMENSION_DEVIATION_MM = 1.0


def public_door_installation_anchor(
    reference: Any, *, allow_wall_face_adaptation: bool = False,
) -> dict[str, Any]:
    """Derive an installation witness from one surviving public occurrence.

    This internal canonical parameter is not a model-authored intent field.
    Its caller must authorize the exact offered occurrence; geometry alone
    cannot authorize selecting a different occurrence of the same type.
    """
    if not reference.is_a("IfcDoor") or len(reference.FillsVoids) != 1:
        raise ValueError("DOOR_INSTALLATION_REFERENCE_FILL_AMBIGUOUS")
    opening = reference.FillsVoids[0].RelatingOpeningElement
    wall = _unique_installation_host(opening)
    if len(opening.HasFillings) != 1:
        raise ValueError("DOOR_INSTALLATION_REFERENCE_FILL_AMBIGUOUS")
    types = [r.RelatingType for r in reference.IsDefinedBy
             if r.is_a("IfcRelDefinesByType")]
    if len(types) != 1 or not types[0].is_a("IfcDoorStyle"):
        raise ValueError("DOOR_INSTALLATION_REFERENCE_TYPE_AMBIGUOUS")
    relative = _relative_placement(reference, opening)
    if _axis_deviation_degrees(relative) > MAX_AXIS_DEVIATION_DEGREES:
        raise ValueError("DOOR_INSTALLATION_REFERENCE_AXIS_UNSUPPORTED")
    bounds = product_geometry_bounds_in_host_mm(reference, opening)
    opening_bounds = product_geometry_bounds_in_host_mm(opening, opening)
    offset = _center(bounds["y"]) - _center(opening_bounds["y"])
    # The nominal base must align with its opening. A Type map may have a
    # different mesh origin (e.g. a frame above the unfinished floor datum).
    # Preserve that signed public mesh offset, rather than moving the instance.
    diagnostics = measure_door_opening_alignment(reference, opening)
    nominal_base_deviation = abs(diagnostics["nominal_door_bounds_mm"]["z"][0] - opening_bounds["z"][0])
    if (diagnostics["projected_overlap_ratio"] < MIN_PROJECTED_OVERLAP_RATIO
            or diagnostics["normal_axis_intersection_mm"] <= 0
            or diagnostics["geometry_center_deviation_by_axis_mm"]["x"] > MAX_CENTER_DEVIATION_MM
            or nominal_base_deviation > MAX_CENTER_DEVIATION_MM
            or diagnostics["width_deviation_mm"] > MAX_DIMENSION_DEVIATION_MM
            or diagnostics["height_deviation_mm"] > MAX_DIMENSION_DEVIATION_MM):
        raise ValueError("DOOR_INSTALLATION_REFERENCE_ALIGNMENT_UNSUPPORTED")
    anchor = {
        "method": "public-door-opening-installation/0.2",
        "reference_global_id": str(reference.GlobalId),
        "reference_opening_global_id": str(opening.GlobalId),
        "reference_wall_global_id": str(wall.GlobalId),
        "type_global_id": str(types[0].GlobalId),
        "width_mm": round(_millimetres(reference, float(reference.OverallWidth)), 6),
        "height_mm": round(_millimetres(reference, float(reference.OverallHeight)), 6),
        "opening_depth_mm": round(_extent(opening_bounds["y"]), 6),
        "wall_thickness_mm": round(float(wall_dimensions_mm(wall)["thickness"]), 6),
        "opening_normal_offset_from_wall_mm": round(_opening_normal_offset_in_wall(opening, wall), 6),
        "normal_center_offset_mm": round(offset, 6),
        "base_offset_from_opening_mm": round(float(bounds["z"][0]) - float(opening_bounds["z"][0]), 6),
        "axis_sign": 1.0 if relative[0, 0] > 0 else -1.0,
    }
    if types[0].RepresentationMaps:
        anchor["mapped_body"] = _mapped_body_signature(reference, types[0])
        if allow_wall_face_adaptation:
            raise ValueError("DOOR_INSTALLATION_THICKNESS_ADAPTATION_UNSUPPORTED")
    else:
        anchor["method"] = "public-door-occurrence-installation/0.1"
        anchor["direct_body"] = _direct_body_reference(reference)
        if allow_wall_face_adaptation:
            anchor["wall_face_adaptation_authorized"] = True
            anchor["wall_face"] = _public_frame_wall_face(reference, opening, wall)
    return anchor


def public_wall_face_adaptation_requested(text: str) -> bool:
    """Recognize explicit installation permission in actual public request text.

    This deliberately bounded internal permission is never read from a model
    parameter or provenance excerpt. Unclear or negated language cannot unlock
    cross-thickness installation; exact reuse remains available without it.
    """
    text = text.casefold()
    if (re.search(r"(?:do\s+not|don't|never|without|\bnot\b)[^.!?;]{0,120}\badapt", text)
            or re.search(r"(?:不|勿|禁止)[^。；;]{0,12}适配", text)):
        return False
    return (all(word in text for word in ("墙面", "适配", "墙厚"))
            or bool(re.search(r"wall[\s-]+face", text) and "adapt" in text
                    and re.search(r"wall[\s-]+thickness", text)))


def supports_direct_door_body(reference: Any) -> bool:
    bodies = _bodies(reference)
    return (len(bodies) == 1 and bool(bodies[0].Items)
            and all(item.is_a("IfcFacetedBrep") for item in bodies[0].Items))


def has_direct_door_brep(reference: Any) -> bool:
    """A partly unsupported Brep Body must not silently become a cuboid."""
    return any(item.is_a("IfcFacetedBrep") for body in _bodies(reference) for item in body.Items)


def _bodies(product: Any) -> list[Any]:
    return [r for r in product.Representation.Representations
            if r.RepresentationIdentifier == "Body"] if product.Representation else []


def _direct_body_reference(reference: Any) -> dict[str, Any]:
    if not supports_direct_door_body(reference):
        raise ValueError("DOOR_INSTALLATION_DIRECT_BODY_UNSUPPORTED")
    body = _bodies(reference)[0]
    graph = {entity.id(): entity.to_string() for entity in reference.file.traverse(body)}
    for item in body.Items:
        for styled in item.StyledByItem:
            graph.update((entity.id(), entity.to_string()) for entity in reference.file.traverse(styled))
    return {"representation_id": body.id(), "item_ids": [item.id() for item in body.Items],
            "geometry_and_styles_sha256": hashlib.sha256(
                "\n".join(graph[key] for key in sorted(graph)).encode("utf8")).hexdigest()}


def reuse_public_door_body(model: Any, reference: Any) -> list[Any]:
    """Map the exact public Body, preserving its per-item geometry and styles.

    A separate representation wrapper owns the new map; its Items share the
    exact source geometry and styles. IFC2X3 forbids the original Body being
    owned simultaneously by a product definition and a representation map.
    The reference and its mapless Type stay unchanged.
    """
    _direct_body_reference(reference)
    body = _bodies(reference)[0]
    mapped_body = model.createIfcShapeRepresentation(
        body.ContextOfItems, body.RepresentationIdentifier, body.RepresentationType, body.Items)
    origin = model.createIfcCartesianPoint((0., 0., 0.))
    source = model.createIfcRepresentationMap(model.createIfcAxis2Placement3D(origin), mapped_body)
    transform = model.createIfcCartesianTransformationOperator3D(None, None, origin, 1., None)
    item = model.createIfcMappedItem(source, transform)
    return [model.createIfcShapeRepresentation(body.ContextOfItems, "Body", "MappedRepresentation", [item])]


def _verify_direct_body(door: Any, reference: Any) -> None:
    bodies = _bodies(door)
    source = _bodies(reference)[0]
    if len(bodies) != 1 or len(bodies[0].Items) != 1:
        raise ValueError("DOOR_INSTALLATION_BODY_MISMATCH")
    item = bodies[0].Items[0]
    if not item.is_a("IfcMappedItem"):
        raise ValueError("DOOR_INSTALLATION_BODY_MISMATCH")
    mapped = item.MappingSource.MappedRepresentation
    if (mapped == source or mapped.ContextOfItems != source.ContextOfItems
            or mapped.RepresentationIdentifier != source.RepresentationIdentifier
            or mapped.RepresentationType != source.RepresentationType
            or mapped.Items != source.Items or mapped.OfProductRepresentation
            or len(mapped.RepresentationMap) != 1
            or not np.allclose(ifcopenshell.util.placement.get_mappeditem_transformation(item),
                               np.eye(4), rtol=0., atol=1e-9)):
        raise ValueError("DOOR_INSTALLATION_BODY_MISMATCH")


def _public_frame_wall_face(reference: Any, opening: Any, wall: Any) -> dict[str, Any]:
    """Identify a wall face from one full nominal-size frame Brep, not hardware."""
    settings = ifcopenshell.geom.settings()
    width = _millimetres(reference, float(reference.OverallWidth))
    height = _millimetres(reference, float(reference.OverallHeight))
    frames = []
    relative = _relative_placement(reference, opening)
    for item in _bodies(reference)[0].Items:
        shape = ifcopenshell.geom.create_shape(settings, item)
        vertices = np.asarray(shape.verts, dtype=float).reshape(-1, 3) * 1000.
        if not len(vertices) or not np.isfinite(vertices).all():
            raise ValueError("DOOR_INSTALLATION_FRAME_GEOMETRY_INVALID")
        extents = np.ptp(vertices, axis=0)
        if abs(extents[0] - width) <= MAX_DIMENSION_DEVIATION_MM and abs(extents[2] - height) <= MAX_DIMENSION_DEVIATION_MM:
            points = vertices @ relative[:3, :3].T + relative[:3, 3] * _millimetres_per_project_unit(reference)
            frames.append((item.id(), [float(points[:, 1].min()), float(points[:, 1].max())]))
    if len(frames) != 1:
        raise ValueError("DOOR_INSTALLATION_FRAME_WITNESS_AMBIGUOUS")
    wall_y = product_geometry_bounds_in_host_mm(wall, opening)["y"]
    item_id, frame_y = frames[0]
    matches = [index for index, face in enumerate(wall_y)
               if min(abs(face - edge) for edge in frame_y) <= MAX_DIMENSION_DEVIATION_MM]
    if len(matches) != 1:
        raise ValueError("DOOR_INSTALLATION_WALL_FACE_AMBIGUOUS")
    face = float(wall_y[matches[0]])
    body_y = product_geometry_bounds_in_host_mm(reference, opening)["y"]
    return {"frame_item_id": item_id, "side": -1 if matches[0] == 0 else 1,
            "body_center_offset_mm": round(_center(body_y) - face, 6),
            "frame_bounds_from_face_mm": [round(value - face, 6) for value in frame_y]}


def _unique_installation_host(opening: Any) -> Any:
    if len(opening.VoidsElements) != 1:
        raise ValueError("DOOR_INSTALLATION_HOST_AMBIGUOUS")
    wall = opening.VoidsElements[0].RelatingBuildingElement
    if not wall.is_a("IfcWall"):
        raise ValueError("DOOR_INSTALLATION_HOST_UNSUPPORTED")
    if _axis_deviation_degrees(_relative_placement(opening, wall)) > MAX_AXIS_DEVIATION_DEGREES:
        raise ValueError("DOOR_INSTALLATION_OPENING_AXIS_UNSUPPORTED")
    return wall


def _mapped_body_signature(product: Any, style: Any) -> list[dict[str, Any]]:
    """Require the same maps and occurrence mapping conventions, not AABB fit."""
    maps = list(style.RepresentationMaps or ())
    body = [r for r in product.Representation.Representations
            if r.RepresentationIdentifier == "Body"] if product.Representation else []
    if not maps or not body:
        raise ValueError("DOOR_INSTALLATION_MAPPED_BODY_REQUIRED")
    signature = []
    for representation in body:
        for item in representation.Items:
            if not item.is_a("IfcMappedItem") or item.MappingSource not in maps:
                raise ValueError("DOOR_INSTALLATION_MAPPED_BODY_UNSUPPORTED")
            matrix = ifcopenshell.util.placement.get_mappeditem_transformation(item)
            signature.append({"map_index": maps.index(item.MappingSource),
                              "transform": [round(float(v), 9) for v in matrix.flat]})
    return sorted(signature, key=lambda item: (item["map_index"], item["transform"]))


def validate_door_installation_target(opening: Any, anchor: Mapping[str, Any]) -> None:
    """Validate exact installation or the explicitly authorized frame face."""
    wall = _unique_installation_host(opening)
    depth = _extent(product_geometry_bounds_in_host_mm(opening, opening)["y"])
    if anchor.get("wall_face_adaptation_authorized"):
        thickness = float(wall_dimensions_mm(wall)["thickness"])
        wall_y = product_geometry_bounds_in_host_mm(wall, opening)["y"]
        face = float(wall_y[0 if anchor["wall_face"]["side"] < 0 else 1])
        frame_y = [face + value for value in anchor["wall_face"]["frame_bounds_from_face_mm"]]
        if (not anchor.get("direct_body") or abs(depth - thickness) > MAX_DIMENSION_DEVIATION_MM
                or abs(_opening_normal_offset_in_wall(opening, wall)) > MAX_DIMENSION_DEVIATION_MM
                or frame_y[0] < wall_y[0] - MAX_DIMENSION_DEVIATION_MM
                or frame_y[1] > wall_y[1] + MAX_DIMENSION_DEVIATION_MM):
            raise ValueError("DOOR_INSTALLATION_WALL_FACE_ADAPTATION_UNSUPPORTED")
        return
    if (abs(depth - float(anchor["opening_depth_mm"])) > MAX_DIMENSION_DEVIATION_MM
            or abs(float(wall_dimensions_mm(wall)["thickness"]) - float(anchor["wall_thickness_mm"])) > MAX_DIMENSION_DEVIATION_MM):
        raise ValueError("DOOR_INSTALLATION_THICKNESS_ADAPTATION_UNSUPPORTED")
    if abs(_opening_normal_offset_in_wall(opening, wall)
           - float(anchor["opening_normal_offset_from_wall_mm"])) > MAX_DIMENSION_DEVIATION_MM:
        raise ValueError("DOOR_INSTALLATION_OPENING_DEPTH_ORIGIN_UNSUPPORTED")


def _opening_normal_offset_in_wall(opening: Any, wall: Any) -> float:
    return (_center(product_geometry_bounds_in_host_mm(opening, wall)["y"])
            - _center(product_geometry_bounds_in_host_mm(wall, wall)["y"]))


def _verified_installation_anchor(door: Any, opening: Any,
                                  anchor: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        reference = door.file.by_guid(str(anchor["reference_global_id"]))
        measured = public_door_installation_anchor(reference,
            allow_wall_face_adaptation=anchor.get("wall_face_adaptation_authorized") is True)
        if dict(anchor) != measured:
            raise ValueError("DOOR_INSTALLATION_ANCHOR_MISMATCH")
        validate_door_installation_target(opening, measured)
        style = door.file.by_guid(str(measured["type_global_id"]))
        if measured.get("direct_body"):
            _verify_direct_body(door, reference)
        elif _mapped_body_signature(door, style) != measured["mapped_body"]:
            raise ValueError("DOOR_INSTALLATION_MAPPING_MISMATCH")
        if any(abs(_millimetres(door, float(getattr(door, attr))) - measured[key])
               > MAX_DIMENSION_DEVIATION_MM
               for attr, key in (("OverallWidth", "width_mm"), ("OverallHeight", "height_mm"))):
            raise ValueError("DOOR_INSTALLATION_DIMENSIONS_MISMATCH")
        return measured
    except (KeyError, RuntimeError, TypeError, AttributeError) as error:
        raise ValueError("DOOR_INSTALLATION_ANCHOR_UNAVAILABLE") from error


def _expected_normal_offset(opening: Any, anchor: Mapping[str, Any] | None) -> float:
    if anchor is None:
        return 0.0
    if anchor.get("wall_face_adaptation_authorized"):
        wall = _unique_installation_host(opening)
        wall_y = product_geometry_bounds_in_host_mm(wall, opening)["y"]
        face = float(wall_y[0 if anchor["wall_face"]["side"] < 0 else 1])
        opening_y = product_geometry_bounds_in_host_mm(opening, opening)["y"]
        return face + float(anchor["wall_face"]["body_center_offset_mm"]) - _center(opening_y)
    return float(anchor["normal_center_offset_mm"])


def select_door_placement_in_opening(
    door: Any,
    opening: Any,
    *, installation_anchor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Choose the canonical 0/180-degree placement that best fills Opening.

    Reused IFC2X3 DoorStyle maps do not share one geometry-origin convention.
    The choice is therefore derived from the surviving Opening and the mapped
    Door representation, never from a deleted occurrence or benchmark model.
    """

    opening_bounds = product_geometry_bounds_in_host_mm(opening, opening)
    local_bounds = product_local_geometry_bounds_mm(door)
    opening_center_y = _center(opening_bounds["y"])
    width_mm = _millimetres(door, float(door.OverallWidth))
    height_mm = _millimetres(door, float(door.OverallHeight))
    anchor = (_verified_installation_anchor(door, opening, installation_anchor)
              if installation_anchor is not None else None)
    expected_normal_offset = _expected_normal_offset(opening, anchor)
    expected_base_offset = float(anchor["base_offset_from_opening_mm"]) if anchor else 0.0
    candidates = []
    for sign in ((float(anchor["axis_sign"]),) if anchor else (1.0, -1.0)):
        rotated_center_y = sign * _center(local_bounds["y"])
        location_y = opening_center_y + expected_normal_offset - rotated_center_y
        location_z = opening_bounds["z"][0] + expected_base_offset - local_bounds["z"][0]
        nominal_edge_x = (
            opening_bounds["x"][0]
            if sign > 0
            else opening_bounds["x"][1]
        )
        geometry_centered_x = (
            _center(opening_bounds["x"])
            - sign * _center(local_bounds["x"])
        )
        for placement_kind, location_x in (
            ("nominal_edge", nominal_edge_x),
            ("geometry_center", geometry_centered_x),
        ):
            actual_bounds = _placed_axis_aligned_bounds(
                local_bounds,
                sign=sign,
                location_mm=(location_x, location_y, location_z),
            )
            nominal_bounds = {
                "x": sorted((location_x, location_x + sign * width_mm)),
                "y": [location_y, location_y],
                "z": [location_z, location_z + height_mm],
            }
            diagnostics = _alignment_diagnostics(
                door_bounds=actual_bounds,
                opening_bounds=opening_bounds,
                nominal_bounds=nominal_bounds,
                axis_deviation_degrees=0.0,
                expected_normal_offset_mm=expected_normal_offset,
                expected_base_offset_mm=expected_base_offset,
            )
            candidates.append(
                {
                    "sign": sign,
                    "placement_kind": placement_kind,
                    "location_mm": (location_x, location_y, location_z),
                    "diagnostics": diagnostics,
                }
            )
    selected = max(
        candidates,
        key=lambda item: (
            item["diagnostics"]["valid"],
            item["diagnostics"]["projected_overlap_ratio"],
            -item["diagnostics"]["geometry_placement_excess_mm"],
            -item["diagnostics"]["geometry_center_deviation_mm"],
            item["placement_kind"] == "geometry_center",
            item["sign"],
        ),
    )
    return {
        "location": tuple(
            _project_units(opening, value)
            for value in selected["location_mm"]
        ),
        "ref_direction": (selected["sign"], 0.0, 0.0),
        "diagnostics": selected["diagnostics"],
    }


def measure_door_opening_alignment(
    door: Any,
    opening: Any,
    *, installation_anchor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Measure actual and nominal Door envelopes in Opening-local axes."""

    door_bounds = product_geometry_bounds_in_host_mm(door, opening)
    opening_bounds = product_geometry_bounds_in_host_mm(opening, opening)
    relative = _relative_placement(door, opening)
    width_mm = _millimetres(door, float(door.OverallWidth))
    height_mm = _millimetres(door, float(door.OverallHeight))
    nominal_points = []
    for x in (0.0, _project_units(door, width_mm)):
        for z in (0.0, _project_units(door, height_mm)):
            point = relative @ [x, 0.0, z, 1.0]
            nominal_points.append(
                [
                    float(point[axis]) * _millimetres_per_project_unit(door)
                    for axis in range(3)
                ]
            )
    nominal_bounds = {
        axis_name: [
            min(point[axis] for point in nominal_points),
            max(point[axis] for point in nominal_points),
        ]
        for axis, axis_name in enumerate(("x", "y", "z"))
    }
    anchor = (_verified_installation_anchor(door, opening, installation_anchor)
              if installation_anchor is not None else None)
    axis_deviation = _axis_deviation_degrees(relative)
    if anchor and (relative[0, 0] > 0) != (anchor["axis_sign"] > 0):
        axis_deviation = 180.0
    return _alignment_diagnostics(
        door_bounds=door_bounds,
        opening_bounds=opening_bounds,
        nominal_bounds=nominal_bounds,
        axis_deviation_degrees=axis_deviation,
        expected_normal_offset_mm=_expected_normal_offset(opening, anchor),
        expected_base_offset_mm=float(anchor["base_offset_from_opening_mm"]) if anchor else 0.0,
    )


def _alignment_diagnostics(
    *,
    door_bounds: Mapping[str, list[float]],
    opening_bounds: Mapping[str, list[float]],
    nominal_bounds: Mapping[str, list[float]],
    axis_deviation_degrees: float,
    expected_normal_offset_mm: float = 0.0,
    expected_base_offset_mm: float = 0.0,
) -> dict[str, Any]:
    intersection_x = _intersection_length(
        door_bounds["x"], opening_bounds["x"]
    )
    intersection_y = _intersection_length(
        door_bounds["y"], opening_bounds["y"]
    )
    intersection_z = _intersection_length(
        door_bounds["z"], opening_bounds["z"]
    )
    door_face_area = _extent(door_bounds["x"]) * _extent(door_bounds["z"])
    opening_face_area = (
        _extent(opening_bounds["x"]) * _extent(opening_bounds["z"])
    )
    overlap_denominator = min(door_face_area, opening_face_area)
    projected_overlap = (
        0.0
        if overlap_denominator <= 0.0
        else intersection_x * intersection_z / overlap_denominator
    )
    nominal_center_deviation = math.hypot(
        _center(nominal_bounds["x"]) - _center(opening_bounds["x"]),
        _center(nominal_bounds["z"]) - _center(opening_bounds["z"]),
    )
    geometry_center_deviation = math.sqrt(
        sum(
            (
                _center(door_bounds[axis])
                - _center(opening_bounds[axis])
            )
            ** 2
            for axis in ("x", "y", "z")
        )
    )
    geometry_center_by_axis = {
        axis: abs(
            _center(door_bounds[axis])
            - _center(opening_bounds[axis])
        )
        for axis in ("x", "y", "z")
    }
    geometry_base_deviation = abs(
        float(door_bounds["z"][0]) - float(opening_bounds["z"][0])
    )
    normal_installation_deviation = abs(
        _center(door_bounds["y"]) - _center(opening_bounds["y"])
        - expected_normal_offset_mm
    )
    base_installation_deviation = abs(
        float(door_bounds["z"][0]) - float(opening_bounds["z"][0]) - expected_base_offset_mm
    )
    geometry_placement_excess = max(
        0.0,
        geometry_center_by_axis["x"] - MAX_CENTER_DEVIATION_MM,
        normal_installation_deviation - MAX_CENTER_DEVIATION_MM,
        base_installation_deviation - MAX_CENTER_DEVIATION_MM,
    )
    width_deviation = abs(
        _extent(nominal_bounds["x"]) - _extent(opening_bounds["x"])
    )
    height_deviation = abs(
        _extent(nominal_bounds["z"]) - _extent(opening_bounds["z"])
    )
    valid = (
        projected_overlap >= MIN_PROJECTED_OVERLAP_RATIO
        and intersection_y > 0.0
        and geometry_placement_excess <= 0.0
        and axis_deviation_degrees <= MAX_AXIS_DEVIATION_DEGREES
        and width_deviation <= MAX_DIMENSION_DEVIATION_MM
        and height_deviation <= MAX_DIMENSION_DEVIATION_MM
    )
    return {
        "valid": valid,
        "projected_overlap_ratio": round(projected_overlap, 6),
        "normal_axis_intersection_mm": round(intersection_y, 6),
        "nominal_center_deviation_mm": round(
            nominal_center_deviation, 6
        ),
        "geometry_center_deviation_mm": round(
            geometry_center_deviation, 6
        ),
        "geometry_center_deviation_by_axis_mm": {
            axis: round(value, 6)
            for axis, value in geometry_center_by_axis.items()
        },
        "geometry_base_deviation_mm": round(
            geometry_base_deviation, 6
        ),
        "expected_normal_offset_mm": round(expected_normal_offset_mm, 6),
        "normal_installation_deviation_mm": round(normal_installation_deviation, 6),
        "expected_base_offset_mm": round(expected_base_offset_mm, 6),
        "base_installation_deviation_mm": round(base_installation_deviation, 6),
        "geometry_placement_excess_mm": round(
            geometry_placement_excess, 6
        ),
        "axis_deviation_degrees": round(axis_deviation_degrees, 6),
        "width_deviation_mm": round(width_deviation, 6),
        "height_deviation_mm": round(height_deviation, 6),
        "door_bounds_in_opening_mm": _rounded_bounds(door_bounds),
        "opening_bounds_mm": _rounded_bounds(opening_bounds),
        "nominal_door_bounds_mm": _rounded_bounds(nominal_bounds),
        "thresholds": {
            "minimum_projected_overlap_ratio": (
                MIN_PROJECTED_OVERLAP_RATIO
            ),
            "maximum_center_deviation_mm": MAX_CENTER_DEVIATION_MM,
            "maximum_axis_deviation_degrees": (
                MAX_AXIS_DEVIATION_DEGREES
            ),
            "maximum_dimension_deviation_mm": (
                MAX_DIMENSION_DEVIATION_MM
            ),
        },
    }


def _relative_placement(product: Any, host: Any) -> Any:
    host_matrix = ifcopenshell.util.placement.get_local_placement(
        host.ObjectPlacement
    )
    product_matrix = ifcopenshell.util.placement.get_local_placement(
        product.ObjectPlacement
    )
    return _inverse_rigid_transform(host_matrix) @ product_matrix


def _axis_deviation_degrees(relative: Any) -> float:
    x_axis = [float(relative[index, 0]) for index in range(3)]
    z_axis = [float(relative[index, 2]) for index in range(3)]
    x_norm = math.sqrt(sum(value * value for value in x_axis))
    z_norm = math.sqrt(sum(value * value for value in z_axis))
    if x_norm <= 0.0 or z_norm <= 0.0:
        return 180.0
    x_deviation = math.degrees(
        math.acos(min(1.0, max(-1.0, abs(x_axis[0] / x_norm))))
    )
    z_deviation = math.degrees(
        math.acos(min(1.0, max(-1.0, z_axis[2] / z_norm)))
    )
    return max(x_deviation, z_deviation)


def _placed_axis_aligned_bounds(
    bounds: Mapping[str, list[float]],
    *,
    sign: float,
    location_mm: tuple[float, float, float],
) -> dict[str, list[float]]:
    transformed = []
    for x in bounds["x"]:
        for y in bounds["y"]:
            for z in bounds["z"]:
                transformed.append(
                    (
                        location_mm[0] + sign * x,
                        location_mm[1] + sign * y,
                        location_mm[2] + z,
                    )
                )
    return {
        axis_name: [
            min(point[axis] for point in transformed),
            max(point[axis] for point in transformed),
        ]
        for axis, axis_name in enumerate(("x", "y", "z"))
    }


def _inverse_rigid_transform(matrix: Any) -> Any:
    inverse = matrix.copy()
    rotation = matrix[:3, :3]
    inverse[:3, :3] = rotation.T
    inverse[:3, 3] = -(rotation.T @ matrix[:3, 3])
    inverse[3, :] = (0.0, 0.0, 0.0, 1.0)
    return inverse


def _intersection_length(
    first: list[float], second: list[float]
) -> float:
    return max(0.0, min(first[1], second[1]) - max(first[0], second[0]))


def _extent(interval: list[float]) -> float:
    return max(0.0, float(interval[1]) - float(interval[0]))


def _center(interval: list[float]) -> float:
    return (float(interval[0]) + float(interval[1])) / 2.0


def _millimetres_per_project_unit(entity: Any) -> float:
    return (
        float(ifcopenshell.util.unit.calculate_unit_scale(entity.file))
        * 1000.0
    )


def _millimetres(entity: Any, project_units: float) -> float:
    return project_units * _millimetres_per_project_unit(entity)


def _project_units(entity: Any, millimetres: float) -> float:
    return millimetres / _millimetres_per_project_unit(entity)


def _rounded_bounds(
    bounds: Mapping[str, list[float]],
) -> dict[str, list[float]]:
    return {
        axis: [round(float(value), 6) for value in bounds[axis]]
        for axis in ("x", "y", "z")
    }


__all__ = [
    "MAX_AXIS_DEVIATION_DEGREES",
    "MAX_CENTER_DEVIATION_MM",
    "MAX_DIMENSION_DEVIATION_MM",
    "MIN_PROJECTED_OVERLAP_RATIO",
    "measure_door_opening_alignment",
    "select_door_placement_in_opening",
]
