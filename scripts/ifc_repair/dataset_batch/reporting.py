from __future__ import annotations

import collections
import csv
import json
from pathlib import Path

from .engine import write_json
from .validation import sha256


def summarize(root: Path) -> dict:
    root = Path(root)
    plan = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    results = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((root / "sources").glob("*/result.json"))]
    cases = [case for result in results for case in result.get("cases", [])]
    passed = [case for case in cases if case["status"] == "passed"]
    types = collections.Counter(case["family"] for case in passed)
    severities = collections.Counter(case["severity"] for case in passed)
    sampling = json.loads((root / "sampling.json").read_text(encoding="utf-8")) if (root / "sampling.json").exists() else None
    target = plan["cases_per_source"] * len(plan["sources"])
    report = {"schema_version": "text2ifc/ifc-repair-dataset-summary/1.0", "status": "complete" if len(passed) == target and len(results) == len(plan["sources"]) and all(row["source_unchanged"] for row in results) and (sampling is None or sampling["passed"]) else "incomplete", "source_models": len(results), "formal_mothers": sum(spec["kind"] == "formal" for spec in plan["sources"]), "external_mothers": sum(spec["kind"] == "external" for spec in plan["sources"]), "unique_source_bytes": len({spec["source_sha256"] for spec in plan["sources"]}), "target_cases": target, "attempted_cases": len(cases), "machine_validated_cases": len(passed), "failed_cases": len(cases) - len(passed), "human_reviewed_derivatives": 0, "all_sources_unchanged": bool(results) and all(row["source_unchanged"] for row in results), "provider_calls": 0, "system_pilot": "deferred_by_user", "family_counts": dict(types), "severity_counts": dict(severities), "prompt_counts": {frame: sum(case["prompt_templates"][frame]["applicable"] for case in passed) for frame in ("host_wall", "world", "storey_local")}, "sampling": {key: sampling[key] for key in ("checked_samples", "passed_samples", "passed", "checked_families")} if sampling else None, "source_results": [{key: result[key] for key in ("source_id", "status", "target_cases", "attempted_cases", "passed_cases", "source_unchanged", "elapsed_seconds")} for result in results], "sources_manifest_sha256": sha256(root / "sources.json")}
    write_json(root / "summary.json", report)
    with (root / "cases.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        columns = ["case_id", "path", "status", "family", "severity", "property_changes", "machine_validated", "human_reviewed", "source_sha256", "damaged_sha256"]
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader(); writer.writerows(cases)
    lines = ["# text2IFC 批量损伤数据集", "", f"状态：**{report['status']}**。{report['source_models']}个母IFC；目标{target}份，机器校验通过{len(passed)}份，失败记录{len(cases)-len(passed)}份。", "", "系统小测及后续内容实验按用户要求暂缓；Provider调用为0。派生样本逐项机器校验，人工审核通过数为0。母本历史认可与委托技术复核按来源原记录保留，不传给派生样本。", "", "统一机器检查：IfcOpenShell schema＋EXPRESS、写出重开、全部未删除产品的前向图/实例属性/类型/材料/楼层/void-fill关系保全、损伤记录匹配、原件SHA-256不变和Prompt删除身份隔离。机器检查不等同人审、工程性能验证或系统修复成功。", "", "[全部样本索引](cases.csv) · [机器汇总](summary.json) · [母本及许可](sources.json) · [抽样记录](sampling.json)", "", "公开修复输入仅为每题public/model.ifc和一份request-*.txt；private目录含源参考与损伤映射，不能给被测系统。同母本/建筑族/模板变体按来源标识，不当作独立建筑；本批未建立训练/验证/测试划分。", "", "## 损伤分布", "", "|操作族|通过数|", "|---|---:|", *[f"|{name}|{count}|" for name, count in sorted(types.items())], "", "## 母本与结果", "", "|母本|许可|机器通过/目标|查看|", "|---|---|---:|---|"]
    by_source = {spec["source_id"]: spec for spec in plan["sources"]}
    for result in results:
        identifier = result["source_id"]
        lines.append(f"|{identifier}|{by_source[identifier]['license']}|{result['passed_cases']}/{result['target_cases']}|[来源](sources/{identifier}/SOURCE.md) · [结果](sources/{identifier}/result.json)|")
    lines += ["", "## 抽样检查", ""]
    if sampling:
        lines += [f"{sampling['passed_samples']}/{sampling['checked_samples']}份抽样通过；检查删除身份、属性真实前后值/类型、世界与楼层局部坐标、实际Prompt文本及每例最多3个保留构件的世界网格。抽样属于机器/Agent检查，没有新增用户人审标注。", ""]
    else:
        lines += ["尚未执行抽样。", ""]
    (root / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return report
