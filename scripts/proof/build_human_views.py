"""Build only human discovery surfaces from existing frozen Proof.

No Provider, IFC compiler, curator, authority mutation or recursive deletion.
The approved Windows directory moves are performed separately with LiteralPath.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PROOF = ROOT / "dataset/processed/proof"
SCHEMA = "text2ifc/workflow-human-proof/0.1"
PLAN_NAMES = (
    "beam-loadbearing", "column-loadbearing", "beam-column-atomic",
    "beam-material-present", "column-material-absent", "four-family-atomic",
    "live-complete", "live-clarification", "live-window-property", "program-guard",
)


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def copy_exact(source: Path, target: Path):
    if not source.is_file():
        raise FileNotFoundError(source)
    if target.exists():
        if not target.is_file() or sha(source) != sha(target):
            raise FileExistsError(f"independent target content: {target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(line.rstrip() for line in text.rstrip().splitlines()) + "\n", encoding="utf-8", newline="\n")


def write_json(path, obj):
    write(path, json.dumps(obj, ensure_ascii=False, indent=2))


def link(label, path, parent):
    relative = os.path.relpath(path, parent).replace("\\", "/")
    return f"[{label}](<{relative}>)"


def repo_path(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def archive_report(case):
    old = case / "REPORT.md"
    saved = case / "evidence/prior-REPORT.md"
    if old.exists() and not saved.exists():
        copy_exact(old, saved)
    return saved.read_text(encoding="utf-8") if saved.exists() else ""


def artifact_map(case, sources):
    bindings = {}
    for name, source in sources.items():
        if isinstance(source, tuple):
            path, field = source
            value = read(path)[field]
            if not isinstance(value, str):
                raise ValueError("request field must be text")
            payload = value.encode("utf-8")
            target = case / name
            if target.exists() and target.read_bytes() != payload:
                raise FileExistsError(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            bindings[name] = {"path": repo_path(path), "field": field}
        else:
            copy_exact(source, case / name)
            bindings[name] = repo_path(source)
    return bindings


def finish_case(collection, case, *, case_id, authority, sources, status, outcome,
                mode, calls, run_id, original_role=None, detail="", prior_text="", ifccompare="未知；参见冻结评估"):
    artifacts = artifact_map(case, sources)
    request = (case / "request.txt").read_text(encoding="utf-8")
    if outcome == "no_output":
        write(case / "NO-REPAIR.md", "# 正确无输出\n\n" + detail + "\n\n请求被原子阻断；不允许补造 repaired IFC。详情见 [REPORT.md](REPORT.md)。")
    role = {None: "没有 original；不补造私有 Gold。", "private_ground_truth": "original 为已冻结 evaluator-only 真值，仅供修复后评估。",
            "physical_fixture_non_private_audit": "original 仅为此前声明的物理对照，不是 case-specific private Gold。"}[original_role]
    if outcome == "generated":
        role = "Generation 案例不使用 original/private Gold 三元组。"
    links = "\n".join(f"- {link(name,case/name,case)}" for name in sources)
    # Keep the human page short; full historical reports stay in authority.
    def bullet(prefix):
        for line in prior_text.splitlines():
            if line.strip().startswith(prefix):
                return line.strip().removeprefix(prefix).strip()
        return None
    semantic = bullet("- 语义/模型结果：")
    execution = bullet("- 确定性执行结果：")
    if semantic is None:
        semantic = ("N/A（没有真实 Provider 语义评测）；原记录为离线确定性 operation-engine 通过。" if mode.startswith("offline")
                    else "原记录为正确拒绝该不受支持请求。" if outcome == "no_output"
                    else "原验收记录通过；本轮未重新评估模型语义或能力。")
    execution = execution or detail
    checks = []
    for line in prior_text.splitlines():
        if line.lstrip().startswith("-") and any(word in line for word in ("L0", "L1", "L2", "Preservation", "preservation", "Application", "Evidence validation", "Structural restoration", "Provider calls", "Runtime run ID", "Operations", "Operation types", "独立 Proof", "synthetic fallback")):
            checks.append(re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line.strip()))
    checks = checks[:14]
    if outcome == "generated":
        result_file = authority / "case-result.json"
        result_record = read(result_file) if result_file.exists() else read(authority / "verification.json")
        checks = [f"- 原记录 {key}：{value}" for key, value in result_record.items() if key in ("final_status", "audit_passed", "compile_reopen_passed", "schema_passed", "deterministic_gates_passed", "success", "compile_reopen_success", "formal_validation_issue_count")]
        execution = "确定性代码把最终 BIM JSON 编译为 IFC2X3；编译、重开及原验收结果见下表摘录。"
        role = "Generation 没有 repair 三元组。repair L0/L1/L2 与私有三元组 IFCCompare 为 N/A；生成专用 gates 以原记录为准。"
    else:
        role += " 若原评估包含私有删除身份或 mutation mapping，它们仅供修复后评估，不属于 Provider 输入。"
    no_output_link = "- [NO-REPAIR.md](NO-REPAIR.md)" if outcome == "no_output" else ""
    report_link = link("原权威报告", authority / "REPORT.md", case) if (authority / "REPORT.md").exists() else link("原运行材料", authority, case)
    text = f"""# {case_id}

