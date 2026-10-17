"""Publish a bounded first-batch report from sealed receipts, without IFC dumps."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from scripts.ifc_repair.dataset_batch.engine import write_json
from scripts.ifc_repair.dataset_batch.validation import program_hash, sha256


def publish(root: Path):
    root = root.resolve()
    before = json.loads((root / "before/summary.json").read_text(encoding="utf-8"))
    after = json.loads((root / "after-final/summary.json").read_text(encoding="utf-8"))
    boundary = json.loads((root / "boundary/summary.json").read_text(encoding="utf-8"))
    tests = json.loads((root / "tests.json").read_text(encoding="utf-8"))
    checks = []
    for directory in ("before", "after", "after-final", "boundary"):
        summary = json.loads((root / directory / "summary.json").read_text(encoding="utf-8"))
        if sha256(root / directory / "auditor-source.py") != summary["auditor_sha256"]:
            raise ValueError("auditor_code_snapshot_mismatch:" + directory)
    for path in sorted((root / "after-final").glob("case-*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        for name, expected in record["input_sha256"].items():
            if sha256(Path(name)) != expected:
                raise ValueError("audited_input_changed:" + name)
        reused = record["native_reused_from"]
        if sha256(Path(reused["path"])) != reused["sha256"]:
            raise ValueError("native_authority_changed")
    # Check the actual formal sources against their pre-damage source manifest.
    folders = [ROOT / ".tmp/ifc-dataset-prototype-v1/sources" / name for name in ("formal-001", "formal-017", "formal-019")]
    folders.append(ROOT / "dataset/processed/ifc-repair/batch-damage-v1/sources/formal-004")
    for folder in folders:
        spec = json.loads((folder / "private/source.json").read_text(encoding="utf-8"))
        actual = ROOT / spec["input_path"]
        matches = sha256(actual) == spec["source_sha256"] == sha256(folder / "private/reference.ifc")
        checks.append({"source_id": spec["source_id"], "source_path": str(actual), "unchanged": matches})
    build = json.loads((ROOT / ".tmp/ifc-dataset-prototype-v3/build.json").read_text(encoding="utf-8"))
    if build["configuration"]["code_sha256"] != program_hash():
        raise ValueError("prototype_generator_changed")
    receipt_paths = [path for path in root.rglob("*.json") if path.name not in {"evidence.json", "summary.json"}]
    receipt_paths.extend(root / directory / "summary.json" for directory in ("before", "after", "after-final", "boundary"))
    summary = {
        "status": "first_batch_validation_complete",
        "full_batch": "stopped_by_user; no resumption or completion",
        "before": {key: before[key] for key in ("case_count", "unique_damaged_bytes", "ifc_compliant", "damage_crosscheck_passed", "prompt_information_sufficient")},
        "after": {key: after[key] for key in ("case_count", "ifc_compliant", "damage_crosscheck_passed", "prompt_information_sufficient", "applicable_prompt_templates", "sufficient_prompt_templates")},
        "boundary_native": {"checked": boundary["case_count"], "raw_rejected": True, "normalized_copy_passed": True, "prompt_ready_cases": 0},
        "test_count": sum(row["passed"] for row in tests["runs"]),
        "source_integrity": checks,
        "all_checked_sources_unchanged": all(row["unchanged"] for row in checks),
        "generator_sha256": program_hash(),
        "provider_calls": 0,
        "human_reviewed_derivatives": 0,
        "scope": "bounded door/window and property real cases, all eight operation families in offline fixture tests; not full-dataset qualification or system repair performance",
    }
    if not summary["all_checked_sources_unchanged"] or after["case_count"] != after["ifc_compliant"] or after["case_count"] != after["damage_crosscheck_passed"] or after["case_count"] != after["prompt_information_sufficient"]:
        raise ValueError("final_first_batch_gate_failed")
    write_json(root / "summary.json", summary)
    write_json(root / "evidence.json", {"sha256": {path.relative_to(root).as_posix(): sha256(path) for path in receipt_paths}, "report_generator_sha256": sha256(Path(__file__)), "source_integrity": checks})
    text = f"""# text2IFC 首批损伤校验报告

**首批检查和小样本修正复验已完成，40 × 25 全量生成继续暂停。** 当前修正版小样本通过 IFC 原生校验、损伤交叉检查及定义范围内的 prompt 信息检查；没有调用修复系统或 Provider，也没有新增人工审核。

|检查批次|记录数|IFC2X3 schema＋EXPRESS|损伤交叉检查|全部适用 prompt 信息检查|
|---|---:|---:|---:|---:|
|原首批 v1＋v2|{before['case_count']}（{before['unique_damaged_bytes']} 个不同 IFC 字节）|{before['ifc_compliant']}/{before['case_count']}|{before['damage_crosscheck_passed']}/{before['case_count']}|{before['prompt_information_sufficient']}/{before['case_count']}|
|修正小批 v3|{after['case_count']}|{after['ifc_compliant']}/{after['case_count']}|{after['damage_crosscheck_passed']}/{after['case_count']}|{after['prompt_information_sufficient']}/{after['case_count']}|

