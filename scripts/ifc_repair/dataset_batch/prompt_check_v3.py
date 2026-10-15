"""Read-only, independent public-text audit for dataset request profile 1.3.

The public parser accepts only damaged IFC and the actual request. It resolves
all locators, complete shapes, opening instructions and instance properties
before the audit introduces the reference IFC or private mutation identities.
No renderer, recipe or private geometry specification supplies missing facts.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from itertools import product
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from scripts.ifc_repair.audit_initial_dataset import _mesh, matrix
from .prompt_check import _actual_host, _bounds, _floor_of, _instance_property


CHECKER_VERSION = "text2ifc/dataset-prompt-check/1.2"
PROFILE = "text2ifc/dataset-request/1.3"
HEADER = "请按以下要求修复模型。世界坐标用米，尺寸和相对距离用毫米；公开数值最多三位小数。"
NAME_HEADER = "请按以下要求修复模型。尺寸和相对距离用毫米；公开数值最多三位小数。"
FOOTER = "除以上补建、洞口关系及指定实例属性外，其余构件、楼层、尺寸、位置、类型和材料保持原样。"
CLASSES = {"门": "IfcDoor", "窗": "IfcWindow", "梁": "IfcBeam", "柱": "IfcColumn"}
NUMBER = r"[-+]?\d+(?:\.\d{1,3})?"
POINT = rf"（({NUMBER})，({NUMBER})，({NUMBER})）"
WORLD_TOLERANCE_M = 0.000501
MM_TOLERANCE_M = 0.000000501
ANGLE_TOLERANCE_DEG = 0.0005
EXACT_AXIS_TOLERANCE = 0.000002
SCOPE = "actual public text and surviving damaged-IFC anchors; complete local shape, placement, floor, real host, opening/void/fill and instance-property restoration; no Provider, repair execution or all-semantic-field equivalence"


class _Cursor:
    def __init__(self, text):
        self.text = text

    def take(self, pattern, code):
        match = re.match(pattern, self.text)
        if match is None:
            raise ValueError(code)
        self.text = self.text[match.end():]
        return match

    def finish(self):
        if self.text:
            raise ValueError("unparsed_operation_text")


def _vector(match, start=1):
    values = np.array([float(match[index]) for index in range(start, start + 3)])
    if not np.isfinite(values).all():
        raise ValueError("invalid_public_vector")
    return values


def _close(left, right, tolerance):
    return np.allclose(left, right, atol=tolerance, rtol=0)


def _floor(model, name):
    matches = [item for item in model.by_type("IfcBuildingStorey") if item.Name == name]
    if len(matches) != 1:
        raise ValueError("storey_not_unique_or_absent")
    return matches[0]


def _cached_bounds(entity, cache, *, world=False):
    key = (entity.id(), world)
    if key not in cache:
        cache[key] = _bounds(entity, world=world, uncut=True)
    return cache[key]


def _direction(axis):
    x, y, z = axis
    if abs(z) > math.hypot(x, y):
        return "上" if z > 0 else "下"
    index = int(math.floor(math.degrees(math.atan2(y, x)) / 45 + 0.5)) % 8
    return ("东", "东北", "北", "西北", "西", "西南", "南", "东南")[index]


def _host(cursor, damaged, floor, mode, unit, cache):
    if mode == "host_wall":
        found = cursor.take(r"宿主墙「([^」]+)」，长度正向大致朝([^，。]+)，厚度正向大致朝([^，。]+)。", "wall_host_missing")
        matches = [wall for wall in damaged.by_type("IfcWall") if wall.Name == found[1] and _floor_of(wall) == floor]
        if len(matches) != 1:
            raise ValueError("wall_not_unique_or_absent")
        frame = matrix(matches[0], unit)
        if (found[2], found[3]) != (_direction(frame[:3, 0]), _direction(frame[:3, 1])):
            raise ValueError("wall_direction_mismatch")
        return matches[0]
    if not cursor.text.startswith("宿主墙"):
        return None
    found = cursor.take(r"宿主墙未扣洞口的整体范围为" + POINT + r"至" + POINT + r"米。", "wall_bounds_missing")
    expected = np.array([_vector(found), _vector(found, 4)])
    if np.any(expected[0] >= expected[1]):
        raise ValueError("wall_bounds_invalid")
    matches = [wall for wall in damaged.by_type("IfcWall") if _close(_cached_bounds(wall, cache, world=True), expected, WORLD_TOLERANCE_M)]
    if len(matches) != 1:
        raise ValueError("wall_not_unique_or_absent")
    # A world-bounds locator also supports a wall spanning more than one floor.
    return matches[0]


def _position(cursor, mode, host, unit, cache, *, prefix="放置基点"):
    if mode == "world":
        return _vector(cursor.take(re.escape(prefix) + r"世界坐标为" + POINT + r"米。", "placement_missing"))
    if host is None:
        raise ValueError("wall_host_missing")
    found = cursor.take(re.escape(prefix) + rf"距墙长度起端({NUMBER})毫米，距墙厚度负向侧({NUMBER})毫米，高出墙底({NUMBER})毫米。", "placement_missing")
    local = _cached_bounds(host, cache)[0] + _vector(found) / 1000
    return (matrix(host, unit) @ np.r_[local, 1])[:3]


def _rotation(angles):
    yaw, pitch, roll = np.radians(angles)
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return rz @ ry @ rx


def _orientation(cursor, mode, host, unit, *, peer=None, prefix=""):
    if peer is not None and cursor.text.startswith("朝向与参照相同。"):
        cursor.take("朝向与参照相同。", "orientation_missing")
        base = matrix(peer, unit)[:3, :3]
        return {"rotation": base, "base": base, "angles": None}
    if peer is not None:
        clause = "朝向相对参照，按自身高、厚、宽轴依次旋转"
        base = matrix(peer, unit)[:3, :3]
    else:
        clause = prefix + "朝向相对" + ("项目坐标系" if mode == "world" else "宿主墙") + "，按高、厚、宽轴依次旋转"
        base = np.eye(3) if mode == "world" else matrix(host, unit)[:3, :3]
    found = cursor.take(re.escape(clause) + rf"({NUMBER})度、({NUMBER})度、({NUMBER})度。", "orientation_missing")
    angles = _vector(found)
    return {"rotation": base @ _rotation(angles), "base": base, "angles": angles}


def _peer(cursor, damaged, mode, unit, expected_class):
    if mode == "world":
        found = cursor.take(r"完整形状复制参照：现存(Ifc\w+)世界基点" + POINT + r"米。", "public_peer_locator_missing")
        origin = _vector(found, 2)
        matches = [entity for entity in damaged.by_type(found[1]) if _close(matrix(entity, unit)[:3, 3], origin, WORLD_TOLERANCE_M)]
    else:
        found = cursor.take(r"完整形状复制参照：楼层「([^」]+)」的现存(Ifc\w+)「([^」]+)」。", "public_peer_locator_missing")
        floor = _floor(damaged, found[1])
        matches = [entity for entity in damaged.by_type(found[2]) if entity.Name == found[3] and _floor_of(entity) == floor]
    if len(matches) != 1:
        raise ValueError("public_peer_not_unique_or_absent")
    if matches[0].is_a() != expected_class:
        raise ValueError("public_peer_class_mismatch")
    return matches[0]


def _reference_authorability(entity):
    """Check the publicly selected door/window without consulting any recipe."""
    if entity.is_a() not in {"IfcDoor", "IfcWindow"}:
        return None
    from text2ifc_ifc_repair.door_geometry import public_door_installation_anchor
    from text2ifc_ifc_repair.window_geometry import public_window_installation_anchor

    anchor = public_door_installation_anchor if entity.is_a("IfcDoor") else public_window_installation_anchor
    try:
        anchor(entity)
        return "public_installation_anchor"
    except ValueError as exc:
        reason = str(exc)
    try:
        if _box_certificate(entity):
            return "independent_basic_box"
    except (ValueError, RuntimeError, AttributeError):
        pass
    raise ValueError("public_reference_not_authorable:" + reason)


def _shape(cursor, damaged, mode, unit, expected_class, *, prefix=""):
    if not prefix and cursor.text.startswith("完整形状复制参照："):
        peer = _peer(cursor, damaged, mode, unit, expected_class)
        authorability = _reference_authorability(peer)
        return {"method": "peer", "peer": peer, "mesh": _mesh(peer), "bounds": _bounds(peer), "reference_authorability": authorability}
    if cursor.text.startswith(prefix + "形状为单一长方体"):
        found = cursor.take(re.escape(prefix) + r"形状为单一长方体，沿自身三个轴方向的尺寸为" + POINT + r"毫米；基点距对应负向面的距离为" + POINT + r"毫米。", "basic_shape_incomplete")
        dimensions, offsets = _vector(found) / 1000, _vector(found, 4) / 1000
        if np.any(dimensions <= 0):
            raise ValueError("basic_shape_dimensions_invalid")
        return {"method": "box", "dimensions": dimensions, "offsets": offsets, "bounds": np.array([-offsets, dimensions - offsets])}
    raise ValueError("complete_geometry_not_described")


def _located(cursor, damaged, mode, unit, cache):
    floor = _floor(damaged, cursor.take(r"归属楼层「([^」]+)」。", "storey_membership_missing")[1])
    host = _host(cursor, damaged, floor, mode, unit, cache)
    return {"floor": floor, "host": host, "position": _position(cursor, mode, host, unit, cache), "position_basis": np.eye(3) if mode == "world" else matrix(host, unit)[:3, :3], "position_tolerance": WORLD_TOLERANCE_M if mode == "world" else MM_TOLERANCE_M}


def _set_frame(located, orientation):
    frame = np.eye(4)
    frame[:3, 3], frame[:3, :3] = located["position"], orientation["rotation"]
    return {**located, "orientation": orientation, "frame": frame}


def _opening(cursor, target, damaged, mode, unit, cache):
    host = target["host"]
    if host is None:
        raise ValueError("wall_host_missing")
    if cursor.text.startswith("保留现有洞口："):
        cursor.take("保留现有洞口：", "opening_spec_missing")
        if mode == "world":
            found = cursor.take(r"世界基点" + POINT + r"米；", "retained_opening_locator_missing")
            position = _vector(found)
        else:
            found = cursor.take(rf"距墙长度起端({NUMBER})毫米，距墙厚度负向侧({NUMBER})毫米，高出墙底({NUMBER})毫米；", "retained_opening_locator_missing")
            position = (matrix(host, unit) @ np.r_[_cached_bounds(host, cache)[0] + _vector(found) / 1000, 1])[:3]
        cursor.take("将新构件填入并建立门窗填充关系。", "fill_relationship_missing")
        tolerance = target["position_tolerance"]
        located = {"position": position, "position_tolerance": tolerance, "position_basis": target["position_basis"]}
        matches = [rel.RelatedOpeningElement for rel in host.HasOpenings if _position_close(located, matrix(rel.RelatedOpeningElement, unit)[:3, 3])]
        if len(matches) != 1:
            raise ValueError("retained_opening_not_unique_or_absent")
        entity = matches[0]
        if len(entity.VoidsElements) != 1 or entity.VoidsElements[0].RelatingBuildingElement != host:
            raise ValueError("retained_opening_void_binding_mismatch")
        if entity.HasFillings:
            raise ValueError("retained_opening_already_filled")
        frame = matrix(entity, unit)
        orientation = {"rotation": frame[:3, :3], "base": frame[:3, :3], "angles": None}
        return {"preserve": True, "entity": entity, "method": "peer", "mesh": _mesh(entity), **_set_frame(located, orientation)}
    if cursor.text.startswith("洞口复制参照构件所填洞口"):
        cursor.take("洞口复制参照构件所填洞口，保持与新构件相同的相对位置和朝向；", "opening_copy_instruction_incomplete")
        cursor.take("在宿主墙上建立洞口", "void_relationship_missing")
        cursor.take("并建立门窗填充关系。", "fill_relationship_missing")
        peer = target.get("peer")
        if peer is None or len(peer.FillsVoids) != 1:
            raise ValueError("public_opening_peer_not_unique_or_absent")
        opening = peer.FillsVoids[0].RelatingOpeningElement
        if len(opening.VoidsElements) != 1 or len(opening.HasFillings) != 1 or opening.HasFillings[0].RelatedBuildingElement != peer:
            raise ValueError("public_opening_peer_void_fill_mismatch")
        relative = np.linalg.inv(matrix(peer, unit)) @ matrix(opening, unit)
        return {"preserve": False, "method": "peer", "mesh": _mesh(opening), "relative_frame": relative, "copy_base": target, "frame": target["frame"] @ relative}
    if cursor.text.startswith("洞口规格："):
        cursor.take("洞口规格：", "opening_spec_missing")
        position = _position(cursor, mode, host, unit, cache, prefix="洞口放置基点")
        shape = _shape(cursor, damaged, mode, unit, "IfcOpeningElement", prefix="洞口")
        orientation = _orientation(cursor, mode, host, unit, prefix="洞口")
        cursor.take("在宿主墙上建立洞口", "void_relationship_missing")
        cursor.take("并建立门窗填充关系。", "fill_relationship_missing")
        return {**shape, "preserve": False, **_set_frame({"position": position, "position_tolerance": target["position_tolerance"], "position_basis": target["position_basis"]}, orientation)}
    raise ValueError("opening_spec_missing")


def _target(row, damaged, mode, unit, cache):
    cursor = _Cursor(row)
    kind = cursor.take(r"\d+\. 补建一[扇根](门|窗|梁|柱)：", "target_class_missing")[1]
    cls = CLASSES[kind]
    located = _located(cursor, damaged, mode, unit, cache)
    shape = _shape(cursor, damaged, mode, unit, cls)
    orientation = _orientation(cursor, mode, located["host"], unit, peer=shape.get("peer"))
    result = {"class": cls, **shape, **_set_frame(located, orientation)}
    if cls in {"IfcDoor", "IfcWindow"}:
        result["opening"] = _opening(cursor, result, damaged, mode, unit, cache)
    elif "洞口" in cursor.text:
        raise ValueError("unexpected_opening_spec")
    cursor.finish()
    return result


def _angle_difference(left, right):
    return (np.asarray(left) - right + 180) % 360 - 180


def _orientation_close(spec, actual):
    if spec["angles"] is None:
        return _close(spec["rotation"], actual, EXACT_AXIS_TOLERANCE)
    relative = spec["base"].T @ actual
    pitch = math.asin(float(np.clip(-relative[2, 0], -1, 1)))
    tolerance = ANGLE_TOLERANCE_DEG + 1e-9
    if abs(math.cos(pitch)) > 1e-8:
        angles = np.degrees([math.atan2(relative[1, 0], relative[0, 0]), pitch, math.atan2(relative[2, 1], relative[2, 2])])
        alternatives = (angles, np.array([angles[0] + 180, 180 - angles[1], angles[2] + 180]))
        return any(np.all(np.abs(_angle_difference(values, spec["angles"])) <= tolerance) for values in alternatives)
    # At gimbal lock yaw and roll describe the same axis. Their combined
    # rounding uncertainty is two components; pitch remains an independent one.
    delta = spec["rotation"].T @ actual
    angle = math.degrees(math.acos(float(np.clip((np.trace(delta) - 1) / 2, -1, 1))))
    return abs(_angle_difference(math.degrees(pitch), spec["angles"][1])) <= tolerance and angle <= 2 * tolerance


def _position_close(parsed, actual):
    difference = parsed["position_basis"].T @ (parsed["position"] - actual)
    return _close(difference, np.zeros(3), parsed["position_tolerance"])


def _frame_matches(parsed, expected):
    return _position_close(parsed, expected[:3, 3]) and _orientation_close(parsed["orientation"], expected[:3, :3])


def _property(row, damaged, mode, unit, cache):
    cursor = _Cursor(row)
    cls = cursor.take(r"属性更改\d+：现有(Ifc\w+)，", "property_class_missing")[1]
    if cls not in CLASSES.values():
        raise ValueError("unsupported_property_class")
    located = _located(cursor, damaged, mode, unit, cache)
    orientation = _orientation(cursor, mode, located["host"], unit) if cursor.text.startswith("朝向") else None
    candidates = [entity for entity in damaged.by_type(cls) if _floor_of(entity) == located["floor"] and _position_close(located, matrix(entity, unit)[:3, 3]) and (located["host"] is None or _actual_host(entity) == located["host"]) and (orientation is None or _orientation_close(orientation, matrix(entity, unit)[:3, :3]))]
    if len(candidates) != 1:
        raise ValueError("property_target_not_unique_or_absent")
    entity = candidates[0]
    if orientation is None:
        axes = matrix(entity, unit)[:3, :3]
        orientation = {"rotation": axes, "base": axes, "angles": None}
    found = cursor.take(r"将实例属性「([^」]+)」改为(.*?)，保留其原属性类型。$", "property_path_or_value_missing")
    token = found[2]
    value = True if token == "是" else False if token == "否" else json.loads(token)
    if not isinstance(value, (bool, int, float, str)) or isinstance(value, float) and not math.isfinite(value):
        raise ValueError("property_restoration_value_invalid")
    cursor.finish()
    return {"class": cls, "entity": entity, "path": found[1], "value": value, "actual": _instance_property(entity, found[1]), **_set_frame(located, orientation)}


def _public_policy(text, mode, damaged, errors):
    rows = "\n".join(text.splitlines()[1:])
    if mode == "host_wall" and "世界" in rows or mode == "world" and re.search(r"宿主墙「|距墙长度起端|距墙厚度负向侧|高出墙底|相对宿主墙", rows):
        errors.append("mixed_locator_modes")
    if mode == "world":
        for match in re.finditer(r"「([^」]*)」", text):
            preceding = text[:match.start()]
            if not preceding.endswith(("楼层", "实例属性")):
                errors.append("world_name_leak")
        if re.search(r"(?:对象|构件|宿主墙|类型|参照)(?:名称|名字|名|GUID|GlobalId)", rows):
            errors.append("world_name_or_guid_leak")
    # Names and JSON strings keep their original digits. Only public numeric
    # fields, including numeric property values, have the three-decimal policy.
    masked = re.sub(r"「[^」]*」|\"(?:\\.|[^\"\\])*\"", "", text)
    if re.search(r"[-+]?\d+\.\d{4,}|\d+(?:\.\d+)?[eE][-+]?\d+", masked):
        errors.append("numeric_precision_exceeded")
    if re.search(r"多边形|几何实体|polygon|Ifc\w*(?:ProfileDef|AreaSolid|Brep)|外轮廓|拉伸参数", masked, re.IGNORECASE):
        errors.append("unsupported_geometry_description")
    if re.search(r"#\d+", text):
        errors.append("step_identity_leak")
    if re.search(r"\b(?:GUID|GlobalId)\b", masked) or any(entity.GlobalId and entity.GlobalId in text for entity in damaged.by_type("IfcRoot")):
        errors.append("object_guid_leak")


def parse_public_request(damaged_model, mode, text) -> dict:
    """Resolve a request using only public text and damaged IFC, without writes.

    Internal entities and arrays remain in this returned parsing record. The
    externally serializable audit report contains counts, errors and tolerances.
    """
    errors, targets, properties = [], [], []
    authorability = {"checked": 0, "passed": 0, "failed": 0, "methods": {}, "scope": "public door/window installation anchor or independently certified rigid basic box; separate from geometry equivalence"}
    result = {"passed": False, "errors": errors, "targets": targets, "properties": properties, "reference_authorability": authorability}
    if mode not in {"host_wall", "world"}:
        errors.append("unsupported_mode")
        return result
    if not isinstance(text, str) or not text.strip():
        errors.append("public_text_missing")
        return result
    damaged = ifcopenshell.open(str(damaged_model)) if isinstance(damaged_model, (str, Path)) else damaged_model
    unit = ifcopenshell.util.unit.calculate_unit_scale(damaged)
    lines = [line for line in text.splitlines() if line.strip()]
    if lines[0] != (HEADER if mode == "world" else NAME_HEADER):
        errors.append("units_or_numeric_policy_missing")
    if lines[-1] != FOOTER:
        errors.append("preservation_instruction_missing")
    _public_policy(text, mode, damaged, errors)
    target_rows = [line for line in lines[1:-1] if re.match(r"\d+\. ", line)]
    property_rows = [line for line in lines[1:-1] if line.startswith("属性更改")]
    for rows, pattern, code in ((target_rows, r"(\d+)\.", "target_row_numbering_invalid"), (property_rows, r"属性更改(\d+)：", "property_row_numbering_invalid")):
        numbering = [int(match[1]) if (match := re.match(pattern, line)) else None for line in rows]
        if numbering != list(range(1, len(rows) + 1)):
            errors.append(code)
    if not target_rows and not property_rows:
        errors.append("repair_operations_missing")
    if any(line not in target_rows and line not in property_rows for line in lines[1:-1]):
        errors.append("unparsed_request_line")
    cache = {}
    for label, rows, parser, values in (("target", target_rows, _target, targets), ("property", property_rows, _property, properties)):
        for index, row in enumerate(rows, 1):
            try:
                values.append(parser(row, damaged, mode, unit, cache))
            except Exception as exc:
                errors.append(f"{label}:{index}:{str(exc)[:120]}")
                values.append(None)
    result["errors"] = sorted(set(errors))
    result["passed"] = not errors
    methods = Counter(row["reference_authorability"] for row in targets if row is not None and row.get("reference_authorability"))
    authorability["passed"] = sum(methods.values())
    authorability["failed"] = sum("public_reference_not_authorable" in error for error in errors)
    authorability["checked"] = authorability["passed"] + authorability["failed"]
    authorability["methods"] = dict(methods)
    return result


def _box_certificate(entity):
    """Prove one rectangular extrusion is a closed axis-aligned local box.

    Eight corners, six boundary planes and areas, closed triangulated edges and
    volume are checked; the bounding box alone never proves a complete shape.
    """
    bodies = [rep for rep in entity.Representation.Representations if rep.RepresentationIdentifier == "Body"]
    if len(bodies) != 1 or len(bodies[0].Items) != 1:
        return False
    solid = bodies[0].Items[0]
    seen = set()
    while solid.is_a("IfcMappedItem"):
        if solid.id() in seen:
            return False
        seen.add(solid.id())
        transform = ifcopenshell.util.placement.get_mappeditem_transformation(solid)
        if transform is None:
            return False
        axes = np.asarray(transform, dtype=float)[:3, :3]
        if not _close(axes.T @ axes, np.eye(3), 1e-10) or not math.isclose(np.linalg.det(axes), 1, abs_tol=1e-10):
            return False
        items = solid.MappingSource.MappedRepresentation.Items
        if len(items) != 1:
            return False
        solid = items[0]
    if not solid.is_a("IfcExtrudedAreaSolid") or not solid.SweptArea.is_a("IfcRectangleProfileDef") or getattr(entity, "HasOpenings", ()):
        return False
    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), entity)
    vertices = np.asarray(shape.geometry.verts, dtype=float).reshape(-1, 3)
    faces = np.asarray(shape.geometry.faces, dtype=int).reshape(-1, 3)
    if not len(vertices) or not len(faces) or not np.isfinite(vertices).all():
        return False
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    dimensions = high - low
    tolerance = 1e-8
    if np.any(dimensions <= tolerance):
        return False
    corners = np.array(list(product(*zip(low, high))))
    if not all(np.any(np.all(np.abs(vertices - corner) <= tolerance, axis=1)) for corner in corners):
        return False
    areas, edges, volume = np.zeros((3, 2)), Counter(), 0.0
    for face in faces:
        triangle = vertices[face]
        normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
        area = np.linalg.norm(normal) / 2
        planes = [(axis, side) for axis in range(3) for side, boundary in enumerate((low[axis], high[axis])) if np.all(np.abs(triangle[:, axis] - boundary) <= tolerance)]
        if area <= tolerance * tolerance or len(planes) != 1:
            return False
        areas[planes[0]] += area
        # Translate to the local lower corner to avoid a far-origin cancellation.
        a, b, c = triangle - low
        volume += np.dot(a, np.cross(b, c)) / 6
        keys = [tuple(np.round(vertex, 9)) for vertex in triangle]
        edges.update(tuple(sorted((keys[index], keys[(index + 1) % 3]))) for index in range(3))
    expected_areas = np.array([dimensions[1] * dimensions[2], dimensions[0] * dimensions[2], dimensions[0] * dimensions[1]])
    return all(count == 2 for count in edges.values()) and _close(areas, expected_areas[:, None], 1e-8) and math.isclose(abs(volume), float(np.prod(dimensions)), rel_tol=1e-8, abs_tol=1e-10)


def _shape_matches(parsed, entity):
    if parsed["method"] == "peer":
        return parsed["mesh"] == _mesh(entity)
    bounds = _bounds(entity)
    return _close(parsed["dimensions"], bounds[1] - bounds[0], MM_TOLERANCE_M) and _close(parsed["offsets"], -bounds[0], MM_TOLERANCE_M) and _box_certificate(entity)


def _usable_peer(damaged, cls, mesh, mode, unit):
    peers = damaged.by_type(cls)
    for entity in peers:
        try:
            if _mesh(entity) != mesh:
                continue
            _reference_authorability(entity)
            if mode == "world":
                printed = np.round(matrix(entity, unit)[:3, 3], 3)
                matches = [peer for peer in peers if _close(matrix(peer, unit)[:3, 3], printed, WORLD_TOLERANCE_M)]
            else:
                floor = _floor_of(entity)
                if floor is None or not floor.Name or not entity.Name:
                    continue
                if len([item for item in damaged.by_type("IfcBuildingStorey") if item.Name == floor.Name]) != 1:
                    continue
                matches = [peer for peer in peers if peer.Name == entity.Name and _floor_of(peer) == floor]
            if len(matches) == 1:
                return True
        except (ValueError, RuntimeError):
            continue
    return False


def _same_value(left, right):
    return type(left) is type(right) and left == right


def _restored_value(value, expected):
    if isinstance(expected, float) and isinstance(value, (int, float)) and not isinstance(value, bool):
        return math.isfinite(value) and abs(value - expected) <= 0.0005 + 1e-9
    return _same_value(value, expected)


def audit_prompt(reference_model, damaged_model, manifest, mode, text) -> dict:
    """Resolve publicly first, then compare with evaluator-only reference facts."""
    checks = {key: 0 for key in ("target_placements", "target_meshes", "host_locators", "floor_memberships", "openings", "properties")}
    public = parse_public_request(damaged_model, mode, text)
    errors = list(public["errors"])
    result = {"checker_version": CHECKER_VERSION, "request_profile": PROFILE, "mode": mode, "passed": False, "errors": errors, "checks": checks, "scope": SCOPE, "public_resolution_passed": public["passed"], "private_comparison_performed": False, "reference_authorability": public["reference_authorability"],
              "numeric_tolerances": {"world_position_or_bounds_axis_m": WORLD_TOLERANCE_M, "wall_relative_position_axis_m": MM_TOLERANCE_M, "basic_dimension_or_offset_axis_m": MM_TOLERANCE_M, "angle_component_deg": ANGLE_TOLERANCE_DEG, "angle_axis_matrix_propagation_max_abs": 3 * math.radians(ANGLE_TOLERANCE_DEG), "peer_mesh_quantization_m": 0.000001}}
    if not public["passed"]:
        return result
    result["private_comparison_performed"] = True
    damaged = ifcopenshell.open(str(damaged_model)) if isinstance(damaged_model, (str, Path)) else damaged_model
    reference = ifcopenshell.open(str(reference_model)) if isinstance(reference_model, (str, Path)) else reference_model
    unit, ref_unit = ifcopenshell.util.unit.calculate_unit_scale(damaged), ifcopenshell.util.unit.calculate_unit_scale(reference)
    if any(entity.GlobalId and entity.GlobalId in text for entity in reference.by_type("IfcRoot")):
        errors.append("object_guid_leak")
    targets, changes = manifest.get("deletions", []), manifest.get("property_changes", [])
    if len(targets) != len(public["targets"]):
        errors.append("target_count_mismatch")
    if len(changes) != len(public["properties"]):
        errors.append("property_count_mismatch")
    for index, (parsed, target) in enumerate(zip(public["targets"], targets), 1):
        prefix = f"target:{index}:"
        try:
            entity = reference.by_guid(target["guid"])
            if parsed["class"] != entity.is_a() or target["ifc_class"] != entity.is_a():
                errors.append(prefix + "target_class_mismatch")
            if any(item.GlobalId == entity.GlobalId for item in damaged.by_type(entity.is_a())):
                errors.append(prefix + "target_not_deleted")
            if not _frame_matches(parsed, matrix(entity, ref_unit)):
                errors.append(prefix + "placement_or_axes_mismatch")
            checks["target_placements"] += 1
            if not _shape_matches(parsed, entity):
                errors.append(prefix + "target_geometry_mismatch")
            if parsed["method"] == "box" and _usable_peer(damaged, entity.is_a(), _mesh(entity), mode, unit):
                errors.append(prefix + "basic_shape_surviving_peer_available")
            checks["target_meshes"] += 1
            floor = _floor_of(entity)
            if floor is None or parsed["floor"].GlobalId != floor.GlobalId or target["storey"]["guid"] != floor.GlobalId:
                errors.append(prefix + "floor_membership_mismatch")
            checks["floor_memberships"] += 1
            host = _actual_host(entity)
            if (host is None) != (parsed["host"] is None) or host is not None and host.GlobalId != parsed["host"].GlobalId:
                errors.append(prefix + "wall_host_mismatch")
            if parsed["host"] is not None:
                checks["host_locators"] += 1
            if parsed["class"] in {"IfcDoor", "IfcWindow"}:
                if len(entity.FillsVoids) != 1:
                    raise ValueError("source_opening_not_unique")
                expected = entity.FillsVoids[0].RelatingOpeningElement
                opening = parsed["opening"]
                if len(expected.VoidsElements) != 1 or host is None or expected.VoidsElements[0].RelatingBuildingElement.GlobalId != parsed["host"].GlobalId:
                    errors.append(prefix + "opening_void_binding_mismatch")
                if target.get("opening_guid") != expected.GlobalId or opening["preserve"] != target.get("preserve_opening", True):
                    errors.append(prefix + "opening_binding_or_mode_mismatch")
                expected_frame = matrix(expected, ref_unit)
                placement_ok = _frame_matches(opening["copy_base"], expected_frame @ np.linalg.inv(opening["relative_frame"])) if "copy_base" in opening else _frame_matches(opening, expected_frame)
                if not placement_ok:
                    errors.append(prefix + "opening_placement_or_axes_mismatch")
                if not _shape_matches(opening, expected):
                    errors.append(prefix + "opening_geometry_mismatch")
                if opening["method"] == "box" and parsed["method"] == "peer" and len(parsed["peer"].FillsVoids) == 1:
                    peer = parsed["peer"]
                    peer_opening = peer.FillsVoids[0].RelatingOpeningElement
                    peer_relative = np.linalg.inv(matrix(peer, unit)) @ matrix(peer_opening, unit)
                    source_relative = np.linalg.inv(matrix(entity, ref_unit)) @ expected_frame
                    if _mesh(peer_opening) == _mesh(expected) and _close(peer_relative, source_relative, 1e-8):
                        errors.append(prefix + "basic_opening_copy_available")
                if opening["preserve"] and opening["entity"].GlobalId != expected.GlobalId:
                    errors.append(prefix + "retained_opening_identity_mismatch")
                if not opening["preserve"] and any(item.GlobalId == expected.GlobalId for item in damaged.by_type("IfcOpeningElement")):
                    errors.append(prefix + "removed_opening_still_present")
                checks["openings"] += 1
        except Exception as exc:
            errors.append(prefix + "reference_comparison_unverified:" + str(exc)[:120])
    for index, (parsed, change) in enumerate(zip(public["properties"], changes), 1):
        prefix = f"property:{index}:"
        try:
            source = reference.by_guid(change["guid"])
            path = change["pset_name"] + "." + change["property_name"]
            before_type, before_value = _instance_property(source, path)
            after_type, after_value = parsed["actual"]
            if parsed["entity"].GlobalId != source.GlobalId or parsed["class"] != source.is_a() or parsed["path"] != path:
                errors.append(prefix + "property_identity_or_path_mismatch")
            if not _frame_matches(parsed, matrix(source, ref_unit)):
                errors.append(prefix + "property_placement_or_axes_mismatch")
            if _floor_of(source) is None or _floor_of(source).GlobalId != parsed["floor"].GlobalId:
                errors.append(prefix + "property_floor_membership_mismatch")
            host = _actual_host(source)
            if (host is None) != (parsed["host"] is None) or host is not None and host.GlobalId != parsed["host"].GlobalId:
                errors.append(prefix + "property_wall_host_mismatch")
            if before_type != after_type or before_type != change["value_type"]:
                errors.append(prefix + "property_type_mismatch")
            if not _same_value(before_value, change["before"]) or not _same_value(after_value, change["after"]):
                errors.append(prefix + "property_before_or_after_mismatch")
            if not _restored_value(parsed["value"], before_value):
                errors.append(prefix + "property_restoration_value_mismatch")
            checks["floor_memberships"] += 1
            if parsed["host"] is not None:
                checks["host_locators"] += 1
            checks["properties"] += 1
        except Exception as exc:
            errors.append(prefix + "reference_comparison_unverified:" + str(exc)[:120])
    result["errors"] = sorted(set(errors))
    result["passed"] = not errors
    return result