状态：**{status}**；证据方式：`{mode}`。此次只整理展示，不改变原验收或 Phase 状态。

## 请求与输入

完整公共原文：[request.txt](request.txt)。下面是阅读摘要，文件原文未改写。

> {request[:350].strip().replace(chr(10), chr(10)+'> ')}

## 实际工作

{detail}

- **Provider 语义选择：** {semantic}
- **确定性执行：** {execution}
- **输入／私有评估边界：** {role}

## 直接文件

{links}
{no_output_link}

## 结果与限制

| 维度 | 结论与来源 |
|---|---|
| 语义结果 | {semantic} |
| 确定性执行 | {"正确无输出；Stage 2 / apply / publish 的原记录见下方" if outcome == "no_output" else "沿用原操作／编译结果；具体执行与 gates 见下方原记录摘录"} |
| 产物 | {outcome}；本轮只验证可发现性、来源一致性与 reopen |
| 证据合同 | {report_link}；原权威保持原位 |
| IFCCompare | {ifccompare} |
| genuine run ID | {run_id} |
| Provider 调用次数 | {calls} |
| 人工审查 | {status}；本轮不提升状态 |

### 原记录中的适用检查

{chr(10).join(checks) or '- 原报告未单列 reopen / L0 / L1 / L2 / atomicity / preservation 结果：未知；不得从文件存在推断通过。'}

未在原记录中单列的 atomicity、preservation 或其他门结果记为未知；正确无输出案的输出 reopen/L0/L1/L2 为 N/A。本轮的文件 reopen 只证明文件可打开，不代替这些语义和执行门。

