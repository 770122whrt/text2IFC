"""Private post-repair IFCcompare focused on restored geometry and properties."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from text2ifc_ifc_repair.compare import compare_ifc_models
from text2ifc_ifc_repair.door_geometry import measure_door_opening_alignment
from text2ifc_ifc_repair.geometry import (
    measure_straight_rectangular_member,
    opening_dimensions_mm,
    opening_position_in_wall_mm,
    product_geometry_bounds_in_host_mm,
)

SCHEMA_VERSION = "text2ifc/damage-restoration-ifccompare-debug/0.1"
GEOMETRY_TOLERANCE_MM = 0.1
REQUEST_TOLERANCE_MM = 1e-3


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _single_type_global_id(entity: Any) -> str:
    matches = [
        relation.RelatingType
        for relation in entity.IsDefinedBy
        if relation.is_a("IfcRelDefinesByType")
    ]
    if len(matches) != 1:
        raise ValueError("RESTORATION_DEBUG_TYPE_BINDING_AMBIGUOUS")
    return str(matches[0].GlobalId)


def _containing_storey(model: Any, entity: Any) -> Any:
    matches = [
        relation.RelatingStructure
        for relation in model.by_type("IfcRelContainedInSpatialStructure")
        if entity in relation.RelatedElements
        and relation.RelatingStructure.is_a("IfcBuildingStorey")
    ]
    if len(matches) != 1:
        raise ValueError("RESTORATION_DEBUG_STOREY_BINDING_AMBIGUOUS")
    return matches[0]


def _restored_by_tag(
    model: Any,
    *,
    ifc_class: str,
    tag: str,
) -> Any:
    matches = [
        entity
        for entity in model.by_type(ifc_class)
        if str(getattr(entity, "Tag", "")) == tag
    ]
    if len(matches) != 1:
        raise ValueError(f"RESTORATION_DEBUG_TAG_BINDING_AMBIGUOUS:{tag}")
    return matches[0]


def _direct_properties(model: Any, entity: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for relation in model.by_type("IfcRelDefinesByProperties"):
        if entity not in relation.RelatedObjects:
            continue
        definition = relation.RelatingPropertyDefinition
        if not definition.is_a("IfcPropertySet"):
            continue
        for prop in definition.HasProperties:
            nominal = getattr(prop, "NominalValue", None)
            if nominal is not None:
                result[f"{definition.Name}.{prop.Name}"] = nominal.wrappedValue
    return result


def _differences(
    expected: Any,
    actual: Any,
    *,
    path: str = "",
    tolerance: float = 1e-3,
) -> list[dict[str, Any]]:
    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        differences: list[dict[str, Any]] = []
        for key in sorted(set(expected) | set(actual)):
            child = f"{path}/{key}"
            if key not in expected or key not in actual:
                differences.append(
                    {
                        "path": child,
                        "expected": expected.get(key),
                        "actual": actual.get(key),
                        "reason": "missing_field",
                    }
                )
            else:
                differences.extend(
                    _differences(
                        expected[key],
                        actual[key],
                        path=child,
                        tolerance=tolerance,
                    )
                )
        return differences
    if (
        isinstance(expected, Sequence)
        and not isinstance(expected, (str, bytes))
        and isinstance(actual, Sequence)
        and not isinstance(actual, (str, bytes))
    ):
        if len(expected) != len(actual):
            return [
                {
                    "path": path,
                    "expected": list(expected),
                    "actual": list(actual),
                    "reason": "cardinality",
                }
            ]
        differences = []
        for index, (expected_item, actual_item) in enumerate(
            zip(expected, actual, strict=True)
        ):
            differences.extend(
                _differences(
                    expected_item,
                    actual_item,
                    path=f"{path}/{index}",
                    tolerance=tolerance,
                )
            )
        return differences
    numeric = (
        isinstance(expected, (int, float))
        and not isinstance(expected, bool)
        and isinstance(actual, (int, float))
        and not isinstance(actual, bool)
    )
    if numeric:
        delta = float(actual) - float(expected)
        if math.isfinite(delta) and abs(delta) <= tolerance:
            return []
        return [
            {
                "path": path,
                "expected": expected,
                "actual": actual,
                "delta": delta,
                "tolerance": tolerance,
                "reason": "numeric_mismatch",
            }
        ]
    if expected == actual:
        return []
    return [
        {
            "path": path,
            "expected": expected,
            "actual": actual,
            "reason": "value_mismatch",
        }
    ]


def _column_geometry(model: Any, column: Any) -> dict[str, Any]:
    storey = _containing_storey(model, column)
    bounds = product_geometry_bounds_in_host_mm(column, storey)
    width = bounds["x"][1] - bounds["x"][0]
    depth = bounds["y"][1] - bounds["y"][0]
    if not math.isclose(width, depth, rel_tol=0.0, abs_tol=1e-3):
        raise ValueError("RESTORATION_DEBUG_ORIENTED_COLUMN_UNSUPPORTED")
    center_x = (bounds["x"][0] + bounds["x"][1]) / 2.0
    center_y = (bounds["y"][0] + bounds["y"][1]) / 2.0
    return {
        "axis_start_mm": [center_x, center_y, bounds["z"][0]],
        "axis_end_mm": [center_x, center_y, bounds["z"][1]],
        "axis_direction": [0.0, 0.0, 1.0],
        "axis_extent_mm": bounds["z"][1] - bounds["z"][0],
        "section": {
            "shape": "rectangle",
            "width_mm": width,
            "depth_mm": depth,
        },
        "geometry_bounds_mm": bounds,
    }


def _structural_geometry(model: Any, entity: Any) -> dict[str, Any]:
    if entity.is_a("IfcColumn"):
        return _column_geometry(model, entity)
    storey = _containing_storey(model, entity)
    measurement = measure_straight_rectangular_member(
        entity,
        relative_to=storey,
    )
    body = next(
        representation
        for representation in entity.Representation.Representations
        if representation.RepresentationIdentifier == "Body"
    )
    solid = body.Items[0]
    profile = solid.SweptArea
    member_matrix = ifcopenshell.util.placement.get_local_placement(
        entity.ObjectPlacement
    )
    storey_matrix = ifcopenshell.util.placement.get_local_placement(
        storey.ObjectPlacement
    )
    solid_matrix = ifcopenshell.util.placement.get_axis2placement(solid.Position)
    frame = np.linalg.inv(storey_matrix) @ member_matrix @ solid_matrix
    x_is_vertical = abs(float(frame[2, 0])) > abs(float(frame[2, 1]))
    scale = ifcopenshell.util.unit.calculate_unit_scale(entity.file) * 1000.0
    measurement["profile_local_section_mm"] = dict(measurement["section"])
    measurement["section"] = {
        "shape": "rectangle",
        "width_mm": float(profile.YDim if x_is_vertical else profile.XDim)
        * scale,
        "height_mm": float(profile.XDim if x_is_vertical else profile.YDim)
        * scale,
    }
    measurement["profile_axis_mapping"] = {
        "profile_x_is_vertical": x_is_vertical,
    }
    return measurement


def _opening_for_window(model: Any, window: Any) -> Any:
    matches = [
        relation.RelatingOpeningElement
        for relation in model.by_type("IfcRelFillsElement")
        if relation.RelatedBuildingElement == window
    ]
    if len(matches) != 1:
        raise ValueError("RESTORATION_DEBUG_WINDOW_OPENING_AMBIGUOUS")
    return matches[0]


def _wall_for_opening(model: Any, opening: Any) -> Any:
    matches = [
        relation.RelatingBuildingElement
        for relation in model.by_type("IfcRelVoidsElement")
        if relation.RelatedOpeningElement == opening
    ]
    if len(matches) != 1:
        raise ValueError("RESTORATION_DEBUG_OPENING_HOST_AMBIGUOUS")
    return matches[0]


def _door_geometry(model: Any, door: Any, *, opening_global_id: str) -> dict[str, Any]:
    opening = model.by_guid(opening_global_id)
    alignment = measure_door_opening_alignment(door, opening)
    return {
        "overall_width_mm": float(door.OverallWidth),
        "overall_height_mm": float(door.OverallHeight),
        "opening_dimensions_mm": opening_dimensions_mm(opening),
        "alignment": {
            key: alignment[key]
            for key in (
                "valid",
                "projected_overlap_ratio",
                "geometry_base_deviation_mm",
                "geometry_placement_excess_mm",
                "axis_deviation_degrees",
                "width_deviation_mm",
                "height_deviation_mm",
                "door_bounds_in_opening_mm",
                "opening_bounds_mm",
            )
        },
    }


def _window_geometry(model: Any, window: Any) -> dict[str, Any]:
    opening = _opening_for_window(model, window)
    wall = _wall_for_opening(model, opening)
    position = opening_position_in_wall_mm(opening, wall)
    return {
        "overall_width_mm": float(window.OverallWidth),
        "overall_height_mm": float(window.OverallHeight),
        "opening_dimensions_mm": opening_dimensions_mm(opening),
        "opening_position_mm": {
            key: position[key]
            for key in (
                "center_offset",
                "normal_offset",
                "sill_height",
                "geometry_bounds_mm",
            )
        },
        # Compare physical envelopes in the common Wall frame. Original and
        # generated Openings may use different but equivalent local origins.
        "window_bounds_in_wall_mm": product_geometry_bounds_in_host_mm(
            window, wall
        ),
        "opening_bounds_in_wall_mm": product_geometry_bounds_in_host_mm(
            opening, wall
        ),
    }


def _requested_geometry(
    member: Mapping[str, Any],
    *,
    key: str,
) -> dict[str, Any]:
    if key == "beams":
        start = member["axis"]["start"]
        end = member["axis"]["end"]
        start_values = [start[f"{axis}_mm"] for axis in ("x", "y", "z")]
        end_values = [end[f"{axis}_mm"] for axis in ("x", "y", "z")]
        vector = [
            float(end_values[index]) - float(start_values[index])
            for index in range(3)
        ]
        extent = math.sqrt(sum(value * value for value in vector))
        return {
            "axis_start_mm": start_values,
            "axis_end_mm": end_values,
            "axis_direction": [value / extent for value in vector],
            "axis_extent_mm": extent,
            "section": {
                "shape": "rectangle",
                "width_mm": member["section"]["width_mm"],
                "height_mm": member["section"]["height_mm"],
            },
        }
    if key == "columns":
        base = member["axis"]["base"]
        top = member["axis"]["top"]
        base_values = [base[f"{axis}_mm"] for axis in ("x", "y", "z")]
        top_values = [top[f"{axis}_mm"] for axis in ("x", "y", "z")]
        extent = float(top_values[2]) - float(base_values[2])
        return {
            "axis_start_mm": base_values,
            "axis_end_mm": top_values,
            "axis_direction": [0.0, 0.0, 1.0],
            "axis_extent_mm": extent,
            "section": {
                "shape": "rectangle",
                "width_mm": member["section"]["width_mm"],
                "depth_mm": member["section"]["depth_mm"],
            },
        }
    opening = member["opening"]
    dimensions = {
        "width": opening["width_mm"],
        "height": opening["height_mm"],
    }
    if key == "doors":
        dimensions["depth"] = opening["depth_mm"]
        return {
            "overall_width_mm": opening["width_mm"],
            "overall_height_mm": opening["height_mm"],
            "opening_dimensions_mm": dimensions,
        }
    dimensions["depth"] = member["wall_query"]["thickness_mm"]
    return {
        "overall_width_mm": opening["width_mm"],
        "overall_height_mm": opening["height_mm"],
        "opening_dimensions_mm": dimensions,
        "opening_position_mm": {
            "center_offset": opening["center_offset_mm"],
            "sill_height": opening["sill_height_mm"],
        },
    }


def _expected_differences(
    expected: Any,
    actual: Any,
    *,
    path: str,
    tolerance: float,
) -> list[dict[str, Any]]:
    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        differences: list[dict[str, Any]] = []
        for key in sorted(expected):
            child = f"{path}/{key}"
            if key not in actual:
                differences.append(
                    {
                        "path": child,
                        "expected": expected[key],
                        "actual": None,
                        "reason": "missing_field",
                    }
                )
            else:
                differences.extend(
                    _expected_differences(
                        expected[key],
                        actual[key],
                        path=child,
                        tolerance=tolerance,
                    )
                )
        return differences
    return _differences(
        expected,
        actual,
        path=path,
        tolerance=tolerance,
    )


def _property_debug(
    member: Mapping[str, Any],
    *,
    original_model: Any,
    original: Any,
    repaired_model: Any,
    repaired: Any,
) -> dict[str, Any]:
    original_properties = _direct_properties(original_model, original)
    repaired_properties = _direct_properties(repaired_model, repaired)
    records = []
    for claim in member.get("property_intents", ()):
        key = f"{claim['set_name']}.{claim['property_name']}"
        requested = claim["raw_value"]
        original_value = original_properties.get(key)
        repaired_value = repaired_properties.get(key)
        request_vs_original = _differences(
            requested, original_value, path=f"/{key}", tolerance=1e-6
        )
        original_vs_repaired = _differences(
            original_value, repaired_value, path=f"/{key}", tolerance=1e-6
        )
        records.append(
            {
                "property": key,
                "requested": requested,
                "original": original_value,
                "repaired": repaired_value,
                "requested_value_type": claim.get("requested_value_type"),
                "status": (
                    "passed"
                    if not request_vs_original and not original_vs_repaired
                    else "failed"
                ),
                "request_vs_original_differences": request_vs_original,
                "original_vs_repaired_differences": original_vs_repaired,
            }
        )
    return {
        "status": (
            "passed"
            if all(record["status"] == "passed" for record in records)
            else "failed"
        ),
        "property_count": len(records),
        "properties": records,
    }


def _member_debug(
    member: Mapping[str, Any],
    *,
    key: str,
    index: int,
    original_model: Any,
    repaired_model: Any,
) -> dict[str, Any]:
    definitions = {
        "beams": ("IfcBeam", "restore-beam", _structural_geometry),
        "columns": ("IfcColumn", "restore-column", _structural_geometry),
        "doors": ("IfcDoor", "restore-door", None),
        "windows": ("IfcWindow", "restore-window", _window_geometry),
    }
    ifc_class, tag_prefix, projector = definitions[key]
    original = original_model.by_guid(str(member["gid"]))
    repaired = _restored_by_tag(
        repaired_model,
        ifc_class=ifc_class,
        tag=f"{tag_prefix}-{index}",
    )
    if key == "doors":
        original_geometry = _door_geometry(
            original_model,
            original,
            opening_global_id=str(member["opening"]["gid"]),
        )
        repaired_geometry = _door_geometry(
            repaired_model,
            repaired,
            opening_global_id=str(member["opening"]["gid"]),
        )
    else:
        original_geometry = projector(original_model, original)
        repaired_geometry = projector(repaired_model, repaired)
    original_comparable = dict(original_geometry)
    repaired_comparable = dict(repaired_geometry)
    if key == "beams":
        for diagnostic_key in (
            "profile_local_section_mm",
            "profile_axis_mapping",
        ):
            original_comparable.pop(diagnostic_key, None)
            repaired_comparable.pop(diagnostic_key, None)
    original_geometry_differences = _differences(
        original_comparable,
        repaired_comparable,
        path="/geometry",
        tolerance=GEOMETRY_TOLERANCE_MM,
    )
    requested_geometry = _requested_geometry(member, key=key)
    request_geometry_differences = _expected_differences(
        requested_geometry,
        repaired_comparable,
        path="/geometry",
        tolerance=REQUEST_TOLERANCE_MM,
    )
    geometry_differences = (
        original_geometry_differences + request_geometry_differences
    )
    properties = _property_debug(
        member,
        original_model=original_model,
        original=original,
        repaired_model=repaired_model,
        repaired=repaired,
    )
    expected_type = str(member["prototype_intent"]["reference"])
    original_type = _single_type_global_id(original)
    repaired_type = _single_type_global_id(repaired)
    type_status = (
        "passed"
        if original_type == repaired_type == expected_type
        else "failed"
    )
    status = (
        "passed"
        if not geometry_differences
        and properties["status"] == "passed"
        and type_status == "passed"
        else "failed"
    )
    return {
        "member_kind": key,
        "ifc_class": ifc_class,
        "original_global_id": str(original.GlobalId),
        "repaired_global_id": str(repaired.GlobalId),
        "repaired_tag": str(repaired.Tag),
        "status": status,
        "geometry": {
            "status": "passed" if not geometry_differences else "failed",
            "original": original_geometry,
            "requested": requested_geometry,
            "repaired": repaired_geometry,
            "original_vs_repaired_tolerance_mm": GEOMETRY_TOLERANCE_MM,
            "request_vs_repaired_tolerance_mm": REQUEST_TOLERANCE_MM,
            "original_vs_repaired_differences": (
                original_geometry_differences
            ),
            "request_vs_repaired_differences": (
                request_geometry_differences
            ),
            "differences": geometry_differences,
        },
        "properties": properties,
        "type_reuse": {
            "status": type_status,
            "expected_type_global_id": expected_type,
            "original_type_global_id": original_type,
            "repaired_type_global_id": repaired_type,
        },
    }


def compare_damage_restoration(
    case: Mapping[str, Any],
    *,
    original_path: Path | str,
    repaired_path: Path | str,
) -> dict[str, Any]:
    """Run whole-model IFCcompare plus role-mapped geometry/property debug."""

    original_path = Path(original_path).resolve()
    repaired_path = Path(repaired_path).resolve()
    original_model = ifcopenshell.open(str(original_path))
    repaired_model = ifcopenshell.open(str(repaired_path))
    members = []
    for key in ("beams", "columns", "doors", "windows"):
        for index, member in enumerate(case["damage"].get(key, ()), start=1):
            members.append(
                _member_debug(
                    member,
                    key=key,
                    index=index,
                    original_model=original_model,
                    repaired_model=repaired_model,
                )
            )
    whole_model = compare_ifc_models(
        original_path,
        repaired_path,
        allowed_changed_ids=(),
    )
    focused_status = (
        "passed"
        if members and all(member["status"] == "passed" for member in members)
        else "failed"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "comparison_mode": "private_post_repair_role_mapped_debug",
        "comparator": "text2ifc_ifc_repair.compare.compare_ifc_models",
        "inputs": {
            "original_sha256": _sha256(original_path),
            "repaired_sha256": _sha256(repaired_path),
            "private_mapping_source": "frozen_damage_recipe",
        },
        "status": focused_status,
        "member_count": len(members),
        "failed_member_count": sum(
            member["status"] != "passed" for member in members
        ),
        "members": members,
        "whole_model_ifccompare": whole_model,
        "identity_boundary": (
            "Restored occurrences may have new GlobalIds. Geometry, requested "
            "occurrence properties, and exact surviving Type bindings are "
            "therefore compared through the frozen private role mapping."
        ),
    }


__all__ = ["compare_damage_restoration"]
