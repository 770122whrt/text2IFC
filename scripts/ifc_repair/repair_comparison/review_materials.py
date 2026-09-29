"""Readable, explicitly pending human-review material."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from scripts.ifc_repair.repair_comparison.contracts import damage_profile


def render_validation(report: dict[str, Any]) -> str:
    status = "PASS" if report["passed"] else "FAIL"
    return f"""# 损坏 IFC 格式校验：{status}

- 文件：[冻结 damaged.ifc](private/mutation/damaged.ifc)；公开副本与其字节一致。
- 校验器：{report['validator']}，IfcOpenShell {report['version']}。
- Schema：{report['ifc_schema']}；EXPRESS rules：已执行。
- 诊断数量：{report['diagnostic_count']}。
- SHA-256：`{report['ifc_sha256']}`。
- [机器结果与全部诊断](private/damaged-ifc-validation.json)。

PASS 表示该文件通过本地 IFC schema／EXPRESS 校验，构件缺失仍是待修任务。
这不表示已经完成修复，也不代表 buildingSMART 在线验证服务已验证。

可在仓库根目录独立复查：

```powershell
.\\.venv\\Scripts\\python.exe -m ifcopenshell.validate --rules <本题 damaged.ifc 的完整路径>
```
"""


def render_review(definition: dict[str, Any], checks: dict[str, Any], visual: dict[str, Any] | None = None) -> str:
    source, task = definition["source"], definition["task"]
    facts = definition["clarification"]["required_user_facts"]
    lines = [f"# {definition['case_id']}：{task['summary']}", "", "> 状态：pending_human_review。开发样例，不计入正式成绩；没有运行修复模型，也没有 repaired.ifc。", "", "## 先看这几个文件", "", "- [公开修复要求](public/request.txt)", "- [损坏 IFC：给被测系统的副本](public/model.ifc)", "- [损坏前参考 G](private/reference.ifc)", "- [冻结损坏 D](private/mutation/damaged.ifc)", "- [私有任务条件](private/task.json)／[受控答复卡](private/answer-card.json)", "- [完整检查记录](private/checks.json)／[损坏记录](private/mutation/mutation_manifest.private.json)", "", "上述整目录仅供审阅。后续只导出 public/；目录分层本身不证明运行时沙箱隔离。", "", "## 来源、许可与样本身份", "", f"- 源：`{source['path']}`", f"- SHA-256：`{source['sha256']}`", f"- 许可：{source['rights']}；登记用途：{source['approved_use']}。", f"- 场景族：`{source['scene_family']}`；开发中已使用，正式未见样本应排除同族和变体。", f"- 参考角色：{source.get('reference_role', '本题损坏前参考；尚待人工确认，不自动视为私有 Gold 真值。')}", ""]
    for i, path in enumerate(source.get("attribution_files", [])):
        lines.append(f"- [来源／许可材料 {i + 1}](private/attribution/{i + 1:02d}-{Path(path).name})")
    profile = damage_profile(task["required_products"])
    lines += ["", f"损伤规模：{profile['level']}，主目标 {profile['target_count']} 个，组合 {profile['composition']}。洞口等附属结构不重复计作主目标；规模不等同于实际难度。", "", "[损坏 IFC 的格式校验结果](IFC-VALIDATION.md)"]
    lines += ["", "## 公开请求与可解性", "", "```text", definition["request"]["text"], "```", "", *[f"- {basis}" for basis in definition["request"]["basis"]], "", "## 实际损坏与检查", "", "| 对象类别 | 损坏前 | 损坏后 |", "|---|---:|---:|"]
    for key in sorted(set(checks["counts_before"]) | set(checks["counts_after"])):
        before, after = checks["counts_before"].get(key, 0), checks["counts_after"].get(key, 0)
        if before != after:
            lines.append(f"| {key} | {before} | {after} |")
    lines += ["", *[f"- {key}: `{value}`" for key, value in checks["checks"].items()], f"- 原生 schema＋EXPRESS 诊断：G={checks['source_validation']['diagnostic_count']}，D={checks['damaged_validation']['diagnostic_count']}，新增={checks['new_native_diagnostic_count']}。这是制题检查，不是修复成绩。", "", "[实际 IFC 几何包围盒俯视定位图](private/location.svg)仅用于定位；完整形状、开向和外观请打开 IFC 查看。", "", "## 怎样才算完成：待你确认", "", f"主目标分母：{sum(task['required_products'].values())}；应修关系分母：{len(task['required_relations'])}。", "", *[f"- {text}" for text in task["acceptance"]], "", "| 应修关系 | 依据 |", "|---|---|"]
    lines += [f"| {row['ifc_class']} / {row['id']} | {row['basis']} |" for row in task["required_relations"]]
    lines += ["", "公开请求只表达安装、开洞及楼层位置，不给 IFC 关系术语或修复方法。评分仍检查这些任务必需的语义；能否由模型自然补全，留待获准后的真实实验验证。类型关联不作为强制分母，允许实例表达等价语义。"]
    if visual:
        removed = visual["removed_target"]
        def readable_bounds(bounds):
            return [[round(value, 4) for value in axis] for axis in bounds] if bounds else None
        lines += ["", "## 视觉检查与具体删除对象", "", "[打开同步视角网格查看器](VIEW.html)：红色为 G 中删除的对象，蓝色为保留参照；两侧共用世界坐标和视角。仅供人工审阅，不能送入被测系统。", "", f"删除对象：`{removed['class']}`，Tag=`{removed['tag']}`，Name=`{removed['name']}`。", f"删除前世界包围盒（米，依次X/Y/Z）：`{readable_bounds(removed['bounds'])}`。下表坐标仅为阅读四舍五入，原始精度见JSON。", "", "| 保留对象 Tag / GUID | 世界包围盒（米） | G/D 放置、顶点、面索引 |", "|---|---|---|"]
        lines += [f"| {row['tag'] or row['guid']} | `{readable_bounds(row['bounds_d_m'])}` | {'完全一致' if row['unchanged'] else '不一致或不可用'} |" for row in visual["references"]]
        lines += ["", f"网格数量 G/D：{visual['mesh_count']['G']}/{visual['mesh_count']['D']}；生成失败：{len(visual['mesh_errors']['G'])}/{len(visual['mesh_errors']['D'])}。", "[具体网格核对和诊断](private/visual-inspection.json)。查看器使用三角网格，但不渲染原材质，也不代替原生 IFC 校验。"]
    lines += ["", "允许替代：", "", *[f"- {text}" for text in task["allowed_alternatives"]], "", "保全要求：", "", *[f"- {text}" for text in task["preservation"]], "", f"匹配：{task['matching']}", f"数值规则草案：`{task['tolerances']}`；尚未正式冻结。", "", "## 澄清与答复卡", ""]
    if not facts:
        lines.append("本题拟为信息充分题；公开参照已足以确定目标。仍允许普通提问，不预设必须提问。")
    for fact in facts:
        lines += [f"- 必要事实 `{fact['fact_id']}`：{fact['why_required']}", f"- D 无法唯一决定：{fact['why_not_in_d']}", f"- 可行选项：{'；'.join(fact['allowed_answers'])}", f"- 答复草案：**{fact['answer']}**", f"- 草案依据：{fact['answer_basis']}", f"- 回复范围：{fact['reply_scope']}"]
    lines += ["", "只回答实际问到的事实；卡外问题留待人工处理，不查 G 临时补答案。未问碰巧做对与合格澄清分别计分。", "", "## 请你审阅", "", "1. 损坏是否符合题意，有没有误伤其他部分？", "2. 公开请求是否自然且充分；澄清题是否确有必要的用户选择？", "3. 主目标、应修关系、允许替代和保全条件是否合理？", "4. 答复卡草案及拟定容差是否接受，还是需要修改？", "", "请按本题编号给出接受／修改意见。程序不会自动写 accepted；任何题意、输入或答复事实变更均需重新审阅。", ""]
    return "\n".join(lines)


def render_location(checks: dict[str, Any]) -> str:
    entries = [("host in D", checks["damaged_host"], "#ced5dc"), ("removed target in G", checks["target"], "#df5a49")]
    entries += [(f"reference {i + 1}", row, "#287c9b") for i, row in enumerate(checks["public_references"])]
    entries = [entry for entry in entries if "bounds_world_m" in entry[1]]
    if not entries:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="200"><text x="20" y="60">No geometry in this fixture.</text></svg>\n'
    min_x = min(row["bounds_world_m"][0][0] for _, row, _ in entries)
    max_x = max(row["bounds_world_m"][0][1] for _, row, _ in entries)
    min_y = min(row["bounds_world_m"][1][0] for _, row, _ in entries)
    max_y = max(row["bounds_world_m"][1][1] for _, row, _ in entries)
    scale = min(700 / max(max_x - min_x, 0.1), 350 / max(max_y - min_y, 0.1))
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="700" viewBox="0 0 900 700">', '<rect width="900" height="700" fill="white"/>', '<text x="30" y="30" font-size="18">World XY bounding boxes (metres) - private review only</text>']
    for i, (label, row, color) in enumerate(entries):
        bounds = row["bounds_world_m"]
        x, y = 60 + (bounds[0][0] - min_x) * scale, 70 + (max_y - bounds[1][1]) * scale
        width, height = max((bounds[0][1] - bounds[0][0]) * scale, 2), max((bounds[1][1] - bounds[1][0]) * scale, 2)
        svg.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{width:.3f}" height="{height:.3f}" fill="{color}" fill-opacity="0.6" stroke="{color}"/>')
        svg.append(f'<text x="30" y="{490 + i * 25}" fill="{color}" font-size="13">{escape(label)}: {escape(str(row["guid"]))}</text>')
    svg += ['<text x="30" y="670" font-size="13">Removed target shown at G position. Open IFC for exact shape and swing.</text>', '</svg>\n']
    return "\n".join(svg)
