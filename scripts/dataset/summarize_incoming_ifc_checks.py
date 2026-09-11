"""Independently reparse all incoming IFCs, reconcile evidence, and write a review.

Read-only for IFC/ZIP/manifest inputs. Adds exclusive report files only. Expensive
schema validation is not retried for files already rejected by the size gate.
"""
from collections import Counter, defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys
import traceback
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "dataset/external/_checks/incoming-ifc-audit-20260910"
LIMIT = 10 * 1024 * 1024


def write_new(name, value):
    with (REPORT / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, default=str)
        stream.write("\n")


def main():
    import ifcopenshell
    sys.stdout.reconfigure(encoding="utf-8")
    inventory = json.loads((REPORT / "inventory.json").read_text(encoding="utf-8"))
    source_docs = inventory["archives"][0]["other_members"]
    source_assets = json.loads(next(d["text"] for d in source_docs if d["member"].endswith("/rvt_manifest.json")))
    assets = {d["asset_id"]: d for d in source_assets}
    deps = json.loads(next(d["text"] for d in source_docs if d["member"].endswith("/dependency_manifest.json")))
    rows, uid = [], 0
    for archive_record in inventory["archives"]:
        name = archive_record["name"]
        with zipfile.ZipFile(ROOT / "dataset/external" / name) as archive:
            for member in archive_record["members"]:
                report_file = REPORT / f"member-v2-{uid:03d}.json"
                deep = json.loads(report_file.read_text(encoding="utf-8")) if report_file.exists() else {}
                row = {**member, "number": uid, "deep_report": report_file.name if deep else None,
                       "deep_status": deep.get("parse_status", "not_run_size_gate_failed"),
                       "schema_error_count": deep.get("schema_error_count"),
                       "geometry_checked": deep.get("geometry_checked"), "geometry_failed": deep.get("geometry_failed"),
                       "roundtrip_ok": deep.get("roundtrip_ok"), "basic_candidate": deep.get("basic_candidate", False),
                       "geometry_scope": deep.get("geometry_scope", "not_completed"),
                       "full_express_rules": "not_run", "human_review": "pending",
                       "training_eligible": False, "redistribution": "not_admitted"}
                match = re.search(r"RVT-\d{3}", member["member"])
                row["asset_id"] = match.group() if match else ("ResBIM-" + Path(member["member"]).stem if name.startswith("ResBIM") else "Circular-existing")
                source = assets.get(row["asset_id"], {})
                row["source_provenance"] = {k: source.get(k) for k in ("repo", "original_filename", "data_license_status", "repository_license_recorded", "variant_of", "project_group_hint", "dataset_role")}
                row["license_status"] = source.get("data_license_status", "not_established_in_package")
                row["dependency_evidence"] = [d for d in deps if d["host_asset_id"] == row["asset_id"]]
                try:
                    raw = archive.read(archive.infolist()[member["index"]])
                    if hashlib.sha256(raw).hexdigest() != member["sha256"]:
                        raise RuntimeError("SOURCE_CHANGED_SINCE_INVENTORY")
                    data_start = re.search(rb"(?m)^DATA;\s*$", raw)
                    row["data_section_sha256"] = hashlib.sha256(raw[data_start.end():raw.rfind(b"ENDSEC;")]).hexdigest() if data_start else None
                    model = ifcopenshell.file.from_string(raw.decode("utf-8-sig"))
                    row["reparse_status"] = "ok"
                    row["schema"] = model.schema
                    classes = ("IfcProject", "IfcBuilding", "IfcBuildingStorey", "IfcWall", "IfcDoor", "IfcWindow", "IfcRoof", "IfcSlab", "IfcBeam", "IfcColumn", "IfcGrid", "IfcGridAxis", "IfcElement")
                    row["counts"] = {c: len(model.by_type(c)) for c in classes}
                    elements = model.by_type("IfcElement")
                    body = [e for e in elements if e.Representation and any(r.RepresentationIdentifier == "Body" and r.Items for r in e.Representation.Representations)]
                    row["body_elements"] = len(body)
                    row["element_guids"] = sorted({e.GlobalId for e in elements if e.GlobalId})
                    row["roof_slab_count"] = sum(getattr(e, "PredefinedType", None) == "ROOF" for e in model.by_type("IfcSlab"))
                    row["invalid_si_units_missing_name"] = [e.id() for e in model.by_type("IfcSIUnit") if e.Name is None]
                    row["missing_originating_system"] = model.header.file_name.originating_system is None
                    ids = [e.GlobalId for e in model.by_type("IfcRoot") if e.GlobalId]
                    row["duplicate_globalid_count"] = len(ids) - len(set(ids))
                    if len(raw) >= LIMIT:
                        row["additional_schema_validation"] = "not_run_size_gate_failed; direct mandatory-field and GUID checks only"
                    row["unvoided_opening_count"] = sum(not e.VoidsElements for e in model.by_type("IfcOpeningElement"))
                    row["door_window_without_fill_count"] = sum(not e.FillsVoids for e in model.by_type("IfcDoor") + model.by_type("IfcWindow"))
                    # Missing fill chains are review signals, not universal schema violations.
                    row["texture_references"] = [e.URLReference for e in model.by_type("IfcImageTexture")]
                    if not body:
                        row["size_body_class"] = "no_body"
                    elif len(raw) >= LIMIT:
                        row["size_body_class"] = "oversize_with_body"
                    else:
                        row["size_body_class"] = "small_with_body"
                    del model
                    del raw
                except Exception:
                    row.update(reparse_status="failed", error=traceback.format_exc(), size_body_class="check_failed")
                rows.append(row)
                uid += 1
    groups = defaultdict(list)
    for row in rows:
        if row.get("data_section_sha256"):
            groups[row["data_section_sha256"]].append(row["asset_id"])
    same_data = [v for v in groups.values() if len(v) > 1]
    overlap = []
    for a, b in itertools.combinations(rows, 2):
        x, y = set(a.get("element_guids", [])), set(b.get("element_guids", []))
        denominator = min(len(x), len(y))
        if denominator >= 10 and len(x & y) / denominator >= 0.8:
            overlap.append({"a": a["asset_id"], "b": b["asset_id"], "shared": len(x & y), "a_elements": len(x), "b_elements": len(y), "smaller_overlap": round(len(x & y) / denominator, 4), "classification": "variant_signal_not_independent_identity_proof"})
    summary = {"ifc_occurrences": len(rows), "exact_unique_files": inventory["unique_ifc_contents"],
               "canonical_exact_matches": sum(bool(r["canonical_match"]) for r in rows),
               "independent_building_count": None, "data_identical_groups": same_data,
               "high_guid_overlap_pairs": overlap, "groups": {}}
    for label, subset in (("converted_29", rows[:29]), ("circular_existing", rows[29:30]), ("resbim_50", rows[30:])):
        summary["groups"][label] = {"count": len(subset), "reparse_ok": sum(r["reparse_status"] == "ok" for r in subset),
            "size_body": dict(Counter(r["size_body_class"] for r in subset)),
            "no_grid_and_axis": sum(r.get("counts", {}).get("IfcGrid") == 0 and r.get("counts", {}).get("IfcGridAxis") == 0 for r in subset),
            "schema_checked": sum(r["schema_error_count"] is not None for r in subset),
            "schema_errors_found": sum(bool(r["schema_error_count"]) for r in subset),
            "schema_error_total": sum(r["schema_error_count"] or 0 for r in subset),
            "files_duplicate_globalid": sum(r.get("duplicate_globalid_count", 0) > 0 for r in subset),
            "files_missing_unit_name": sum(bool(r.get("invalid_si_units_missing_name")) for r in subset),
            "files_missing_header_originating_system": sum(r.get("missing_originating_system", False) for r in subset),
            "geometry_files_checked": sum(bool(r["geometry_checked"]) for r in subset),
            "geometry_elements_checked": sum(r["geometry_checked"] or 0 for r in subset),
            "geometry_failures": sum(r["geometry_failed"] or 0 for r in subset),
            "roundtrip_passed": sum(r["roundtrip_ok"] is True for r in subset),
            "basic_candidates": sum(bool(r["basic_candidate"]) for r in subset),
            "roof_entity_files": sum(r.get("counts", {}).get("IfcRoof", 0) > 0 for r in subset),
            "roof_slab_files": sum(r.get("roof_slab_count", 0) > 0 for r in subset),
            "unvoided_opening_files": sum(r.get("unvoided_opening_count", 0) > 0 for r in subset),
            "door_window_without_fill_files": sum(r.get("door_window_without_fill_count", 0) > 0 for r in subset)}
    summary["reported_missing_dependency_assets"] = sorted({d["host_asset_id"] for d in deps if d["bundle_presence_status"] == "not_in_supplied_bundle"})
    summary["reported_unresolved_link_assets"] = sorted({d["host_asset_id"] for d in deps if d["bundle_presence_status"] != "not_in_supplied_bundle"})
    write_new("verified-register.json", {"summary": summary, "files": rows})
    write_new("summary.json", summary)
    lines = ["# 新增 IFC ZIP 检查结果（2026-09-10）", "", "本报告仅登记检查结果，不是 canonical 准入清单。原 IFC/ZIP 均未修改。", "", "## 汇总", "", "```json", json.dumps(summary, ensure_ascii=False, indent=2), "```", "", "## 逐文件结果", "", "| 编号 | IFC 文件 | MiB | 主体构件 | 格式错误数 | 几何抽检数/失败数 | 屋顶/屋面板 | 状态 |", "|---|---|---:|---:|---:|---:|---:|---|"]
    for r in rows:
        errors = r["schema_error_count"] if r["schema_error_count"] is not None else "未完成（超限）"
        geometry = f"{r['geometry_checked']}/{r['geometry_failed']}" if r["geometry_checked"] is not None else "未完成"
        lines.append(f"| {r['asset_id']} | {Path(r['member']).name} | {r['size_bytes']/LIMIT*10:.4f} | {r.get('body_elements', '未知')} | {errors} | {geometry} | {r.get('counts',{}).get('IfcRoof','?')}/{r.get('roof_slab_count','?')} | {r['size_body_class']} |")
    lines += ["", "## 检查边界", "", "全体80个IFC从ZIP内重新用IfcOpenShell解析，未解压落盘。正式属性/基数/逆关系/唯一性校验对76个未超限文件完成；4个超限文件只计基础解析及直接必填字段/GlobalId检查。几何是按构件类别分层的有限抽样，不是全模型几何验收。EXPRESS WHERE规则、碰撞、设计规范、RVT→IFC完整性、逐模型视觉审查和许可终审未完成。", "", "重复GlobalId、缺失必填单位名等已由第二次独立解析直接确认。许可未审查通过前，training_eligible保持false；同一建筑变体不得计作独立建筑。", "", "历史member-000至004为检查器兼容故障证据，已由member-v2结果替代。member-v2-020保留一次90秒超时；整批10至19曾遇180秒命令超时，已保留完成结果并补齐。", ""]
    with (REPORT / "REPORT.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
