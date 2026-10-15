"""Read-only, fresh IFC validation and independently parsed public-task checks.

This checker does not regenerate prompts or treat a bounding box as full geometry.
It reconstructs supported extrusion bodies from the actual text, or resolves the
text's surviving reference against the damaged IFC. No Provider calls are made.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path[:0] = [str(ROOT), str(ROOT / "src")]

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from scripts.ifc_repair.dataset_batch.engine import verify_seal, write_json
from scripts.ifc_repair.dataset_batch.sampling import inspect_case
from scripts.ifc_repair.dataset_batch.validation import native_validate, sha256, verify_case

NUMBER = r"[-+0-9.eE]+"
POINT = r"[（(]([^）)]+)[）)]"


def point(token):
    return np.asarray([float(x) for x in token.replace("，", ",").split(",")])


def points(text):
    return [point(token) for token in re.findall(POINT, text)]


def matrix(product, unit):
    frame = np.asarray(ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement), dtype=float)
    frame[:3, 3] *= unit
    return frame


def _axis(model, origin, axes):
    return model.createIfcAxis2Placement3D(model.createIfcCartesianPoint(tuple(float(x) for x in origin)), model.createIfcDirection(tuple(float(x) for x in axes[2])), model.createIfcDirection(tuple(float(x) for x in axes[0])))


def geometry_from_text(text):
    """Build a metre-unit geometry fixture using only parameters parsed in text."""
    # POINT contains a capture; use complete match rather than re.findall tuples.
    chunks = [match[0] for match in re.finditer(r"几何实体\d+采用.*?沿实体坐标方向" + POINT + r"拉伸" + NUMBER + r"毫米。", text)]
    if not chunks:
        raise ValueError("complete_geometry_not_described")
    model = ifcopenshell.file(schema="IFC2X3")
    axes = np.eye(3)
    context = model.createIfcGeometricRepresentationContext(None, "Model", 3, 1e-7, _axis(model, np.zeros(3), axes), None)
    items = []
    for chunk in chunks:
        kind = re.search(r"截面（(Ifc[A-Za-z0-9]+)）", chunk)
        if not kind:
            raise ValueError("profile_class_missing")
        values = {key: float(value) * (0.001 if unit == "毫米" else 1) for key, value, unit in re.findall(r"([A-Za-z0-9]+)=(" + NUMBER + r")(毫米|弧度)", chunk)}
        radius = re.search(r"半径(" + NUMBER + r")毫米", chunk)
        if radius:
            values["Radius"] = float(radius[1]) / 1000
        solid_part = re.search(r"实体坐标原点在构件自身坐标中为(.*?)；截面原点", chunk)
        profile_part = re.search(r"截面原点在实体坐标中为(.*?)；沿实体坐标方向", chunk)
        extrusion = re.search(r"沿实体坐标方向" + POINT + r"拉伸(" + NUMBER + r")毫米", chunk)
        if not (solid_part and profile_part and extrusion):
            raise ValueError("extrusion_frame_missing")
        sframe, pframe = points(solid_part[1]), points(profile_part[1])
        if len(sframe) != 4 or len(pframe) != 3:
            raise ValueError("extrusion_axes_incomplete")
        if kind[1] in {"IfcArbitraryClosedProfileDef", "IfcArbitraryProfileDefWithVoids"}:
            polygon = re.search(r"外轮廓及内孔依次为(\[.*?\])毫米；", chunk)
            if not polygon:
                raise ValueError("profile_polygon_missing")
            curves = [model.createIfcPolyline([model.createIfcCartesianPoint(tuple(float(v) / 1000 for v in vertex)) for vertex in contour]) for contour in json.loads(polygon[1])]
            kwargs = {"OuterCurve": curves[0]}
            if kind[1] == "IfcArbitraryProfileDefWithVoids":
                kwargs["InnerCurves"] = curves[1:]
        else:
            kwargs = {"Position": model.createIfcAxis2Placement2D(model.createIfcCartesianPoint(tuple(float(v) / 1000 for v in pframe[0][:2])), model.createIfcDirection(tuple(float(v) for v in pframe[1][:2]))), **values}
        profile = model.create_entity(kind[1], ProfileType="AREA", **kwargs)
        items.append(model.createIfcExtrudedAreaSolid(profile, _axis(model, sframe[0] / 1000, sframe[1:]), model.createIfcDirection(tuple(float(v) for v in point(extrusion[1]))), float(extrusion[2]) / 1000))
    representation = model.createIfcShapeRepresentation(context, "Body", "SweptSolid", items)
    product = model.create_entity("IfcBuildingElementProxy", GlobalId=ifcopenshell.guid.new(), ObjectPlacement=model.createIfcLocalPlacement(None, _axis(model, np.zeros(3), axes)), Representation=model.createIfcProductDefinitionShape(None, None, [representation]))
    return model, product


def _mesh(product):
    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), product)
    vertices = np.asarray(shape.geometry.verts, dtype=float).reshape(-1, 3)
    faces = np.asarray(shape.geometry.faces, dtype=int).reshape(-1, 3)
    if not len(vertices) or not len(faces) or not np.isfinite(vertices).all():
        raise ValueError("mesh_unavailable")
    triangles = [sorted(tuple(round(float(v), 6) for v in vertices[index]) for index in face) for face in faces]
    return sorted(triangles)


def _resolve(model, cls, name, origin, unit, axes=None):
    matches = [entity for entity in model.by_type(cls) if entity.Name == name and np.allclose(matrix(entity, unit)[:3, 3], origin, atol=0.00000051, rtol=0) and (axes is None or np.allclose(matrix(entity, unit)[:3, :3], axes, atol=0.00000051, rtol=0))]
    if len(matches) != 1:
        raise ValueError("public_reference_not_unique_or_absent")
    return matches[0]


def _body_from_public(text, damaged, unit):
    peer = re.search(r"几何形状逐项复制模型中仍存在的(Ifc\w+)「(.*?)」，参考实例的世界基点为" + POINT, text)
    if peer:
        directions = re.search(r"世界X/Y/Z轴分别为(.*?)；复制", text[peer.start():])
        if directions is None:
            raise ValueError("public_peer_axes_mismatch")
        entity = _resolve(damaged, peer[1], peer[2], point(peer[3]), unit, axes=np.asarray(points(directions[1])).T)
        return None, entity
    return geometry_from_text(text)


def _floor_frame(damaged, name, text, unit):
    origin = re.search(r"楼层世界基点" + POINT, text)
    if not origin:
        raise ValueError("storey_frame_missing")
    axes = _public_frame_axes(text, "楼层")
    return _resolve(damaged, "IfcBuildingStorey", name, point(origin[1]), unit, axes=axes)


def _public_frame_axes(text, prefix):
    description = re.search(prefix + r"世界基点" + POINT + r"米，世界X/Y/Z轴" + POINT + "、" + POINT + "、" + POINT, text)
    if not description:
        raise ValueError("public_frame_axes_missing:" + prefix)
    return np.asarray([point(description[i]) for i in (2, 3, 4)]).T


def audit_prompt(original, damaged, manifest, frame, text):
    unit = ifcopenshell.util.unit.calculate_unit_scale(original)
    failures = []
    body_checks = opening_checks = location_checks = property_checks = 0
    rows = re.split(r"\n\d+\. ", text)[1:]
    deletions = manifest.get("deletions", [])
    if len(rows) != len(deletions):
        failures.append("target_count_mismatch")
    if "坐标单位为米，尺寸单位为毫米" not in text:
        failures.append("units_missing")
    for target, row in zip(deletions, rows):
        entity = original.by_guid(target["guid"])
        kind = re.search(r"补建一[扇根](门|窗|梁|柱)：", row)
        if kind is None or {"门": "IfcDoor", "窗": "IfcWindow", "梁": "IfcBeam", "柱": "IfcColumn"}[kind[1]] != entity.is_a():
            failures.append("target_class_mismatch")
        placement = re.search(r"放置原点[^。；]*?为" + POINT + r"米", row)
        axes_text = re.search(r"构件自身X、Y、Z轴在上述坐标系中的方向分别为(.*?)。", row)
        try:
            if not placement or axes_text is None:
                raise ValueError("placement_or_axes_missing")
            local = np.eye(4)
            local[:3, 3] = point(placement[1])
            local[:3, :3] = np.asarray(points(axes_text[1])).T
            if frame == "world":
                located = local
            elif frame == "storey_local":
                name = re.search(r"楼层「(.*?)」", row)
                located = matrix(_floor_frame(damaged, name[1], row, unit), unit) @ local
            else:
                name = re.search(r"墙「(.*?)」", row)
                origin = re.search(r"墙世界基点" + POINT, row)
                located = matrix(_resolve(damaged, "IfcWall", name[1], point(origin[1]), unit, axes=_public_frame_axes(row, "墙")), unit) @ local
            if not np.allclose(located, matrix(entity, unit), atol=0.000003, rtol=0):
                failures.append("placement_or_axes_mismatch")
            location_checks += 1
        except (ValueError, TypeError, IndexError) as exc:
            failures.append(str(exc))
        # Compare source memberships to objects uniquely identifiable in the damaged IFC.
        if "楼层「" not in row:
            failures.append("storey_membership_missing")
        else:
            try:
                name = re.search(r"楼层「(.*?)」", row)[1]
                floor = _floor_frame(damaged, name, row, unit) if "楼层世界基点" in row else next(e for e in damaged.by_type("IfcBuildingStorey") if e.Name == name)
                if floor.GlobalId != target["storey"]["guid"]:
                    failures.append("storey_membership_mismatch")
            except (ValueError, StopIteration):
                failures.append("storey_membership_not_resolvable")
        try:
            product_text = row.split("洞口规格开始")[0]
            geometry_model, reconstructed = _body_from_public(product_text, damaged, unit)
            if _mesh(reconstructed) != _mesh(entity):
                failures.append("target_geometry_mismatch")
            body_checks += 1
        except Exception as exc:
            failures.append("target_geometry_unverified:" + str(exc)[:120])
        if target["ifc_class"] in {"IfcDoor", "IfcWindow"}:
            if not target.get("opening_guid"):
                failures.append("opening_binding_missing")
                continue
            source_opening = original.by_guid(target["opening_guid"])
            source_host = source_opening.VoidsElements[0].RelatingBuildingElement
            try:
                host_name = re.search(r"墙「(.*?)」", row)
                host_point = re.search(r"墙世界基点" + POINT, row)
                if not host_name or not host_point:
                    raise ValueError("wall_host_missing")
                host = _resolve(damaged, "IfcWall", host_name[1], point(host_point[1]), unit, axes=_public_frame_axes(row, "墙"))
                if host.GlobalId != source_host.GlobalId:
                    failures.append("wall_host_mismatch")
            except (ValueError, IndexError) as exc:
                failures.append(str(exc))
            if target.get("preserve_opening", True):
                try:
                    public_origin = re.search(r"保留现有洞口（其世界原点为" + POINT + r"米）", row)
                    if public_origin is None:
                        raise ValueError("retained_opening_public_location_missing")
                    matches = [r.RelatedOpeningElement for r in host.HasOpenings if np.allclose(matrix(r.RelatedOpeningElement, unit)[:3, 3], point(public_origin[1]), atol=0.00000051, rtol=0)]
                    if len(matches) != 1 or matches[0].GlobalId != source_opening.GlobalId or _mesh(matches[0]) != _mesh(source_opening) or "门窗填充关系" not in row:
                        failures.append("retained_opening_not_unique_or_changed")
                    opening_checks += 1
                except Exception as exc:
                    failures.append("retained_opening_unverified:" + str(exc)[:120])
            else:
                spec = re.search(r"洞口规格开始(.*?)洞口规格结束", row)
                if not spec:
                    failures.append("removed_opening_spec_missing")
                    continue
                try:
                    origin = re.search(r"洞口世界原点为" + POINT + r"米", spec[1])
                    directions = re.search(r"洞口世界X/Y/Z轴分别为(.*?)。", spec[1])
                    opening_frame = np.eye(4)
                    opening_frame[:3, 3] = point(origin[1])
                    opening_frame[:3, :3] = np.asarray(points(directions[1])).T
                    if not np.allclose(opening_frame, matrix(source_opening, unit), atol=0.000003, rtol=0):
                        failures.append("opening_placement_mismatch")
                    geometry_model, reconstructed = _body_from_public(spec[1], damaged, unit)
                    if _mesh(reconstructed) != _mesh(source_opening):
                        failures.append("opening_geometry_mismatch")
                    if "门窗填充关系" not in spec[1]:
                        failures.append("fill_relationship_missing")
                    opening_checks += 1
                except Exception as exc:
                    failures.append("opening_geometry_unverified:" + str(exc)[:120])
    # Parse actual property requests, then resolve public name/origin in damaged IFC.
    for change in manifest.get("property_changes", []):
        line = next((line for line in text.splitlines() if "实例属性「" + change["pset_name"] + "." + change["property_name"] + "」" in line), None)
        try:
            if not line or f"「{change['name']}」" not in line:
                raise ValueError("property_target_or_path_missing")
            token = re.search(r"改为(.*?)，保留其原属性类型", line)[1]
            value = True if token == "是" else False if token == "否" else json.loads(token)
            if type(value) != type(change["before"]) or value != change["before"]:
                failures.append("property_restoration_value_mismatch")
            origin = re.search(r"放置原点[^。；]*?为" + POINT + r"米", line)
            if frame == "world":
                world_point = point(origin[1])
            elif frame == "storey_local":
                floor = _floor_frame(damaged, re.search(r"楼层「(.*?)」", line)[1], line, unit)
                world_point = (matrix(floor, unit) @ np.r_[point(origin[1]), 1])[:3]
            else:
                host = _resolve(damaged, "IfcWall", re.search(r"墙「(.*?)」", line)[1], point(re.search(r"墙世界基点" + POINT, line)[1]), unit)
                world_point = (matrix(host, unit) @ np.r_[point(origin[1]), 1])[:3]
            located = _resolve(damaged, change["ifc_class"], change["name"], world_point, unit)
            if located.GlobalId != change["guid"]:
                failures.append("property_identity_mismatch")
            property_checks += 1
        except Exception as exc:
            failures.append("property_request_unverified:" + str(exc)[:120])
    return {"frame": frame, "sufficient": not failures, "target_geometry_checks": body_checks, "opening_geometry_checks": opening_checks, "location_and_axes_checks": location_checks, "property_request_checks": property_checks, "failures": sorted(set(failures)), "scope": "specified geometry, placement, containment, opening/void/fill and named property values; not all original semantic fields or repair-system success"}


def audit_case(folder, label, *, reference=None, reuse_native=None, reuse_receipt=None):
    folder = Path(folder).resolve()
    reference = Path(reference).resolve() if reference else folder.parent.parent / "private/reference.ifc"
    case = json.loads((folder / "case.json").read_text(encoding="utf-8"))
    manifest = json.loads((folder / "private/mutation.json").read_text(encoding="utf-8"))
    input_hashes = {str(path): sha256(path) for path in [reference, *folder.rglob("*")] if path.is_file()}
    original = ifcopenshell.open(str(reference))
    damaged = ifcopenshell.open(str(folder / "public/model.ifc"))
    if reuse_native is not None:
        if reuse_native["case_folder"] != str(folder) or reuse_native["damaged_sha256"] != sha256(folder / "public/model.ifc") or reuse_native["native"].get("ifcopenshell_version") != ifcopenshell.version or not reuse_native["native"].get("express_rules"):
            raise ValueError("native_receipt_byte_binding_failed")
        native = reuse_native["native"]
    else:
        native = native_validate(damaged)
    preservation = verify_case(original, damaged, manifest)
    prompts = []
    for frame, meta in case["prompt_templates"].items():
        if meta["applicable"]:
            prompts.append(audit_prompt(original, damaged, manifest, frame, (folder / f"public/request-{frame}.txt").read_text(encoding="utf-8")))
    # The original spot checker adds up to 3 independent surviving world meshes.
    if reference == folder.parent.parent / "private/reference.ifc":
        sampled = inspect_case(folder.parents[3], {**case, "case_id": label, "path": folder.relative_to(folder.parents[3]).as_posix()})
    else:
        sampled = {"passed": True, "scope": "normalization probe; product cross-check only", "preserved_world_meshes_checked": 0}
    unchanged = all(sha256(Path(path)) == expected for path, expected in input_hashes.items())
    reference_bound = sha256(reference) == manifest["source_sha256"] == case["source_sha256"]
    removed = {row["guid"] for row in manifest["deletions"]} | {row["opening_guid"] for row in manifest["deletions"] if row.get("opening_guid") and not row.get("preserve_opening", True)}
    old_ids = {entity.GlobalId for entity in original.by_type("IfcProduct")}
    new_ids = {entity.GlobalId for entity in damaged.by_type("IfcProduct")}
    count_check = old_ids - new_ids == removed and not new_ids - old_ids
    sufficient = bool(prompts) and all(row["sufficient"] for row in prompts)
    seal_ok = verify_seal(folder)
    return {"case_id": label, "case_folder": str(folder), "family": case["family"], "native": native, "native_validation_mode": "reused_bound_receipt" if reuse_native is not None else "fresh", "native_reused_from": reuse_receipt, "preservation": preservation, "independent_sample": sampled, "product_identity_crosscheck_passed": count_check, "input_bytes_unchanged": unchanged, "input_sha256": input_hashes, "reference_bound": reference_bound, "reference_sha256": sha256(reference), "seal_passed": seal_ok, "ifc_compliant": native["passed"], "damage_crosscheck_passed": preservation["passed"] and count_check and sampled["passed"] and unchanged and seal_ok and reference_bound, "prompt_information_sufficient": sufficient, "prompts": prompts, "damaged_sha256": sha256(folder / "public/model.ifc"), "human_reviewed": False}


def run_audit(entries, output, *, reuse_native_from=None):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    code_hash = sha256(Path(__file__))
    (output / "auditor-source.py").write_bytes(Path(__file__).read_bytes())
    results = []
    previous = {}
    if reuse_native_from:
        for path in Path(reuse_native_from).glob("case-*.json"):
            receipt = json.loads(path.read_text(encoding="utf-8"))
            previous[receipt["case_id"]] = (receipt, {"path": str(path.resolve()), "sha256": sha256(path)})
    for index, item in enumerate(entries):
        log = output / f"case-{index + 1:03d}.log"
        with log.open("w", encoding="utf-8") as stream, contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            reused, authority = previous.get(item["case_id"], (None, None))
            result = audit_case(item["case_folder"], item["case_id"], reference=item.get("reference"), reuse_native=reused, reuse_receipt=authority)
        write_json(output / f"case-{index + 1:03d}.json", result)
        results.append(result)
        write_json(output / "progress.json", {"checked": len(results), "planned": len(entries)})
    failure_counts = Counter(code for row in results for prompt in row["prompts"] for code in prompt["failures"])
    summary = {"schema_version": "text2ifc/first-batch-audit/1.2", "case_count": len(results), "unique_damaged_bytes": len({row["damaged_sha256"] for row in results}), "ifc_compliant": sum(row["ifc_compliant"] for row in results), "damage_crosscheck_passed": sum(row["damage_crosscheck_passed"] for row in results), "prompt_information_sufficient": sum(row["prompt_information_sufficient"] for row in results), "applicable_prompt_templates": sum(len(row["prompts"]) for row in results), "sufficient_prompt_templates": sum(prompt["sufficient"] for row in results for prompt in row["prompts"]), "prompt_failure_template_counts": dict(failure_counts), "all_input_bytes_unchanged": all(row["input_bytes_unchanged"] for row in results), "native_validation_modes": dict(Counter(row["native_validation_mode"] for row in results)), "auditor_sha256": code_hash, "auditor_unchanged_during_run": sha256(Path(__file__)) == code_hash, "ifcopenshell_version": ifcopenshell.version, "express_rules": True, "provider_calls": 0, "human_reviewed": False, "scope": "native schema+EXPRESS (fresh or explicitly hash-bound receipts), fresh product/typed-property preservation and sampled meshes, independent actual public-text geometry reconstruction and reference resolution; no live repair testing", "results": [{key: row[key] for key in ("case_id", "family", "ifc_compliant", "damage_crosscheck_passed", "prompt_information_sufficient")} for row in results]}
    write_json(output / "summary.json", summary)
    table = ["|样本|原生校验|损伤交叉检查|Prompt 信息|", "|---|---|---|---|"]
    for row in results:
        table.append("|" + row["case_id"] + "|" + "|".join("通过" if row[key] else "不通过" for key in ("ifc_compliant", "damage_crosscheck_passed", "prompt_information_sufficient")) + "|")
    report = f"# 首批损伤独立校验\n\n检查 {len(results)} 份记录，IFC2X3 schema＋EXPRESS 通过 {summary['ifc_compliant']} 份，损伤交叉检查通过 {summary['damage_crosscheck_passed']} 份，全部适用 prompt 信息检查通过 {summary['prompt_information_sufficient']} 份。原文件和被检查输出全部原字节保留：{summary['all_input_bytes_unchanged']}。\n\n" + "\n".join(table) + "\n\nPrompt 缺口按模板计数：\n\n" + "\n".join(f"- `{key}`：{value}" for key, value in failure_counts.items()) + "\n\n检查实际公开文本中的位置、方向、实体形状、参照实例、楼层、宿主墙和洞口，以及指定属性的目标和值。受支持截面从文本重新建几何；复杂构件在损伤 IFC 中独立解析公开参照并比较局部三角网格。网格比较采用 1 微米量化的无序三角形，不是全工程几何证明。原生零 findings 只证明本次原生校验通过。这里未运行系统修复，不代表修复成功率；也未验收原构件的所有语义属性。每例 JSON 保留完整 findings 和限制。\n"
    (output / "REPORT.md").write_text(report, encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True, help="JSON list of explicit case_folder, case_id, optional reference")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reuse-native-from", type=Path, help="Reuse only the same-version native result for an exact damaged IFC SHA; all other checks run again")
    args = parser.parse_args()
    result = run_audit(json.loads(args.inputs.read_text(encoding="utf-8")), args.output, reuse_native_from=args.reuse_native_from)
    print(json.dumps({key: value for key, value in result.items() if key != "results"}, ensure_ascii=False))
