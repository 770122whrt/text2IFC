"""Versioned, bounded Generation filling parameters; all lengths are millimetres."""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from .validation import ValidationIssue

VERSION = "text2ifc/basic-filling/1.0"
TEMPLATES = {
    "window-single": "IfcWindow", "window-double-vertical": "IfcWindow",
    "door-left": "IfcDoor", "door-right": "IfcDoor",
}


def _number(value: Any) -> bool:
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def validate_basic_filling(value: Any, ifc_class: str, path: str = "/Representation") -> list[ValidationIssue]:
    issues = []
    def fail(field, message):
        issues.append(ValidationIssue("INVALID_BASIC_FILLING", f"{path}/{field}", message))
    if not isinstance(value, Mapping):
        fail("", "Basic filling must be an object.")
        return issues
    for field in set(value) - {"kind", "template_id", "template_version", "width", "height", "depth", "parameters"}:
        fail(field, "Unsupported basic filling field.")
    template = value.get("template_id")
    if value.get("kind") != "basic_filling" or template not in TEMPLATES or TEMPLATES.get(template) != ifc_class:
        fail("template_id", "Template must belong to this occurrence family.")
    if value.get("template_version") != VERSION:
        fail("template_version", "Unsupported template version.")
    for field in ("width", "height", "depth"):
        if not _number(value.get(field)) or not 0 < value[field] <= 100_000_000:
            fail(field, "A positive finite input dimension within the coordinate bound is required.")
    parameters = value.get("parameters", {})
    if not isinstance(parameters, Mapping):
        fail("parameters", "Parameters must be an object.")
        return issues
    is_door = ifc_class == "IfcDoor"
    ranges = {"frame_width": (10, 100), "frame_depth": (20, 200), "panel_thickness": (10, 100) if is_door else (3, 30)}
    if template == "window-double-vertical":
        ranges["split_ratio"] = (.2, .8)
    for field, number in parameters.items():
        if field not in ranges or not _number(number) or not ranges[field][0] <= number <= ranges[field][1]:
            fail(f"parameters/{field}", "Unknown, inapplicable or out-of-range template parameter.")
    if issues:
        return issues
    effective = {"frame_width": 50., "frame_depth": 60., "panel_thickness": 40. if is_door else 6., **parameters}
    frame = effective["frame_width"]
    if max(effective["frame_depth"], effective["panel_thickness"]) > value["depth"]:
        fail("depth", "Frame and panel depths must fit the input opening depth; defaults are never shrunk.")
    if value["width"] <= 2 * frame or value["height"] <= (frame if is_door else 2 * frame):
        fail("parameters/frame_width", "Frame must leave a positive clear aperture.")
    if template == "window-double-vertical":
        split = value["width"] * effective.get("split_ratio", .5)
        if min(split, value["width"] - split) <= 1.5 * frame:
            fail("parameters/split_ratio", "Each pane must retain a positive clear aperture.")
    return issues


def resolve_basic_filling(value: Mapping[str, Any], ifc_class: str) -> dict[str, Any]:
    issues = validate_basic_filling(value, ifc_class)
    if issues:
        raise ValueError("; ".join(issue.message for issue in issues))
    parameters = {"frame_width": 50., "frame_depth": 60., "panel_thickness": 40. if ifc_class == "IfcDoor" else 6.}
    if value["template_id"] == "window-double-vertical":
        parameters["split_ratio"] = .5
    supplied = value.get("parameters", {})
    parameters.update(supplied)
    sources = {field: "user" if field in supplied else f"{VERSION}:{value['template_id']}" for field in parameters}
    return {**value, "parameters": parameters, "parameter_sources": sources}


