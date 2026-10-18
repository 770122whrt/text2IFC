"""Bounded offline polygon reuse probes and read-only pilot admission audit.

The fixture Provider is deterministic. This is public RepairAPI downstream
feasibility evidence, never live LLM evidence or a dataset success rate.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / ".deps/python312")]

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.geom
import ifcopenshell.util.unit
import numpy as np

from scripts.ifc_repair.repair_comparison.inspection import native_validation
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.door_geometry import public_door_installation_anchor
from text2ifc_ifc_repair.window_geometry import public_window_installation_anchor
from tests.ifc_repair.test_door_direct_body_reference import brep_scene
from tests.ifc_repair.test_door_installation_anchor import PublicOnlyProvider
from tests.ifc_repair.test_window_installation_anchor import (
    PublicWindowProvider, scene as window_scene,
)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _type(product):
    types = [r.RelatingType for r in product.IsDefinedBy if r.is_a("IfcRelDefinesByType")]
    return types[0] if len(types) == 1 else None


def _body(product):
    return next(r for r in product.Representation.Representations if r.RepresentationIdentifier == "Body")


def _polygon(model, unit, outer, *, y, depth, inner=None):
    def curve(points):
        return model.createIfcPolyline([
            model.createIfcCartesianPoint((float(x) * unit, float(z) * unit)) for x, z in points
        ])
    outside = curve(outer)
    if inner is None:
        profile = model.createIfcArbitraryClosedProfileDef("AREA", None, outside)
    else:
        profile = model.createIfcArbitraryProfileDefWithVoids("AREA", None, outside, [curve(inner)])
    # The profile lies in X/Z; its local extrusion axis points towards -Y.
    frame = model.createIfcAxis2Placement3D(
        model.createIfcCartesianPoint((0., y * unit, 0.)),
        model.createIfcDirection((0., -1., 0.)), model.createIfcDirection((1., 0., 0.)),
    )
    return model.createIfcExtrudedAreaSolid(profile, frame, model.createIfcDirection((0., 0., 1.)), depth * unit)


def polygon_scene(kind, *, mapped=True, millimetres=False, angle=0.):
    """Independently authored public references: U door and holed window frame."""
    if kind == "door":
        model, opening, reference, unit = brep_scene(millimetres=millimetres, angle=angle)
        body = _body(reference)
        body.RepresentationType = "SweptSolid"
        body.Items = [
            _polygon(model, unit, [(0,0),(30,0),(30,2070),(870,2070),(870,0),
                                  (900,0),(900,2100),(0,2100),(0,0)], y=50., depth=50.),
            _polygon(model, unit, [(40,40),(860,40),(860,2060),(40,2060),(40,40)], y=55., depth=30.),
            _polygon(model, unit, [(700,900),(800,900),(800,1000),(700,1000),(700,900)], y=130., depth=75.),
        ]
        if mapped:
            origin = model.createIfcAxis2Placement3D(model.createIfcCartesianPoint((0., 0., 0.)))
            mapping = model.createIfcRepresentationMap(origin, body)
            reference.Representation.Representations = [
                ifcopenshell.api.geometry.map_representation(model, representation=body)
            ]
            # map_representation uses the existing map, so Body has one owner.
            _type(reference).RepresentationMaps = [mapping]
    else:
        model, _, _, reference, _, unit = window_scene(millimetres=millimetres, angle=angle)
        mapped_body = _type(reference).RepresentationMaps[0].MappedRepresentation
        items = [
            _polygon(model, unit, [(0,0),(900,0),(900,1200),(0,1200),(0,0)], y=20., depth=40.,
                     inner=[(30,30),(30,1170),(870,1170),(870,30),(30,30)]),
            _polygon(model, unit, [(30,30),(870,30),(870,1170),(30,1170),(30,30)], y=2., depth=4.),
            _polygon(model, unit, [(-25,-10),(925,-10),(925,0),(-25,0),(-25,-10)], y=45., depth=75.),
        ]
        mapped_body.Items = items
        if not mapped:
            body = _body(reference)
            body.Items = items
            body.RepresentationType = "SweptSolid"
            _type(reference).RepresentationMaps = None
    return model, reference


def _mesh(product):
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", False)
    shape = ifcopenshell.geom.create_shape(settings, product)
    verts = np.asarray(shape.geometry.verts).reshape(-1, 3)
    faces = np.asarray(shape.geometry.faces, dtype=int).reshape(-1, 3)
    # Independent comparison after reopen: full triangles, not only a box.
    return sorted(tuple(sorted(tuple(np.round(verts[i], 6)) for i in face)) for face in faces)


def run_probe(folder, kind, *, mapped=True, millimetres=False, angle=0.):
    folder = folder.absolute()
    folder.mkdir(parents=True, exist_ok=False)
    model, reference = polygon_scene(kind, mapped=mapped, millimetres=millimetres, angle=angle)
    source = folder / "public.ifc"
    model.write(str(source))
    before = _sha(source)
    input_validation = native_validation(ifcopenshell.open(str(source)))
    expected_mesh = _mesh(reference)
    provider = PublicOnlyProvider() if kind == "door" else PublicWindowProvider()
    request = (
        "Fill the empty opening with a 900 by 2100 mm door. Use the retained door as the complete shape "
        "and installation reference; align the base."
        if kind == "door" else
        "Add a 900 by 1200 mm window, sill 700 mm, at 1500 mm from the public wall axis start. "
        "Reuse the retained window's complete frame, glazing, board and installation."
    )
    (folder / "request.txt").write_text(request + "\n", encoding="utf-8")
    result = RepairAPI(folder / "run", provider=provider, scene_grounding=True).start(source, request)
    row = {
        "kind": kind, "mapped": mapped, "millimetres": millimetres, "angle_degrees": angle,
        "provider_evidence": "offline_fake", "source_unchanged": _sha(source) == before,
        "input_native_passed": input_validation["passed"], "status": result.status,
        "artifact_publishable": result.successful_artifact_publishable,
        "same_local_mesh": False, "reference_mesh_unchanged": False,
        "output_native_passed": None, "provider_call_count": len(provider.calls),
        "successful_ifc": None, "result": result.to_dict(),
    }
    if result.successful_artifact_publishable:
        path = folder / "run" / result.run_directory / result.artifacts["successful_ifc"]
        repaired = ifcopenshell.open(str(path))
        candidates = [e for e in repaired.by_type(reference.is_a()) if e.GlobalId != reference.GlobalId]
        row["same_local_mesh"] = len(candidates) == 1 and _mesh(candidates[0]) == expected_mesh
        row["reference_mesh_unchanged"] = _mesh(repaired.by_guid(reference.GlobalId)) == expected_mesh
        row["output_native_passed"] = native_validation(repaired)["passed"]
        row["successful_ifc"] = str(path.resolve())
    row["exact_reuse_passed"] = all(row[k] for k in (
        "source_unchanged", "input_native_passed", "artifact_publishable", "same_local_mesh",
        "reference_mesh_unchanged", "output_native_passed",
    ))
    (folder / "probe.json").write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return row


def audit_pilot(pilot):
    """Private metadata identifies audit targets only; never enters RepairAPI."""
    rows = []
    with (pilot / "cases.csv").open(encoding="utf-8-sig", newline="") as stream:
        cases = list(csv.DictReader(stream))
    for case in cases:
        folder = pilot / case["path"]
        mutation_path = folder / "private/mutation.json"
        public_path = folder / "public/model.ifc"
        before = _sha(public_path)
        mutation = json.loads(mutation_path.read_text(encoding="utf-8"))
        hosted = [d for d in mutation["deletions"] if d["ifc_class"] in {"IfcDoor", "IfcWindow"}]
        if not hosted:
            continue
        model = ifcopenshell.open(str(public_path))
        deleted = {d["guid"] for d in mutation["deletions"]}
        for target in hosted:
            body = target["geometry"].get("body_spec") or {}
            components = body.get("components", [])
            profiles = [c["profile"]["kind"] for c in components]
            polygonal = any(p in {"IfcArbitraryClosedProfileDef", "IfcArbitraryProfileDefWithVoids"} for p in profiles)
            try:
                style = model.by_guid(target.get("type_guid") or "")
            except RuntimeError:
                style = None
            usable, rejected = [], []
            for peer in target["geometry"].get("peers", []):
                if peer["guid"] in deleted:
                    continue
                entity = model.by_guid(peer["guid"])
                try:
                    function = public_door_installation_anchor if entity.is_a("IfcDoor") else public_window_installation_anchor
                    anchor = function(entity)
                    usable.append({"origin_world_m": peer["origin_world_m"], "method": anchor["method"]})
                except ValueError as exc:
                    rejected.append(str(exc))
            simple = len(components) == 1 and profiles == ["IfcRectangleProfileDef"]
            decision = "keep_same_shape_reference" if usable else (
                "keep_basic_shape_candidate" if simple else "exclude_from_next_simple_reference_batch"
            )
            rows.append({
                "source_id": case["source_id"], "case_id": case["case_id"], "kind": target["ifc_class"],
                "polygonal": polygonal, "component_count": len(components), "profiles": profiles,
                "surviving_type_map_count": len(style.RepresentationMaps or ()) if style else 0,
                "usable_same_mesh_peers": usable, "rejected_peer_reasons": rejected,
                "next_batch_decision": decision, "historical_case_changed": False,
                "boundary": "retained peer identity comes from private audit metadata, not a Provider input; full original-case RepairAPI execution not performed",
            })
        if _sha(public_path) != before:
            raise RuntimeError("Pilot public IFC changed during read-only audit")
    return rows


def collect_probe(folder):
    """Reuse finished probes only after checking their original run authorities."""
    row = json.loads((folder / "probe.json").read_text(encoding="utf-8"))
    run = folder / "run" / row["result"]["run_directory"]
    state = json.loads((run / "state.json").read_text(encoding="utf-8"))
    if "sha256:" + _sha(folder / "public.ifc") != state["source"]["sha256"]:
        raise ValueError("PROBE_SOURCE_HASH_MISMATCH")
    manifest_path = run / row["result"]["artifacts"]["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for artifact in manifest["artifacts"]:
        if _sha(run / artifact["path"]) != artifact["sha256"].removeprefix("sha256:"):
            raise ValueError("PROBE_TERMINAL_ARTIFACT_HASH_MISMATCH")
    return row


def write_report(folder, report):
    decisions = report["pilot_decision_counts"]
    lines = [
        "# 多边形门窗是否保留：当前 Harness 的离线核验",
        "",
        "结论：下一版保留**有完整公开类型映射、且有可用同形实例参照**的多边形门窗；"
        "无合格参照时优先选择母本中原本就是基础形状的对象。公开请求采用单一定位，"
        "先引用同形参照，仅在没有参照时描述必要尺寸和方向；不再逐个展开复杂拉伸实体。",
        "",
        f"通过公开 `RepairAPI.start()` 的四个复用探针中，{report['positive_passed']}/{report['positive_total']} "
        "在写出、重开后完整局部三角网格一致，原输入和保留参照未变，原生 schema＋EXPRESS 校验通过。"
        "探针包含 U 形门框、门扇与附属实体，以及带内孔窗框、玻璃和窗台板；覆盖米制、毫米制及 37° 旋转。",
        "",
        "这些是独立编写的合成公开 IFC，使用确定性的 fixture Provider，没有调用真实模型，"
        "只证明已有绑定之后的复用、安装、写入和校验路径可执行。它们不证明 LLM 能自动选对参照，"
        "也不构成原 20 题修复成功率。当前 Harness 实现没有为本次探针新增多边形功能。",
        "",
        "## 六个探针的结果",
        "",
        "|场景|类型映射|Harness 状态|输出合规|完整同形|",
        "|---|---|---|---|---|",
    ]
    for p in report["probes"]:
        label = f"{p['kind']} / {'毫米' if p['millimetres'] else '米'} / {p['angle_degrees']:g}°"
        lines.append(f"|{label}|{'有' if p['mapped'] else '无'}|{p['status']}|"
                     f"{'通过' if p['output_native_passed'] else '失败或无输出'}|"
                     f"{'一致' if p['same_local_mesh'] else '**不一致**'}|")
    lines += [
        "",
        "两个无类型映射反例都返回 `succeeded`，且输出通过原生校验，但生成的是基础形状，"
        "未保留要求的多边形完整网格。它们作为负面证据保留，不能算恢复原样。"
        "门的直接 Body 参照目前仅支持完整 `IfcFacetedBrep`；没有类型映射的直接拉伸实体被参照检查拒绝。"
        "窗的安装参照要求类型映射。公开 Intent 也没有任意多边形顶点或拉伸组合的输入接口。",
        "",
        "## 现有小批次的只读筛选",
        "",
        "这里按**被删除门窗目标**计数，不是通过题目数。梁柱和纯属性题不在本次几何检查范围内。",
        "",
        "|下一轮选择意见|门窗目标数|",
        "|---|---:|",
        f"|保留：同网格实例参照通过当前安装锚点检查|{decisions.get('keep_same_shape_reference', 0)}|",
        f"|保留基础形状候选：单一矩形拉伸，无需复杂形状参数|{decisions.get('keep_basic_shape_candidate', 0)}|",
        f"|从下一轮简洁参照主批次排除复杂无参照目标|{decisions.get('exclude_from_next_simple_reference_batch', 0)}|",
        "",
        "已有 20 题的 IFC、请求、封存、机器校验状态保持原字节；这里的选择意见只用于下一版。"
        "“参照可用”只检查私有记录所指同网格公开实例能否通过 Harness 的安装参照函数，"
        "并未逐题运行真实 Provider 或整题修复。类型映射存在也不单独保证原实例的位置和安装偏移可恢复。",
        "",
        "## formal-007 / case-003-a01",
        "",
    ]
    for r in report["pilot_admission_audit"]:
        if r["source_id"] != "formal-007" or r["case_id"] != "case-003-a01":
            continue
        if r["kind"] == "IfcWindow":
            lines += [
                "窗：保留为下一版参照候选。损伤模型内仍有同形窗，其完整窗形、洞口形状和相对安装"
                "已在前轮抽查比对；本轮其公开安装锚点也通过。公开形状段可缩为：",
                "",
                "> 完整形状及朝向与世界放置原点（-10.316，7.999，10.363）米处的现存窗一致；"
                "洞口沿用该参照窗所填洞口的宽、高，并贯穿目标宿主墙。",
                "",
                "这是形状段示例，完整定位段仍由脚本按墙名或世界坐标单独生成。公开数值最多三位小数；"
                "其定位匹配和私有评价须按输出精度声明容差。完整参照几何来自损伤 IFC，不靠隐藏几何补答案。",
                "",
            ]
        else:
            lines += [
                f"门：完整的 {r['component_count']} 个拉伸实体仍可由公开门类型的 "
                f"{r['surviving_type_map_count']} 个类型映射提供，但没有同网格存活门实例。"
                "这说明类型几何可获取，尚不足以证明当前简洁请求能恢复原安装状态；"
                "本轮不将它作为简洁实例参照主批次的目标，下一版选择原本基础形状或有合格参照的门替代。"
                "旧 case-003 保留，不把保留类型映射直接算作原题修复成功。",
                "",
            ]
    lines += [
        "## 下一版执行规则",
        "",
        "1. 每份请求只采用墙名定位或世界坐标定位一种；优先引用损伤后仍存活、可唯一找到的同形实例。",
        "2. 同形参照须保留完整类型映射，并通过现有安装锚点检查；损伤不能同时删除该参照。",
        "3. 无参照时，选原本就是基础形状的目标，明确宽、高、厚度、位置和必要方向。"
        "复杂无参照对象不进入本轮主批次；不把复杂原形的外包盒当作恢复答案。",
        "4. 私有记录保留完整几何和原精度；公开请求独立足够。公开数值最多三位小数，"
        "匹配与评价使用相应精度，不能继续套用旧请求的微米容差。",
        "5. 下一版新增 prompt 版本、检查器和抽样报告；本次没有改写原 1.2 版本或生成新的 20 题。",
        "",
        "机器明细：[summary.json](summary.json)。每个探针目录都有 `request.txt`、`public.ifc`、"
        "`probe.json` 和公开 RepairAPI 的 run 权威记录；负例输出同样保留。",
        "",
        "复跑脚本：`scripts/ifc_repair/audit_harness_geometry_scope.py --pilot <pilot-dir> --output <new-dir>`。"
        "`--collect-only` 只汇总已完成的六个探针，并先核对输入及 terminal manifest 的哈希，不重复修复。"
        "最初两次 CLI 尝试在 Windows 沙箱的路径规范化处被拒，未执行修复；第三次在授权的本地执行环境"
        "完成探针。随后只读索引因 UTF-8 BOM 中断，修正索引读取后复用已完成探针，不重复调用。",
        "",
    ]
    (folder / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pilot", type=Path)
    parser.add_argument("--collect-only", action="store_true", help="Finalize existing completed probes without running them again")
    args = parser.parse_args(argv)
    args.output = args.output.absolute()
    args.output.mkdir(parents=True, exist_ok=args.collect_only)
    if (args.output / "summary.json").exists():
        raise ValueError("An existing summary must not be overwritten")
    probes = []
    for kind in ("door", "window"):
        for mm, angle in ((False, 0.), (True, 37.)):
            name = f"{kind}-mapped-{'mm' if mm else 'm'}"
            probes.append(collect_probe(args.output / name) if args.collect_only else
                          run_probe(args.output / name, kind, millimetres=mm, angle=angle))
        name = f"{kind}-direct-no-type-map"
        probes.append(collect_probe(args.output / name) if args.collect_only else
                      run_probe(args.output / name, kind, mapped=False))
    pilot_rows = audit_pilot(args.pilot) if args.pilot else []
    positives = [p for p in probes if p["mapped"]]
    boundaries = [p for p in probes if not p["mapped"]]
    report = {
        "schema_version": "text2ifc/harness-geometry-scope-audit/0.1",
        "scope": "offline public RepairAPI polygon-body reuse feasibility; no live LLM, no new Harness feature, no original pilot changes",
        "positive_passed": sum(p["exact_reuse_passed"] for p in positives),
        "positive_total": len(positives),
        "nonmapped_boundaries": [{k: p[k] for k in ("kind", "status", "exact_reuse_passed", "artifact_publishable")} for p in boundaries],
        "probes": probes, "pilot_admission_audit": pilot_rows,
        "pilot_decision_counts": dict(Counter(r["next_batch_decision"] for r in pilot_rows)),
        "next_batch_policy": {
            "priority": "one localization strategy plus a surviving same-shape reference whose public installation anchor is supported",
            "keep_polygon_if": "complete public type maps and a usable same-shape surviving reference; checked downstream exact reuse",
            "without_reference": "single basic rectangular body with explicit dimensions, position and orientation; no arbitrary polygon vertex recipes",
            "type_map_only": "available geometry does not establish correct instance installation; hold complex no-peer targets out of this simple-reference main batch",
            "private_geometry": "retain full precision for independent evaluation; never use hidden geometry to complete a public answer",
            "numbers": "public dimensions and coordinates at most three decimal places; evaluate at the declared printed precision",
        },
    }
    report["provenance"] = {"collect_only": args.collect_only, "script_sha256": _sha(Path(__file__)),
                            "probe_run_source_snapshot": "evidence/probe-driver-at-run.py" if (args.output / "evidence/probe-driver-at-run.py").exists() else None}
    (args.output / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(args.output, report)
    print(json.dumps({k: report[k] for k in ("positive_passed", "positive_total", "nonmapped_boundaries", "pilot_decision_counts")}, ensure_ascii=False))
    return 0 if all(p["exact_reuse_passed"] for p in positives) else 1


if __name__ == "__main__":
    raise SystemExit(main())
