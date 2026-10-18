"""Independent, read-only audit of the actual public profile-1.2 request.

Public resolution and geometry construction use only the text and damaged IFC.
Private identities are consulted afterwards to compare the resolved result with
the preassigned reference. This is an information-sufficiency check, not a repair
execution or a check of every original semantic field.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
import numpy as np

from scripts.ifc_repair.audit_initial_dataset import NUMBER, POINT, _mesh, geometry_from_text, matrix, point, points

CLASSES = {"门": "IfcDoor", "窗": "IfcWindow", "梁": "IfcBeam", "柱": "IfcColumn"}
CHECKER_VERSION = "text2ifc/dataset-prompt-check/1.1"
TOLERANCE_M = 0.000003
AXIS_TOLERANCE = 0.000002
SCOPE = "actual public text and surviving public anchors; specified local mesh, placement, floor, host, opening/void/fill and instance-property restoration; no Provider, repair execution or all-semantic-field equivalence"


def _one(pattern, text, code):
    found = list(re.finditer(pattern, text, re.DOTALL))
    if len(found) != 1:
        raise ValueError(code)
    return found[0]


def _vector(token):
    value = point(token)
    if value.shape != (3,) or not np.isfinite(value).all():
        raise ValueError("invalid_public_vector")
    return value


def _axes(text):
    tokens = re.findall(POINT, text)
    if len(tokens) != 3:
        raise ValueError("public_axes_missing_or_incomplete")
    axes = np.asarray([_vector(token) for token in tokens]).T
    if not np.allclose(axes.T @ axes, np.eye(3), atol=AXIS_TOLERANCE, rtol=0) or not np.isclose(np.linalg.det(axes), 1, atol=AXIS_TOLERANCE, rtol=0):
        raise ValueError("public_axes_not_orthonormal")
    return axes


def _close(left, right):
    return np.allclose(left, right, atol=TOLERANCE_M, rtol=0)


def _floor_of(entity):
    if len(getattr(entity, "ContainedInStructure", ())) > 1:
        raise ValueError("actual_container_ambiguous")
    floor = ifcopenshell.util.element.get_container(entity, ifc_class="IfcBuildingStorey")
    return floor


def _floor(model, name):
    matches = [item for item in model.by_type("IfcBuildingStorey") if item.Name == name]
    if len(matches) != 1:
        raise ValueError("storey_not_unique_or_absent")
    return matches[0]


def _bounds(entity, *, world=False, uncut=False):
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", world)
    settings.set("disable-opening-subtractions", uncut)
    shape = ifcopenshell.geom.create_shape(settings, entity)
    vertices = np.asarray(shape.geometry.verts, dtype=float).reshape(-1, 3)
    if not len(vertices) or not np.isfinite(vertices).all():
        raise ValueError("mesh_unavailable")
    return np.asarray([vertices.min(axis=0), vertices.max(axis=0)])


def _world_frame(text, prefix, *, separator="。"):
    found = _one(re.escape(prefix) + POINT + r"米" + re.escape(separator) + r"世界X/Y/Z轴分别为(.*?)。", text, "placement_or_axes_missing")
    frame = np.eye(4)
    frame[:3, 3] = _vector(found[1])
    frame[:3, :3] = _axes(found[2])
    return frame


def _host_frame(text, prefix, host, unit):
    found = _one(re.escape(prefix) + r"相对墙自身放置原点，沿墙自身X方向距离(" + NUMBER + r")米，Y方向距离(" + NUMBER + r")米，Z方向距离(" + NUMBER + r")米。构件自身X/Y/Z轴相对墙自身坐标系的方向分别为(.*?)。", text, "placement_or_axes_missing")
    frame = np.eye(4)
    frame[:3, 3] = [float(found[i]) for i in (1, 2, 3)]
    if not np.isfinite(frame).all():
        raise ValueError("invalid_public_vector")
    frame[:3, :3] = _axes(found[4])
    return matrix(host, unit) @ frame


def _wall(text, model, floor, mode, unit, cache):
    if mode == "host_wall":
        name = _one(r"宿主墙「([^」]+)」", text, "wall_host_missing")[1]
        matches = [wall for wall in model.by_type("IfcWall") if wall.Name == name and _floor_of(wall) == floor]
    else:
        frame = _world_frame(text, "宿主墙世界原点为", separator="，")
        bounds = _one(r"宿主墙未扣洞口的世界外包范围下角点为" + POINT + r"米，上角点为" + POINT + r"米。", text, "wall_bounds_missing")
        expected = np.asarray([_vector(bounds[1]), _vector(bounds[2])])
        if np.any(expected[0] >= expected[1]):
            raise ValueError("wall_bounds_invalid")
        matches = []
        # Search every damaged wall, without a private ID or a Name fallback.
        for wall in model.by_type("IfcWall"):
            if _close(matrix(wall, unit), frame):
                if wall.id() not in cache:
                    cache[wall.id()] = _bounds(wall, world=True, uncut=True)
                if _close(cache[wall.id()], expected):
                    matches.append(wall)
    if len(matches) != 1:
        raise ValueError("wall_not_unique_or_absent")
    # A wall may span floors while its window has a different containment.
    # World origin/axes/bounds identify that wall independently of target floor.
    if mode == "host_wall" and _floor_of(matches[0]) != floor:
        raise ValueError("wall_floor_membership_mismatch")
    return matches[0]


def _public_peer(text, damaged, mode, unit):
    suffix = r"复制其自身局部几何，再按本条指定原点和轴放置。"
    if mode == "world":
        found = _one(r"几何形状逐项复制模型中仍存在的(Ifc\w+)，参考实例世界原点为" + POINT + r"米，世界X/Y/Z轴分别为(.*?)。" + suffix, text, "public_peer_locator_missing")
        origin, axes = _vector(found[2]), _axes(found[3])
        matches = [entity for entity in damaged.by_type(found[1]) if _close(matrix(entity, unit)[:3, 3], origin) and _close(matrix(entity, unit)[:3, :3], axes)]
    else:
        filled = re.search(r"几何形状逐项复制楼层「([^」]+)」中现存(Ifc\w+)「([^」]+)」所填充的洞口。" + suffix, text)
        if filled:
            floor = _floor(damaged, filled[1])
            fillings = [entity for entity in damaged.by_type(filled[2]) if entity.Name == filled[3] and _floor_of(entity) == floor]
            if len(fillings) != 1 or len(getattr(fillings[0], "FillsVoids", ())) != 1:
                raise ValueError("public_peer_not_unique_or_absent")
            matches = [fillings[0].FillsVoids[0].RelatingOpeningElement]
        else:
            found = _one(r"几何形状逐项复制楼层「([^」]+)」中仍存在的(Ifc\w+)「([^」]+)」。" + suffix, text, "public_peer_locator_missing")
            floor = _floor(damaged, found[1])
            matches = [entity for entity in damaged.by_type(found[2]) if entity.Name == found[3] and _floor_of(entity) == floor]
    if len(matches) != 1:
        raise ValueError("public_peer_not_unique_or_absent")
    # Reading a mesh establishes that the publicly selected instance still has a body.
    _mesh(matches[0])
    return None, matches[0]


def _body(text, damaged, mode, unit):
    copies = text.count("几何形状逐项复制")
    count = len(re.findall(r"几何实体\d+采用", text))
    if copies:
        if copies != 1 or count:
            raise ValueError("body_description_ambiguous")
        return _public_peer(text, damaged, mode, unit)
    chunks = list(re.finditer(r"几何实体(\d+)采用.*?沿实体坐标方向" + POINT + r"拉伸(" + NUMBER + r")毫米。", text))
    if not chunks:
        raise ValueError("complete_geometry_not_described")
    if count != len(chunks) or [int(chunk[1]) for chunk in chunks] != list(range(1, len(chunks) + 1)):
        raise ValueError("complete_geometry_items_missing_or_ambiguous")
    for chunk in chunks:
        solid = _one(r"实体坐标原点在构件自身坐标中为(.*?)；截面原点", chunk[0], "extrusion_frame_missing")
        profile = _one(r"截面原点在实体坐标中为(.*?)；沿实体坐标方向", chunk[0], "profile_frame_missing")
        sf, pf = points(solid[1]), points(profile[1])
        if len(sf) != 4 or len(pf) != 3 or any(value.shape != (3,) or not np.isfinite(value).all() for value in [*sf, *pf]):
            raise ValueError("extrusion_axes_incomplete")
        _axes("、".join("（" + ",".join(map(str, value)) + "）" for value in sf[1:]))
        pa = np.asarray([pf[1], pf[2], [0, 0, 1]]).T
        if not np.allclose(pa.T @ pa, np.eye(3), atol=AXIS_TOLERANCE, rtol=0) or not np.isclose(np.linalg.det(pa), 1, atol=AXIS_TOLERANCE, rtol=0) or abs(pf[0][2]) > AXIS_TOLERANCE:
            raise ValueError("profile_axes_mismatch")
        if "IfcArbitrary" in chunk[0] and (not _close(pf[0], np.zeros(3)) or not _close(pa, np.eye(3))):
            # These profile classes have no Position in IFC; the polygon itself
            # supplies its coordinates. The shared builder does not apply one.
            raise ValueError("profile_axes_mismatch")
        direction = _vector(chunk[2])
        if not np.isclose(np.linalg.norm(direction), 1, atol=AXIS_TOLERANCE, rtol=0) or not math.isfinite(float(chunk[3])) or float(chunk[3]) <= 0:
            raise ValueError("extrusion_direction_or_depth_invalid")
    return geometry_from_text(text)


def _located_row(text, damaged, mode, unit, cache):
    floor = _floor(damaged, _one(r"归属楼层「([^」]+)」。", text, "storey_membership_missing")[1])
    host = _wall(text, damaged, floor, mode, unit, cache) if mode == "host_wall" or "宿主墙" in text else None
    if mode == "host_wall":
        if host is None:
            raise ValueError("wall_host_missing")
        frame = _host_frame(text, "放置原点", host, unit)
    else:
        frame = _world_frame(text, "放置原点的世界坐标为")
    return {"floor": floor, "host": host, "frame": frame}


def _parse_target(text, damaged, mode, unit, cache):
    kind = _one(r"^\d+\. 补建一[扇根](门|窗|梁|柱)：", text, "target_class_missing")[1]
    product_text = text.split("洞口规格开始：", 1)[0]
    result = {"class": CLASSES[kind], **_located_row(product_text, damaged, mode, unit, cache)}
    bounds = _one(r"自身坐标的外包范围下角点为" + POINT + r"毫米，上角点为" + POINT + r"毫米。", product_text, "target_bounds_missing")
    result["bounds"] = np.asarray([_vector(bounds[1]), _vector(bounds[2])]) / 1000
    if np.any(result["bounds"][0] >= result["bounds"][1]):
        raise ValueError("target_bounds_invalid")
    # Keep the temporary geometry model alive until mesh creation is complete.
    geometry_model, product = _body(product_text, damaged, mode, unit)
    result["mesh"] = _mesh(product)
    if not _close(result["bounds"], _bounds(product)):
        raise ValueError("target_bounds_geometry_mismatch")
    if kind not in {"门", "窗"}:
        if "洞口规格" in text:
            raise ValueError("unexpected_opening_spec")
        return result
    if result["host"] is None:
        raise ValueError("wall_host_missing")
    opening_text = _one(r"洞口规格开始：(.*?)洞口规格结束。", text, "opening_spec_missing")[1]
    opening = {"frame": _world_frame(opening_text, "洞口世界原点为") if mode == "world" else _host_frame(opening_text, "洞口原点", result["host"], unit)}
    if "门窗填充关系" not in opening_text:
        raise ValueError("fill_relationship_missing")
    opening["preserve"] = "保留现有洞口" in opening_text
    if opening["preserve"]:
        if "将新门窗填入该洞口" not in opening_text or "void关系" in opening_text or "几何实体" in opening_text or "几何形状逐项复制" in opening_text:
            raise ValueError("retained_opening_instruction_ambiguous")
        matches = [rel.RelatedOpeningElement for rel in result["host"].HasOpenings if _close(matrix(rel.RelatedOpeningElement, unit), opening["frame"])]
        if len(matches) != 1:
            raise ValueError("retained_opening_not_unique_or_absent")
        opening["entity"] = matches[0]
        opening["mesh"] = _mesh(matches[0])
        if len(matches[0].VoidsElements) != 1 or matches[0].VoidsElements[0].RelatingBuildingElement != result["host"]:
            raise ValueError("retained_opening_void_binding_mismatch")
    else:
        if "在上述宿主墙上建立新洞口的void关系" not in opening_text:
            raise ValueError("void_relationship_missing")
        geometry_model, product = _body(opening_text, damaged, mode, unit)
        opening["mesh"] = _mesh(product)
    result["opening"] = opening
    return result


def _instance_property(entity, path):
    matches = [(pset, prop) for rel in getattr(entity, "IsDefinedBy", ()) if rel.is_a("IfcRelDefinesByProperties") and (pset := rel.RelatingPropertyDefinition).is_a("IfcPropertySet") for prop in pset.HasProperties if str(pset.Name) + "." + str(prop.Name) == path]
    if len(matches) != 1 or not matches[0][1].is_a("IfcPropertySingleValue") or matches[0][1].NominalValue is None:
        raise ValueError("instance_property_not_unique_or_absent")
    value = matches[0][1].NominalValue
    return value.is_a(), value.wrappedValue


def _actual_host(entity):
    fills = getattr(entity, "FillsVoids", ())
    if len(fills) != 1 or len(fills[0].RelatingOpeningElement.VoidsElements) != 1:
        return None
    return fills[0].RelatingOpeningElement.VoidsElements[0].RelatingBuildingElement


def _parse_property(text, damaged, mode, unit, cache):
    kind = _one(r"^属性更改\d+：现有(Ifc\w+)，", text, "property_class_missing")[1]
    located = _located_row(text, damaged, mode, unit, cache)
    candidates = [entity for entity in damaged.by_type(kind) if _close(matrix(entity, unit), located["frame"]) and _floor_of(entity) == located["floor"] and (located["host"] is None or _actual_host(entity) == located["host"])]
    if len(candidates) != 1:
        raise ValueError("property_target_not_unique_or_absent")
    found = _one(r"将实例属性「([^」]+)」改为(.*?)，保留其原属性类型。$", text, "property_path_or_value_missing")
    token = found[2]
    value = True if token == "是" else False if token == "否" else json.loads(token)
    if not isinstance(value, (bool, int, float, str)) or isinstance(value, float) and not math.isfinite(value):
        raise ValueError("property_restoration_value_invalid")
    return {**located, "class": kind, "entity": candidates[0], "path": found[1], "value": value, "actual": _instance_property(candidates[0], found[1])}


def _same_value(left, right):
    return type(left) is type(right) and left == right


def _public_policy(text, mode, damaged, errors):
    if mode == "host_wall" and "世界" in text:
        errors.append("mixed_locator_modes")
    if mode == "world":
        for match in re.finditer(r"「([^」]*)」", text):
            preceding = text[:match.start()]
            if not preceding.endswith("楼层") and not preceding.endswith("实例属性"):
                errors.append("world_name_leak")
        if "相对墙自身放置原点" in text:
            errors.append("mixed_locator_modes")
        if re.search(r"(?:对象|构件|宿主墙|类型|参考实例)(?:名称|名字|名|GUID|GlobalId)", text):
            errors.append("world_name_or_guid_leak")
    if any(entity.GlobalId and entity.GlobalId in text for entity in damaged.by_type("IfcRoot")):
        errors.append("object_guid_leak")


def audit_prompt(reference_model, damaged_model, manifest, mode, text) -> dict:
    """Parse public instructions, resolve damaged anchors, then compare privately.

    Geometry comparison uses unordered local triangles quantized to one micrometre
    and placement tolerance of three micrometres. No input IFC is modified.
    """
    errors = []
    checks = {key: 0 for key in ("target_placements", "target_meshes", "host_locators", "floor_memberships", "openings", "properties")}
    result = {"checker_version": CHECKER_VERSION, "mode": mode, "passed": False, "errors": errors, "checks": checks, "scope": SCOPE}
    if mode not in {"host_wall", "world"}:
        errors.append("unsupported_mode")
        return result
    if not isinstance(text, str) or not text.strip():
        errors.append("public_text_missing")
        return result
    damaged = ifcopenshell.open(str(damaged_model)) if isinstance(damaged_model, (str, Path)) else damaged_model
    unit = ifcopenshell.util.unit.calculate_unit_scale(damaged)
    if "距离和放置坐标单位为米，几何尺寸单位为毫米。" not in text:
        errors.append("units_missing")
    if mode == "world" and "世界坐标采用IFC模型的项目放置坐标系。" not in text:
        errors.append("world_coordinate_system_missing")
    if "除以上补建、洞口关系及指定实例属性外，其余构件、楼层、尺寸、位置、类型和材料保持原样。" not in text:
        errors.append("preservation_instruction_missing")
    _public_policy(text, mode, damaged, errors)
    lines = [line for line in text.splitlines() if line.strip()]
    target_rows = [line for line in lines if re.match(r"\d+\. ", line)]
    property_rows = [line for line in lines if line.startswith("属性更改")]
    if [int(re.match(r"(\d+)\.", line)[1]) for line in target_rows] != list(range(1, len(target_rows) + 1)):
        errors.append("target_row_numbering_invalid")
    if not any(target_rows) and not any(property_rows):
        errors.append("repair_operations_missing")
    for line in lines:
        if line not in target_rows and line not in property_rows and not line.startswith(("请按以下要求修复模型。", "除以上补建、洞口关系及指定实例属性外，")):
            errors.append("unparsed_request_line")

    # This complete public phase never reads mutation identities, recipes, or Gold.
    parsed_targets, parsed_properties, cache = [], [], {}
    for label, rows, parser, values in (("target", target_rows, _parse_target, parsed_targets), ("property", property_rows, _parse_property, parsed_properties)):
        for index, row in enumerate(rows, 1):
            try:
                values.append(parser(row, damaged, mode, unit, cache))
            except Exception as exc:
                errors.append(f"{label}:{index}:{str(exc)[:120]}")
                values.append(None)

    reference = ifcopenshell.open(str(reference_model)) if isinstance(reference_model, (str, Path)) else reference_model
    ref_unit = ifcopenshell.util.unit.calculate_unit_scale(reference)
    if any(entity.GlobalId and entity.GlobalId in text for entity in reference.by_type("IfcRoot")):
        errors.append("object_guid_leak")
    targets, changes = manifest.get("deletions", []), manifest.get("property_changes", [])
    if len(targets) != len(target_rows):
        errors.append("target_count_mismatch")
    if len(changes) != len(property_rows):
        errors.append("property_count_mismatch")
    for index, (parsed, target) in enumerate(zip(parsed_targets, targets), 1):
        if parsed is None:
            continue
        prefix = f"target:{index}:"
        try:
            entity = reference.by_guid(target["guid"])
            if parsed["class"] != entity.is_a() or target["ifc_class"] != entity.is_a():
                errors.append(prefix + "target_class_mismatch")
            if any(item.GlobalId == entity.GlobalId for item in damaged.by_type(entity.is_a())):
                errors.append(prefix + "target_not_deleted")
            if not _close(parsed["frame"], matrix(entity, ref_unit)):
                errors.append(prefix + "placement_or_axes_mismatch")
            checks["target_placements"] += 1
            if parsed["mesh"] != _mesh(entity) or not _close(parsed["bounds"], _bounds(entity)):
                errors.append(prefix + "target_geometry_mismatch")
            checks["target_meshes"] += 1
            source_floor = _floor_of(entity)
            if source_floor is None or parsed["floor"].GlobalId != source_floor.GlobalId or target["storey"]["guid"] != source_floor.GlobalId:
                errors.append(prefix + "floor_membership_mismatch")
            checks["floor_memberships"] += 1
            source_host = _actual_host(entity)
            if (source_host is None) != (parsed["host"] is None) or source_host is not None and source_host.GlobalId != parsed["host"].GlobalId:
                errors.append(prefix + "wall_host_mismatch")
            if parsed["host"] is not None:
                checks["host_locators"] += 1
            if parsed["class"] in {"IfcDoor", "IfcWindow"}:
                fills = entity.FillsVoids
                if len(fills) != 1:
                    raise ValueError("source_opening_not_unique")
                expected = fills[0].RelatingOpeningElement
                opening = parsed["opening"]
                if target.get("opening_guid") != expected.GlobalId or opening["preserve"] != target.get("preserve_opening", True):
                    errors.append(prefix + "opening_binding_or_mode_mismatch")
                if not _close(opening["frame"], matrix(expected, ref_unit)):
                    errors.append(prefix + "opening_placement_or_axes_mismatch")
                if opening["mesh"] != _mesh(expected):
                    errors.append(prefix + "opening_geometry_mismatch")
                if opening["preserve"] and opening["entity"].GlobalId != expected.GlobalId:
                    errors.append(prefix + "retained_opening_identity_mismatch")
                if not opening["preserve"] and any(item.GlobalId == expected.GlobalId for item in damaged.by_type("IfcOpeningElement")):
                    errors.append(prefix + "removed_opening_still_present")
                checks["openings"] += 1
        except Exception as exc:
            errors.append(prefix + "reference_comparison_unverified:" + str(exc)[:120])
    for index, (parsed, change) in enumerate(zip(parsed_properties, changes), 1):
        if parsed is None:
            continue
        prefix = f"property:{index}:"
        try:
            source = reference.by_guid(change["guid"])
            path = change["pset_name"] + "." + change["property_name"]
            before_type, before_value = _instance_property(source, path)
            after_type, after_value = parsed["actual"]
            if parsed["entity"].GlobalId != source.GlobalId or parsed["class"] != source.is_a() or parsed["path"] != path:
                errors.append(prefix + "property_identity_or_path_mismatch")
            if not _close(parsed["frame"], matrix(source, ref_unit)):
                errors.append(prefix + "property_placement_or_axes_mismatch")
            if _floor_of(source) is None or _floor_of(source).GlobalId != parsed["floor"].GlobalId:
                errors.append(prefix + "property_floor_membership_mismatch")
            if parsed["host"] is not None and (_actual_host(source) is None or _actual_host(source).GlobalId != parsed["host"].GlobalId):
                errors.append(prefix + "property_wall_host_mismatch")
            if before_type != after_type or before_type != change["value_type"]:
                errors.append(prefix + "property_type_mismatch")
            if not _same_value(before_value, change["before"]) or not _same_value(after_value, change["after"]):
                errors.append(prefix + "property_before_or_after_mismatch")
            if not _same_value(parsed["value"], before_value):
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