def validate_basic_filling_document(document: Mapping[str, Any]) -> list[ValidationIssue]:
    """Check nominal size and host/opening fit without modifying user placement."""
    import numpy as np
    from .placement import world_transform_for

    issues = []
    records = {record["id"]: record for record in document.get("entities", [])}
    relationships = document.get("relationships", [])
    for index, record in enumerate(document.get("entities", [])):
        attributes = record.get("attributes", {})
        rep = attributes.get("Representation", {})
        if not isinstance(rep, Mapping) or rep.get("kind") != "basic_filling":
            continue
        path = f"/entities/{index}/attributes/Representation"
        def fail(message):
            issues.append(ValidationIssue("BASIC_FILLING_CONSTRAINT_CONFLICT", path, message))
        if validate_basic_filling(rep, record["ifc_class"], path):
            continue
        for dim in ("Width", "Height"):
            if attributes.get("Overall" + dim) != rep[dim.lower()]:
                fail(f"Overall{dim} must equal the explicit filling {dim.lower()}.")
        fills = [r["attributes"] for r in relationships if r.get("ifc_class") == "IfcRelFillsElement" and r.get("attributes", {}).get("RelatedBuildingElement") == record["id"]]
        if len(fills) != 1:
            fail("Basic filling requires exactly one explicit opening relationship.")
            continue
        opening_id = fills[0]["RelatingOpeningElement"]
        voids = [r["attributes"] for r in relationships if r.get("ifc_class") == "IfcRelVoidsElement" and r.get("attributes", {}).get("RelatedOpeningElement") == opening_id]
        if len(voids) != 1 or opening_id not in records:
            fail("Opening requires exactly one supported wall host.")
            continue
        host_id = voids[0]["RelatingBuildingElement"]
        host = records.get(host_id, {})
        if host.get("ifc_class") not in {"IfcWall", "IfcWallStandardCase"}:
            fail("Basic filling host must be a supported wall.")
            continue
        opening_rep = records[opening_id].get("attributes", {}).get("Representation", {})
        host_rep = host.get("attributes", {}).get("Representation", {})
        if document.get("schema_version") in {"bim-json/2.4", "bim-json/2.5"}:
            from .polygon_wall import filling_fit_messages
            try:
                for message in filling_fit_messages(document, host_id, opening_id, record["id"]):
                    fail(message)
            except (KeyError, TypeError, ValueError, IndexError, np.linalg.LinAlgError) as exc:
                fail(f"Filling/opening/host geometry is unsupported or unresolved: {exc}")
        else:
            supported = all(r.get("kind") == "extruded_profile" and r.get("profile", {}).get("kind") == "rectangle" and r.get("direction") == [0, 0, 1] and "position" not in r for r in (opening_rep, host_rep))
            if not supported:
                fail("Basic filling currently requires vertical rectangular host and opening extrusions.")
                continue
            try:
                opening_world = np.array(world_transform_for(document, opening_id))
                fill_world = np.array(world_transform_for(document, record["id"]))
                host_world = np.array(world_transform_for(document, host_id))
                local = np.linalg.inv(opening_world) @ fill_world
                opening_in_host = np.linalg.inv(host_world) @ opening_world
                if not np.allclose(local[:3, :3], np.eye(3), atol=1e-9) or not np.allclose(opening_in_host[:3, :3], np.eye(3), atol=1e-9):
                    fail("Filling, opening and wall axes must align in the bounded template contract.")
                ox, _, oz = opening_in_host[:3, 3]
                if abs(ox) + opening_rep["profile"]["x"] / 2 > host_rep["profile"]["x"] / 2 + 1e-6 or oz < -1e-6 or oz + opening_rep["depth"] > host_rep["depth"] + 1e-6:
                    fail("The unchanged opening must lie within the wall width and height.")
                x, y, z = local[:3, 3]
                if abs(x) + rep["width"] / 2 > opening_rep["profile"]["x"] / 2 + 1e-6 or z < -1e-6 or z + rep["height"] > opening_rep["depth"] + 1e-6:
                    fail("Filling width, height or placement exceeds the unchanged opening.")
                if abs(y) + rep["depth"] / 2 > opening_rep["profile"]["y"] / 2 + 1e-6:
                    fail("Input filling depth exceeds the unchanged opening depth.")
                fy = (np.linalg.inv(host_world) @ fill_world)[1, 3]
                if abs(fy) + rep["depth"] / 2 > host_rep["profile"]["y"] / 2 + 1e-6:
                    fail("Input filling depth or placement exceeds the wall thickness.")
            except (KeyError, TypeError, ValueError, np.linalg.LinAlgError):
                fail("Filling/opening/host placement is unresolved.")
        if record["ifc_class"] == "IfcDoor":
            required = "SINGLE_SWING_LEFT" if rep["template_id"] == "door-left" else "SINGLE_SWING_RIGHT"
            for relation in relationships:
                attr = relation.get("attributes", {})
                if relation.get("ifc_class") == "IfcRelDefinesByType" and record["id"] in attr.get("RelatedObjects", []):
                    style = records.get(attr.get("RelatingType"), {})
                    if style.get("attributes", {}).get("OperationType") != required:
                        fail("Explicit DoorStyle operation conflicts with the requested template hand.")
    return issues