完整过程：[evidence/README.md](evidence/README.md)。这里可进入 Provider attempts、ChangeSet、终端和评估材料；正文不重复展开 runtime 日志。
"""
    write(case / "REPORT.md", text)
    write(case / "evidence/README.md", f"# 过程与机器权威\n\n{link('Authoritative source bundle',authority,case/'evidence')}\n\n原 Provider attempts、请求、评估和发布材料保留原位；此目录不创造第二套验收事实。\n\nprior-REPORT.md（若存在）保存迁移前报告的原文字节，其中相对路径属于旧位置；当前有效入口以上面的 authority 为准。")
    record = {"case_id": case_id, "path": case.relative_to(collection).as_posix(), "status": status,
              "outcome": outcome, "evidence_mode": mode, "provider_calls": calls, "run_id": run_id,
              "authority": repo_path(authority), "original_role": original_role,
              "ifccompare": ifccompare, "artifacts": artifacts}
    if (case / "FILES.json").exists() and read(case / "FILES.json").get("schema_version") != "text2ifc/human-view-files/0.1":
        copy_exact(case / "FILES.json", case / "evidence/prior-FILES.json")
    write_json(case / "FILES.json", {"schema_version": "text2ifc/human-view-files/0.1", "case_id": case_id, "copies": [
        {"path": name, "authority": source, "sha256": sha(case/name)} for name, source in artifacts.items()]})
    return record


def finish_collection(path, title, workflow, status, cases, authority, note, references=()):
    payload = {"schema_version": SCHEMA, "collection_id": path.name, "workflow": workflow,
               "status": status, "authority": repo_path(authority), "cases": cases, "references": list(references),
               "scope": "human discovery only; source acceptance and evidence contracts remain authoritative"}
    if path.name == "plan07-v2":
        payload["r1_included"] = False
    write_json(path / "manifest.json", payload)
    write(path / "README.md", f"# {title}\n\n状态：{status}。{note}\n\n先读 [REPORT.md](REPORT.md)，逐行打开请求、IFC 与案例报告。\n\n机器权威：{link('原集合',authority,path)}。")
    rows = []
    for c in cases:
        case = path / c["path"]
        input_name = "02-damaged.ifc" if workflow == "repair" else "model.json"
        output_name = "03-repaired.ifc" if workflow == "repair" else "generated.ifc"
        if c["outcome"] == "no_output":
            output_name = "NO-REPAIR.md"
        rows.append(f"| {link(c['case_id'],case/'REPORT.md',path)} | {c['status']} / {c['evidence_mode']} | {link('请求',case/'request.txt',path)} | {link(input_name,case/input_name,path)} | {link(output_name,case/output_name,path)} | {c['provider_calls']} |")
    write(path / "REPORT.md", f"# {title}：逐案证据矩阵\n\n{note}\n\n本表按现有记录整理，不重新评定模型能力、人工审查或 Phase 状态。\n\n| 案例与结论 | 状态／证据类型 | 请求 | 输入 IFC／BIM JSON | 输出／无输出原因 | Provider calls |\n|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n\n" + "\n".join(references))
    return path


def build_reference():
    source = PROOF / "ifc-repair-success-cases"
    target = PROOF / "repair/phase11/reference-cases"
    cases = []
    for c in read(source/"manifest.json")["cases"]:
        authority = source / Path(c["report"]).parent
        case = target / Path(c["report"]).parent
        sources = {name: authority/name for name in ("01-original.ifc", "02-damaged.ifc", "03-repaired.ifc")}
        sources["request.txt"] = authority/"input/request.txt" if (authority/"input/request.txt").exists() else (authority/"input/request.json", "text")
        cases.append(finish_case(target,case,case_id=c["case_id"],authority=authority,sources=sources,
            status=c["status"],outcome="repaired",mode=c.get("provider_evidence_mode",c["provider"]),
            calls=0 if c["provider"] == "offline-deterministic" else "未知；见原 Provider evidence",
            run_id="N/A（离线确定性）" if c["provider"] == "offline-deterministic" else "未知；见原 authority 的 source-run / Provider 记录",
            original_role="private_ground_truth", prior_text=(authority/"REPORT.md").read_text(encoding="utf-8"),
            detail=f"请求涉及 {c.get('operation_count')} 个 operation：{c.get('operation_types',c.get('operation_type'))}。实际损伤、对象和确定性执行见原案例报告；不从 repaired 反推 Gold。",
            ifccompare="沿用原案例评估；本案属于 5 个 legacy_unverifiable 历史 Window 案，不得当作新的完整 Proof" if c["case_id"] in {"largebuilding-full-replication", "largebuilding-r22-repeat", "vvo-five-window", "advancedproject-five-window", "px4-five-window"} else "沿用原案例评估；三元组角色按原冻结记录，不在本轮重新计算 IFCCompare"))
    return finish_collection(target,"Phase 11 及此前 repair 参考案例","repair","accepted",cases,source,
        "当前主 manifest 为 16 案；live / replay / offline 分开陈述。早期同进程 Door 案用于历史对照，优先阅读 authority-public-repair 案。历史 24 案校验不代表当前全集。")


def build_plan07(source_root=None, target=None):
    from scripts.ifc_repair import install_plan07_human_proof as legacy
    source_root = source_root or legacy.DEFAULT_SOURCE_ROOT
    target = target or PROOF / "repair/phase12/plan07-v2"
    source_manifest = read(PROOF/"ifc-repair-success-cases/plan07-manifest.json")
    cases = []
    for c, spec, name in zip(source_manifest["cases"],legacy.ALL_CASES,PLAN_NAMES,strict=True):
        case = target/name
        authority = legacy._authority_case_root(source_root,spec)
        if not case.exists():
            case.mkdir(parents=True)
            fn = legacy._copy_offline_case if spec.evidence_mode.startswith("offline") else legacy._copy_live_case
            fn(source_root,case,spec)
        prior = archive_report(case)
        # Retain the migrated source files and their original FILES inventory.
        # A new view index binds exposed copies directly to machine authority.
        sources = {}
        for filename, source_name in (("01-original.ifc", "original.ifc"), ("02-damaged.ifc", "damaged.ifc"), ("03-repaired.ifc", "repaired.ifc")):
            if (case/filename).exists():
                sources[filename] = authority/source_name
        if sha(authority/"request.txt") != sha(case/"input/request.txt"):
            raise ValueError(f"public request authority mismatch: {authority}")
        sources["request.txt"] = authority/"request.txt"
        role = None if c["outcome"] != "repaired" else ("physical_fixture_non_private_audit" if c["evidence_mode"] == "live" else "private_ground_truth")
        cases.append(finish_case(target,case,case_id=c["case_id"],authority=authority,sources=sources,
            status="pending_human_review",outcome="repaired" if c["outcome"] == "repaired" else "no_output",
            mode=c["evidence_mode"],calls=c["provider_calls"],run_id=source_manifest["live_run_id"] if c["evidence_mode"]=="live" else "N/A（离线确定性）",
            original_role=role, prior_text=prior,
            detail={
                "beam-loadbearing": "输入是冻结 VVO 梁缺失案。确定性代码按冻结公共请求恢复矩形直梁及 LoadBearing 属性；原始梁身份和损伤映射仅供私有评估。",
                "column-loadbearing": "输入是冻结 VVO 柱缺失案。确定性代码恢复竖直矩形柱及 LoadBearing 属性；原始柱身份和损伤映射仅供私有评估。",
                "beam-column-atomic": "输入同时缺失梁和柱；确定性代码在同一原子 ChangeSet 中执行 add_beam 与 add_column。",
                "beam-material-present": "输入缺失一根具有材料配置的梁；确定性代码执行梁恢复，材料存在性以冻结 restoration 审计为准。",
                "column-material-absent": "输入缺失一根未配置材料的柱；确定性代码执行柱恢复，材料缺省状态以冻结 restoration 审计为准。",
                "four-family-atomic": "输入包含门、窗、梁、柱四类冻结损伤。确定性代码执行 6 个 operation，涵盖 add_beam、add_column、add_window_with_opening_to_wall、fill_existing_opening_with_door；整组按原子 ChangeSet 应用。",
                "live-complete": "公共请求给出缺失梁和柱的楼层、轴线与截面尺寸。Provider 产生恢复意图，确定性代码绑定目标后执行 add_beam 与 add_column，共 2 个 operation；original 仅为非私有物理对照。",
                "live-clarification": "公共请求要求恢复缺失柱。运行包含 clarification/resume；Provider 在澄清后给出意图，确定性代码执行柱恢复。澄清原文和精确参数位于机器权威。",
                "live-window-property": "公共请求要求修改现有窗的属性。Provider 选择属性意图，确定性代码执行属性修改；这是 property repair，不是被删除窗身份的恢复证明。",
                "program-guard": "请求含不受支持的 structural program；原证据要求 Stage 2=0、source unchanged、零 mutation / publish，因此正确不发布 repaired IFC。",
            }[name],
            ifccompare="N/A：仅物理对照，无 case-specific private Gold" if c["evidence_mode"]=="live" else "沿用已冻结 private restoration / comparator 记录；本次不重跑"))
    return finish_collection(target,"Phase 12 Plan 07 v2","repair","pending_human_review",cases,source_root,
        "6 个离线案例、3 个 genuine repaired 案例和 1 个 no-output guard；11 次 genuine 调用。R1 不包含在该集合中，r1_included=false。")


def build_r1():
    source=PROOF/"repair-milestone-r1"
    target=PROOF/"repair/phase12.1/r1"
    cases=[]
    for c in read(source/"manifest.json")["cases"]:
        case=target/c["case_id"]
        authority=source/c["authority_path"]
        prior=archive_report(case)
        sources={"request.txt":authority/"request.txt", "02-damaged.ifc":authority/"source.ifc"}
        if not sources["request.txt"].is_file():
            raise FileNotFoundError(sources["request.txt"])
        machine=read(source/"r1-20260902T152701658266Z-curated/manifest.json")
        mc=next(x for x in machine["cases"] if x["case_id"]==c["case_id"])
        if c["outcome"]=="repaired":sources["03-repaired.ifc"]=source/"r1-20260902T152701658266Z-curated"/mc["repaired_ifc"]
        if not sources["02-damaged.ifc"].is_file():
            state=read(authority/"terminal.json")
            raise ValueError(f"source binding missing for {c['case_id']}: {list(state)}")
        cases.append(finish_case(target,case,case_id=c["case_id"],authority=authority,sources=sources,status="accepted",outcome=c["outcome"],mode="live",
            calls=c["provider_calls"],run_id="r1-20260902T152701658266Z",prior_text=prior,
            detail=f"冻结 terminal class：{c['terminal_class']}。R1 从真实 IFC 和冻结请求出发，并非预先损伤的私有三元组 benchmark。具体属性、构件和阻断行为见下方逐案摘要。",
            ifccompare="N/A：R1 没有运行前冻结的 case-specific private triplet"))
    return finish_collection(target,"Repair Milestone R1","repair","accepted",cases,source/"r1-20260902T152701658266Z-curated",
        "原连续 run 12/12，40 次 genuine 调用；11 个 repaired、H4 正确无输出。沿用已记录独立 Proof 0.3；本整理不重新运行 curator。")


def build_generation():
    source=PROOF/"text2ifc-success-cases"
    target=PROOF/"generation/phase6.6/generation-examples"
    cases=[]
    for c in read(source/"manifest.json")["cases"]:
        provenance=read(source/c["provenance"])
        authority=(ROOT/provenance["ifc_source"]).parent
        sources={"request.txt":source/c["input"],"generated.ifc":source/c["ifc"],"model.json":authority/"candidate.json"}
        # The terminal case-result/verification selects this final directory;
        # no compile or regeneration is used to manufacture a replacement.
        prior=(authority/"report.md").read_text(encoding="utf-8") if (authority/"report.md").exists() else json.dumps(read(authority/"verification.json"),ensure_ascii=False,indent=2)
        cases.append(finish_case(target,target/c["proof_id"],case_id=c["proof_id"],authority=authority,sources=sources,status=c["status"],outcome="generated",
            mode="historical_authorized_deterministic_revision" if c["proof_id"]=="output-713-success" else "recorded_accepted_generation",
            calls="未知；见来源 Provider traces",run_id=read(authority/"case-result.json").get("case_id", "未知") if (authority/"case-result.json").exists() else "N/A（已授权确定性修订，无新 genuine run）",prior_text=prior,
            detail=f"原 IFC 记录为 {provenance['entity_counts'].get('IfcBuildingStorey')} 层、{provenance['entity_counts'].get('IfcSpace')} 个空间、{provenance['entity_counts'].get('IfcWall')} 面墙。model.json 来自最终来源目录的 candidate.json，IFC 沿用已验收副本。" + ("本案包含已授权的确定性边界修订，不是新 genuine run。" if c["proof_id"]=="output-713-success" else ""),
            ifccompare="N/A：generation 案例"))
    return finish_collection(target,"Generation 六个已记录验收案例","generation","accepted",cases,source,
        "集合跨 Phase 6.5/6.6，唯一归属放在 Phase 6.6；沿用原 manifest 的 accepted 记录。历史人工修改、调用次数未知和原 provenance 乱码均明确保留限制。")



def build_history():
    source = PROOF / "phase11-live-uat/uat-20260731T224900289758Z"
    target = PROOF / "repair/phase11/live-uat"
    raw = ROOT / "dataset/processed/ifc-repair/phase11-live-uat/uat-20260731T224900289758Z/unsupported-complex-door"
    context = raw / "runtime/runs/repair-091d667e6d334857aa364e8038ffd8e9/api-context.json"
    state = read(source / "unsupported/state.json")
    damaged = Path(state["source"]["reference"])
    if sha(damaged) != state["source"]["sha256"].removeprefix("sha256:"):
        raise ValueError("historical guard source fingerprint changed")
    case = target / "unsupported-complex-door"
    record = finish_case(target,case,case_id="unsupported-complex-door",authority=source/"unsupported",
        sources={"request.txt":(context,"repair_text"),"02-damaged.ifc":damaged},status="historical",outcome="no_output",mode="live",calls="1/0 (Stage 1/2)",
        run_id="repair-091d667e6d334857aa364e8038ffd8e9",
        detail="原请求要求 REVOLVING Door。Stage 1 后以 DOOR_OPERATION_TYPE_UNSUPPORTED 终止；Stage 2=0，没有 repaired IFC。旧 UAT 记录判定 contract_pass=true，本次只提供历史阅读入口。",
        ifccompare="N/A：unsupported 无输出")
    refs = []
    for name in ("largebuilding-live-deepseek-complete-door", "largebuilding-live-deepseek-clarified-door"):
        refs.append("- " + link(name, PROOF/"repair/phase11/reference-cases/door/surviving-opening"/name/"REPORT.md", target))
    return finish_collection(target,"Phase 11 历史 live UAT","repair","historical",[record],source,
        "原 UAT 共三案；两个成功案只引用 reference-cases，不重复收纳完整证据。本目录单独展示一个正确无输出案。",refs)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection",choices=["reference","plan07","r1","generation","history"],required=True)
    args=parser.parse_args()
    result={"reference":build_reference,"plan07":build_plan07,"r1":build_r1,"generation":build_generation,"history":build_history}[args.collection]()
    print(result)


if __name__ == "__main__":
    raise SystemExit(main())
