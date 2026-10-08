"""Deterministic mapped Window placement inside a generated Opening."""

from __future__ import annotations

from collections import Counter
import math
from typing import Any, Mapping

import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit

from .geometry import (
    product_geometry_bounds_in_host_mm,
    product_local_geometry_bounds_mm,
    straight_wall_axis,
)


def select_window_placement_in_opening(
    window: Any,
    opening: Any,
    window_type: Any,
    *, host_wall: Any | None = None,
    installation_anchor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Place reused mapped geometry using surviving same-Type orientation.

    IFC2X3 WindowStyle maps may be anchored to either wall face and may use a
    180-degree occurrence rotation. The Type map alone does not record that
    occurrence convention. Surviving occurrences of the same Type are public
    repair-input evidence, so their opening-relative rotation is used without
    consulting the deleted occurrence or pristine benchmark model.
    """

    if installation_anchor is not None:
        anchor = _verified_window_installation(window, opening, installation_anchor, host_wall=host_wall)
        wall = host_wall if host_wall is not None else _window_installation_host(opening)
        frame, expected = _expected_window_bounds(opening, wall, anchor)
        relative = _inverse_rigid_transform(frame) @ ifcopenshell.util.placement.get_local_placement(opening.ObjectPlacement)
        opening_sign = _canonical_half_turn_sign(relative)
        if opening_sign is None:
            raise ValueError("WINDOW_INSTALLATION_TARGET_AXIS_UNSUPPORTED")
        sign = float(anchor["axis_sign"]) * opening_sign
        local_bounds = product_local_geometry_bounds_mm(window)
        unit = _millimetres_per_project_unit(opening)
        target = _inverse_rigid_transform(relative) @ [
            *(_center(expected[axis]) / unit for axis in ("x", "y", "z")), 1.0
        ]
        location_mm = tuple(float(target[i]) * unit - (sign if i < 2 else 1.) * _center(local_bounds[axis])
                            for i, axis in enumerate(("x", "y", "z")))
        return {"location": tuple(value / unit for value in location_mm), "location_mm": location_mm,
                "ref_direction": (sign, 0., 0.), "orientation_source": "verified_public_window_occurrence",
                "orientation_votes": [], "reference_global_id": anchor["reference_global_id"]}

    local_bounds = product_local_geometry_bounds_mm(window)
    opening_bounds = product_geometry_bounds_in_host_mm(opening, opening)
    votes = _surviving_orientation_votes(window, window_type) if host_wall is None else (
        _wall_relative_orientation_votes(window, opening, window_type, host_wall)
    )
    if votes:
        counts = Counter(votes)
        highest = max(counts.values())
        winners = sorted(
            sign for sign, count in counts.items() if count == highest
        )
        if len(winners) != 1:
            raise ValueError("WINDOW_TYPE_PLACEMENT_ORIENTATION_AMBIGUOUS")
        sign = winners[0]
        source = "surviving_same_type_occurrences" if host_wall is None else "surviving_same_type_wall_axis"
    else:
        # Preserve the historical deterministic orientation when no surviving
        # same-Type occurrence exposes the authoring convention.
        sign = 1.0
        source = "deterministic_positive_orientation_fallback"

    if source == "deterministic_positive_orientation_fallback":
        location_mm = (0.0, opening_bounds["y"][0], 0.0)
        return {
            "location": tuple(
                _project_units(opening, value) for value in location_mm
            ),
            "location_mm": location_mm,
            "ref_direction": (sign, 0.0, 0.0),
            "orientation_source": source,
            "orientation_votes": votes,
        }

    transformed_x = sorted(sign * value for value in local_bounds["x"])
    transformed_y = sorted(sign * value for value in local_bounds["y"])
    location_x = _center(opening_bounds["x"]) - _center(transformed_x)
    if sign > 0.0:
        location_y = opening_bounds["y"][1] - transformed_y[1]
    else:
        location_y = opening_bounds["y"][0] - transformed_y[0]
    location_z = opening_bounds["z"][0] - local_bounds["z"][0]
    location_mm = (location_x, location_y, location_z)
    return {
        "location": tuple(
            _project_units(opening, value) for value in location_mm
        ),
        "location_mm": location_mm,
        "ref_direction": (sign, 0.0, 0.0),
        "orientation_source": source,
        "orientation_votes": votes,
    }


def public_window_installation_anchor(reference: Any) -> dict[str, Any]:
    """Witness the exact authorized public instance, separate from its Type.

    Nominal size, void geometry and complete frame/board geometry are distinct
    facts. A Type alone supplies no instance installation depth or base offset.
    The caller authorizes the reference; this function never chooses a peer.
    """
    if not reference.is_a("IfcWindow") or len(reference.FillsVoids) != 1:
        raise ValueError("WINDOW_INSTALLATION_REFERENCE_FILL_AMBIGUOUS")
    opening = reference.FillsVoids[0].RelatingOpeningElement
    if len(opening.HasFillings) != 1:
        raise ValueError("WINDOW_INSTALLATION_REFERENCE_FILL_AMBIGUOUS")
    wall = _window_installation_host(opening)
    types = [r.RelatingType for r in reference.IsDefinedBy if r.is_a("IfcRelDefinesByType")]
    if len(types) != 1 or not types[0].is_a("IfcWindowStyle"):
        raise ValueError("WINDOW_INSTALLATION_REFERENCE_TYPE_AMBIGUOUS")
    unit = _millimetres_per_project_unit(reference)
    nominal = {key: float(getattr(reference, name)) * unit
               for key, name in (("width", "OverallWidth"), ("height", "OverallHeight"))}
    if not all(math.isfinite(v) and v > 0 for v in nominal.values()):
        raise ValueError("WINDOW_INSTALLATION_REFERENCE_DIMENSIONS_UNSUPPORTED")
    frame = _wall_axis_frame(wall)
    sign = _canonical_half_turn_sign(_inverse_rigid_transform(frame) @
        ifcopenshell.util.placement.get_local_placement(reference.ObjectPlacement))
    if sign is None:
        raise ValueError("WINDOW_INSTALLATION_REFERENCE_AXIS_UNSUPPORTED")
    bounds = _bounds_in_axis_frame_mm(reference, frame)
    void = _bounds_in_axis_frame_mm(opening, frame)
    wall_bounds = _bounds_in_axis_frame_mm(wall, frame)
    if any(min(bounds[a][1], void[a][1]) <= max(bounds[a][0], void[a][0]) for a in ("x", "z")) or (
            min(bounds["y"][1], wall_bounds["y"][1]) <= max(bounds["y"][0], wall_bounds["y"][0])):
        raise ValueError("WINDOW_INSTALLATION_REFERENCE_ALIGNMENT_UNSUPPORTED")
    return {"method": "public-window-installation/0.1", "reference_global_id": str(reference.GlobalId),
            "reference_opening_global_id": str(opening.GlobalId), "reference_wall_global_id": str(wall.GlobalId),
            "type_global_id": str(types[0].GlobalId), "axis_sign": sign,
            "nominal_dimensions_mm": {k: round(v, 6) for k, v in nominal.items()},
            "opening_dimensions_mm": {k: round(_extent(void[a]), 6) for k, a in (("width", "x"), ("height", "z"))},
            "wall_thickness_mm": round(_extent(wall_bounds["y"]), 6),
            "normal_center_offset_from_wall_mm": round(_center(bounds["y"]) - _center(wall_bounds["y"]), 6),
            "center_offset_from_opening_mm": round(_center(bounds["x"]) - _center(void["x"]), 6),
            "base_offset_from_opening_mm": round(bounds["z"][0] - void["z"][0], 6),
            "geometry_extent_mm": {a: round(_extent(bounds[a]), 6) for a in ("x", "y", "z")},
            "mapped_body": _window_mapped_body_signature(reference, types[0])}


def _window_installation_host(opening: Any) -> Any:
    if len(opening.VoidsElements) != 1:
        raise ValueError("WINDOW_INSTALLATION_HOST_AMBIGUOUS")
    wall = opening.VoidsElements[0].RelatingBuildingElement
    if not wall.is_a("IfcWall"):
        raise ValueError("WINDOW_INSTALLATION_HOST_UNSUPPORTED")
    frame = _wall_axis_frame(wall)
    if _canonical_half_turn_sign(_inverse_rigid_transform(frame) @
            ifcopenshell.util.placement.get_local_placement(opening.ObjectPlacement)) is None:
        raise ValueError("WINDOW_INSTALLATION_OPENING_AXIS_UNSUPPORTED")
    return wall


def _window_mapped_body_signature(window: Any, style: Any) -> list[dict[str, Any]]:
    maps = list(style.RepresentationMaps or ())
    body = [r for r in window.Representation.Representations if r.RepresentationIdentifier == "Body"] if window.Representation else []
    if not maps or not body:
        raise ValueError("WINDOW_INSTALLATION_MAPPED_BODY_REQUIRED")
    rows = []
    for representation in body:
        for item in representation.Items:
            if not item.is_a("IfcMappedItem") or item.MappingSource not in maps:
                raise ValueError("WINDOW_INSTALLATION_MAPPING_MISMATCH")
            matrix = ifcopenshell.util.placement.get_mappeditem_transformation(item)
            rows.append({"map_index": maps.index(item.MappingSource),
                         "transform": [round(float(v), 9) for v in matrix.flat]})
    if not rows:
        raise ValueError("WINDOW_INSTALLATION_MAPPED_BODY_REQUIRED")
    return sorted(rows, key=lambda row: (row["map_index"], row["transform"]))


def _verified_window_installation(window: Any, opening: Any, anchor: Mapping[str, Any],
                                  *, host_wall: Any | None = None) -> Mapping[str, Any]:
    try:
        measured = public_window_installation_anchor(window.file.by_guid(str(anchor["reference_global_id"])))
        if dict(anchor) != measured:
            raise ValueError("WINDOW_INSTALLATION_ANCHOR_MISMATCH")
        style = window.file.by_guid(str(measured["type_global_id"]))
        if _window_mapped_body_signature(window, style) != measured["mapped_body"]:
            raise ValueError("WINDOW_INSTALLATION_MAPPING_MISMATCH")
        unit = _millimetres_per_project_unit(window)
        if any(abs(float(getattr(window, name)) * unit - measured["nominal_dimensions_mm"][key]) > .1
               for key, name in (("width", "OverallWidth"), ("height", "OverallHeight"))):
            raise ValueError("WINDOW_INSTALLATION_NOMINAL_DIMENSIONS_MISMATCH")
        wall = host_wall if host_wall is not None else _window_installation_host(opening)
        frame = _wall_axis_frame(wall)
        void = _bounds_in_axis_frame_mm(opening, frame)
        if any(abs(_extent(void[a]) - measured["opening_dimensions_mm"][key]) > .1
               for key, a in (("width", "x"), ("height", "z"))):
            raise ValueError("WINDOW_INSTALLATION_OPENING_DIMENSIONS_MISMATCH")
        if abs(_extent(_bounds_in_axis_frame_mm(wall, frame)["y"]) - measured["wall_thickness_mm"]) > .1:
            raise ValueError("WINDOW_INSTALLATION_THICKNESS_ADAPTATION_UNSUPPORTED")
        return measured
    except (KeyError, TypeError, AttributeError, RuntimeError) as error:
        raise ValueError("WINDOW_INSTALLATION_ANCHOR_UNAVAILABLE") from error


def _expected_window_bounds(opening: Any, wall: Any, anchor: Mapping[str, Any]) -> tuple[Any, dict[str, list[float]]]:
    frame = _wall_axis_frame(wall)
    void = _bounds_in_axis_frame_mm(opening, frame)
    wall_bounds = _bounds_in_axis_frame_mm(wall, frame)
    centers = {"x": _center(void["x"]) + float(anchor["center_offset_from_opening_mm"]),
               "y": _center(wall_bounds["y"]) + float(anchor["normal_center_offset_from_wall_mm"])}
    result = {a: [centers[a] - float(anchor["geometry_extent_mm"][a]) / 2,
                  centers[a] + float(anchor["geometry_extent_mm"][a]) / 2] for a in ("x", "y")}
    bottom = void["z"][0] + float(anchor["base_offset_from_opening_mm"])
    result["z"] = [bottom, bottom + float(anchor["geometry_extent_mm"]["z"])]
    return frame, result


def measure_window_installation(window: Any, opening: Any, anchor: Mapping[str, Any]) -> dict[str, Any]:
    """Recompute maps, dimensions and pose; never accept a self-reported fit."""
    try:
        measured = _verified_window_installation(window, opening, anchor)
        wall = _window_installation_host(opening)
        frame, expected = _expected_window_bounds(opening, wall, measured)
        actual = _bounds_in_axis_frame_mm(window, frame)
        sign = _canonical_half_turn_sign(_inverse_rigid_transform(frame) @
            ifcopenshell.util.placement.get_local_placement(window.ObjectPlacement))
        error = max(abs(actual[a][i] - expected[a][i]) for a in ("x", "y", "z") for i in (0, 1))
        return {"valid": sign == measured["axis_sign"] and error <= .1,
                "maximum_bounds_error_mm": error, "actual_bounds_mm": actual, "expected_bounds_mm": expected,
                "method": measured["method"], "reference_global_id": measured["reference_global_id"]}
    except (ValueError, KeyError, TypeError, AttributeError, RuntimeError) as error:
        return {"valid": False, "reason_code": str(error)}


def _bounds_in_axis_frame_mm(product: Any, frame: Any) -> dict[str, list[float]]:
    unit = _millimetres_per_project_unit(product)
    relative = _inverse_rigid_transform(frame) @ ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement)
    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), product)
    verts = shape.geometry.verts
    if not verts:
        raise ValueError("WINDOW_INSTALLATION_GEOMETRY_EMPTY")
    points = [relative @ [*(float(v) * 1000 / unit for v in verts[i:i+3]), 1.]
              for i in range(0, len(verts), 3)]
    return {a: [min(float(p[i]) * unit for p in points), max(float(p[i]) * unit for p in points)]
            for i, a in enumerate(("x", "y", "z"))}


def _millimetres_per_project_unit(entity: Any) -> float:
    return float(ifcopenshell.util.unit.calculate_unit_scale(entity.file)) * 1000.


def _extent(interval: list[float]) -> float:
    return float(interval[1]) - float(interval[0])


def _wall_relative_orientation_votes(new_window: Any, opening: Any,
                                     window_type: Any, host_wall: Any) -> list[float]:
    """Normalize surviving windows to wall axes, not imported opening axes.

    Opening placement axes may be reversed independently of the wall. Reusing
    a window-to-opening sign on a freshly generated opening can turn the frame
    and glazing around while preserving the bounding box. Same-host evidence
    takes priority over other walls that share the Type.
    """
    target_frame = _wall_axis_frame(host_wall)
    opening_frame = ifcopenshell.util.placement.get_local_placement(opening.ObjectPlacement)
    opening_sign = _canonical_half_turn_sign(_inverse_rigid_transform(target_frame) @ opening_frame)
    if opening_sign is None:
        raise ValueError("WINDOW_OPENING_AXIS_UNSUPPORTED")
    votes, same_host, seen = [], [], set()
    for relation in getattr(window_type, "ObjectTypeOf", ()) or ():
        for peer in relation.RelatedObjects:
            if peer == new_window or not peer.is_a("IfcWindow") or peer.id() in seen:
                continue
            fillings = [r for r in getattr(peer, "FillsVoids", ()) if r.is_a("IfcRelFillsElement")]
            if len(fillings) != 1:
                continue
            peer_opening = fillings[0].RelatingOpeningElement
            voids = list(getattr(peer_opening, "VoidsElements", ()) or ())
            if len(voids) != 1:
                continue
            peer_wall = voids[0].RelatingBuildingElement
            if not peer_wall.is_a("IfcWall"):
                continue
            try:
                frame = _wall_axis_frame(peer_wall)
            except ValueError:
                continue
            peer_matrix = ifcopenshell.util.placement.get_local_placement(peer.ObjectPlacement)
            sign = _canonical_half_turn_sign(_inverse_rigid_transform(frame) @ peer_matrix)
            if sign is not None:
                seen.add(peer.id())
                votes.append(sign * opening_sign)
                if peer_wall == host_wall:
                    same_host.append(sign * opening_sign)
    if same_host and len(set(same_host)) != 1:
        raise ValueError("WINDOW_TYPE_PLACEMENT_ORIENTATION_AMBIGUOUS")
    return same_host or votes


def _wall_axis_frame(wall: Any) -> Any:
    start, end = straight_wall_axis(wall)
    delta = [end[i]-start[i] for i in range(3)]
    length = math.hypot(delta[0], delta[1])
    if length <= 0 or abs(delta[2]) > 1e-6:
        raise ValueError("WINDOW_HOST_AXIS_UNSUPPORTED")
    x, y = delta[0]/length, delta[1]/length
    wall_matrix = ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement)
    frame = wall_matrix.copy()
    frame[:3,0] = wall_matrix[:3,:3] @ [x,y,0]
    frame[:3,1] = wall_matrix[:3,:3] @ [-y,x,0]
    return frame


def _surviving_orientation_votes(
    new_window: Any,
    window_type: Any,
) -> list[float]:
    votes: list[float] = []
    seen: set[int] = set()
    for relation in getattr(window_type, "ObjectTypeOf", ()) or ():
        for peer in relation.RelatedObjects:
            if (
                peer == new_window
                or not peer.is_a("IfcWindow")
                or peer.id() in seen
            ):
                continue
            fills = [
                item
                for item in getattr(peer, "FillsVoids", ()) or ()
                if item.is_a("IfcRelFillsElement")
            ]
            if len(fills) != 1:
                continue
            relative = _relative_placement(
                peer, fills[0].RelatingOpeningElement
            )
            sign = _canonical_half_turn_sign(relative)
            if sign is not None:
                seen.add(peer.id())
                votes.append(sign)
    return votes


def _relative_placement(product: Any, host: Any) -> Any:
    host_matrix = ifcopenshell.util.placement.get_local_placement(
        host.ObjectPlacement
    )
    product_matrix = ifcopenshell.util.placement.get_local_placement(
        product.ObjectPlacement
    )
    return _inverse_rigid_transform(host_matrix) @ product_matrix


def _canonical_half_turn_sign(relative: Any) -> float | None:
    tolerance = 1e-6
    sign = 1.0 if float(relative[0, 0]) >= 0.0 else -1.0
    expected = (
        (sign, 0.0, 0.0),
        (0.0, sign, 0.0),
        (0.0, 0.0, 1.0),
    )
    for row in range(3):
        for column in range(3):
            if (
                abs(float(relative[row, column]) - expected[row][column])
                > tolerance
            ):
                return None
    return sign


def _inverse_rigid_transform(matrix: Any) -> Any:
    inverse = matrix.copy()
    rotation = matrix[:3, :3]
    inverse[:3, :3] = rotation.T
    inverse[:3, 3] = -(rotation.T @ matrix[:3, 3])
    inverse[3, :] = (0.0, 0.0, 0.0, 1.0)
    return inverse


def _center(interval: list[float]) -> float:
    return (float(interval[0]) + float(interval[1])) / 2.0


def _project_units(entity: Any, millimetres: float) -> float:
    millimetres_per_project_unit = (
        float(ifcopenshell.util.unit.calculate_unit_scale(entity.file))
        * 1000.0
    )
    return millimetres / millimetres_per_project_unit


__all__ = ["select_window_placement_in_opening", "public_window_installation_anchor", "measure_window_installation"]