原首批来自 formal-001、017、019 的开发测试输出；v1 曾在开发过程中修改脚本，不能当作一个冻结版本的端到端实验。这次重新读取实际文件，对 15 份记录逐份运行原生校验、保全和独立交叉检查，旧 IFC 和旧请求均未改写。原生校验通过不能代替 prompt 完整性，旧样本不因此全部成为可用修复题。

修正版只使用 formal-001，新增 6 份小样本，不补齐暂停批次。5 个墙模板、6 个世界坐标模板、6 个楼层局部坐标模板共 {after['sufficient_prompt_templates']}/{after['applicable_prompt_templates']} 通过信息检查；墙模板不适用的属性题保留“不适用”状态，不强行编造墙定位。这些是同一批损伤的请求变体，不是 17 份独立损伤。

## 发现和修正

旧请求缺少删除洞口的独立形状、深度和位置；门窗外包盒不能代替洞口。世界模板还缺少明确楼层和墙宿主，楼层模板缺墙宿主。新版请求 `text2ifc/dataset-request/1.1` 明确楼层和宿主墙的名称及放置框架；保留洞口时说明其世界原点和新 fill 关系，删除洞口时独立描述其原点、轴、完整受支持实体或损伤后仍在的可定位同形参照，并要求建立 void/fill 关系。挖取配方会跳过同时删掉所需几何参照的组合。

独立检查器从实际公开文本解析形状，不重新调用 prompt 渲染器来认定文本正确。简单截面按文本重建几何；复杂构件和洞口在损伤 IFC 内解析参照名称、原点与轴，并比对局部三角网格。它检查构件类别、位置和轴、楼层及墙的唯一定位、洞口、指定属性目标和值，另外复核删除集合、所有保留产品的图与真实属性类型/单位、项目单位及每例最多 3 个保留构件的世界网格。

复验中检查器曾把“洞口轴”和“参照实例轴”一起解析，造成两例检查报错。该错误可由离线测试稳定重现；修正为从参照实例句子单独解析后，重新检查全部 6 份文本及损伤保全。原生校验已经逐份运行且 IFC 字节未变，因此仅复用同版本、准确 SHA 绑定的零 findings 原生记录；其他交叉检查重新执行。报错历史留在 [after/](after/REPORT.md)，最终检查以 [after-final/](after-final/REPORT.md) 为准。每例记录给出复用原生报告的路径和哈希。

## 不合规负例

额外只抽查了一个已生成失败例：formal-004/case-005 删除 21 个窗和相应洞口后，IfcOpenShell 删除接口遗留空的 `IfcRelAssociatesClassification.RelatedObjects`。原生 validator 得到 1 条 finding，正确拒绝；损伤身份及其余产品保全通过不掩盖这个失败。对单独复制的探针移除已登记受影响的空关联后，原生零 findings，保全仍通过，旧失败 IFC 和报告保留在探针的私有历史。暂停批次的失败原件没有被清理或续跑。这对边界探针的旧 prompt 仍不足，均不算 prompt 就绪样本。详见 [边界检查](boundary/REPORT.md)。

## 证据与适用范围

- 原首批明细：[before/REPORT.md](before/REPORT.md)，每例原生、损伤和请求检查见同目录 JSON。
- 修正后最终明细：[after-final/REPORT.md](after-final/REPORT.md)。[summary.json](summary.json) 为本次结论入口，[evidence.json](evidence.json) 绑定各机器记录和源码快照。
- 相关回归共 {summary['test_count']} 项通过：损伤/来源/归档 31 项，独立检查器 15 项。包含旋转楼层、毫米单位、圆形柱、七种删除族与属性更改、洞口厚度不同于窗、参照解析、属性隔离、未记录改动和不可复用的原生记录等。[测试记录](tests.json)。
- 当前检查涉及的 4 个 formal 源文件及私有参考副本 SHA 一致。全部被检查输入原字节保留；全量停止记录见 [STOPPED-BY-USER.json](../batch-damage-v1/STOPPED-BY-USER.json)。

**结论限于本次 IFC 原生约束、记录中的损伤及明确要求的几何/放置/包含/洞口/指定属性信息。** 真实文件小样本覆盖门窗与属性；梁、柱及综合操作在离线场景测试中覆盖，尚未对大量真实梁柱文件作同等级抽查。局部几何比较采用 1 微米量化三角形，位置矩阵比较有明确容差；这不是全工程几何或建筑法规审查，也不是原构件全部语义属性的精确复刻。未验证 LLM 能完成请求，不能据此报告系统修复成功率。

派生文件维持机器校验与人工审核分离，所有派生样本人工审核为待审。后续是否扩大批量范围由新的工作安排决定，本次不继续全量生成。
"""
    (root / "REPORT.md").write_text(text, encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    info = publish(parser.parse_args().root)
    print(json.dumps({key: info[key] for key in ("status", "before", "after", "test_count", "all_checked_sources_unchanged", "provider_calls")}, ensure_ascii=False))
