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


def render_formal_review(task, checks, references, *, geometry_audit=None, subset_report=None):
    """Names and measurement evidence belong to human review, not requests."""
    def cell(value):
        return str(value if value is not None else '未命名').replace('|', r'\|').replace('\n', ' ')

    def xy(values):
        return ', '.join(f'{v:.6f}' for v in values[:2])

    review = task.get('review', {})
    status = review.get('status', 'pending_human_review')
    accepted = status in {'accepted', 'accepted_by_delegation'}
    if status == 'accepted_by_delegation':
        state = '**委托技术审题已接受（accepted_by_delegation）**。'
    elif status == 'accepted':
        state = '**审题记录已接受（accepted）**。'
    elif status == 'pending_human_review':
        state = '**待人工审阅（pending_human_review）**。'
    else:
        state = f'**审题记录状态：{cell(status)}**。'
    metrics = task.get('metrics') or {}
    frozen = metrics.get('formal_scoring_frozen') is True
    scoring = ('评分合同已冻结' + (f'，版本 `{metrics["policy_version"]}`' if metrics.get('policy_version') else '') + '。'
               if frozen else '评分合同为草案，尚未正式冻结。')
    title = task['source']['task_proposal'].get('description', '局部修复')
    lines = [f'# {task["case_id"]}：{title}', '', state, '',
        '本页记录制题与审题依据；模型是否运行、正式提交和修复成绩以各方法的运行记录为准。']
    if review.get('reviewer'):
        lines += ['', f'审题者：{cell(review["reviewer"])}；审题类型：`{cell(review.get("kind", "未记录"))}`。']
    if 'human_viewed' in review:
        viewed = review['human_viewed']
        recorded = str(viewed).lower() if isinstance(viewed, bool) else cell(viewed)
        lines += [f'查看记录：`human_viewed={recorded}`。' + ('未标记用户已逐题亲自查看。' if viewed is False else '')]
    if review.get('reviewed_at'):
        lines += [f'审题时间：`{review["reviewed_at"]}`。']
    if status == 'accepted_by_delegation':
        authorization = review.get('authorization') or {}
        lines += ['', '用户委托原话：', '']
        lines += ['> ' + line for line in str(authorization.get('user_quote', '委托原话未记录')).splitlines()]
        lines += ['', f'委托时间：`{authorization.get("at", "未记录")}`。'
                  '该记录表示按用户委托完成技术审题，不表示用户已打开 usBIM 逐题确认。',
                  '[委托技术审题证据](private/technical-review.json)。']
    lines += ['', ('后续复审可检查' if accepted else '请你检查') + '：在 usBIM 等查看器中构件与损伤能否看清，'
        '公开请求是否合理、是否符合希望修复的内容。毫米尺寸、坐标、楼层、参照一致性和保全由开发侧核验，不要求你手工量测。', '',
        '- [完整损坏前原件 G](private/reference.ifc)',
        '- [完整损坏 IFC D：正式公开输入](public/model.ifc)',
        '- [公开请求](public/request.txt) · [格式校验](IFC-VALIDATION.md) · [来源与许可](private/SOURCE-LICENSE.md)', '',
        f'登记源角色：`{task["source"].get("source_role", "未记录")}`。G 仅为私有制题／评估参考，不作为被测输入。', '',
        '本地 schema／EXPRESS 校验只说明相应格式规则检查结果，不等于修复完成，'
        '也不代表 buildingSMART 在线验证或 usBIM 导入／显示已成功。', '',
        '## 哪些原件被损伤', '',
        '下表 Name 是原 IFC 的真实名称，仅用于人工查找。重复名称用位置区分；名称中的数字不作为尺寸依据。'
        '这些身份不写入公开请求，也不发送给被测模型。', '',
        '|原件 Name|类别|损伤|原洞口平面中心 X, Y（m）|',
        '|---|---|---|---|']
    for item in checks['targets']:
        position = [sum(b) / 2 for b in item['opening']['bounds_world_m']]
        damage = '删除门，保留空洞口' if item['preserve_opening'] else '删除构件及洞口，恢复连续墙体'
        lines.append(f'|{cell(item["target"].get("name"))}|{item["target"]["class"]}|{damage}|{xy(position)}|')
    lines += ['', '保留参照：', '', '|原件 Name|类别|', '|---|---|']
    lines += [f'|{cell(r.get("name"))}|{r["class"]}|' for r in references]
    lines += ['', '## 公开请求', '', task['request'], '', '## 开发侧数值核验', '']
    if geometry_audit and geometry_audit['passed']:
        lines += ['已重开 G/D，独立从三维网格、IFC 长度单位、洞口和楼层重算下表；公开坐标按三位小数表达。'
                  '名义尺寸与带框构件外包尺寸分别记录，检查误差不作为正式评分容差。', '',
                  '|目标 Name（原洞口 X, Y，m）|请求宽×高（mm）|IFC 名义宽×高（mm）|实测洞口宽×高（mm）|洞底距楼层标高（mm）|',
                  '|---|---|---|---|---:|']
        targets_by_step = {item['source_step_id']: item for item in checks['targets']}
        for item in geometry_audit['targets']:
            pairs = [' × '.join(f'{v:g}' for v in item[k]) for k in ('requested_dimensions_mm', 'nominal_dimensions_mm', 'opening_dimensions_mm')]
            target = targets_by_step[item['step_id']]
            position = [sum(b) / 2 for b in target['opening']['bounds_world_m']]
            identity = f'{cell(target["target"].get("name"))}（{xy(position)}）'
            lines.append(f'|{identity}|{pairs[0]}|{pairs[1]}|{pairs[2]}|{item["opening_sill_mm"]:g}|')
        lines += ['', *geometry_audit.get('notes', []), '',
                  '[完整数值、参照和原件几何核验](private/geometry-review.json)。这是制题检查；'
                  '数值证据本身不代表用户亲自审阅或模型修复成功。']
    else:
        lines += ['完整请求数值核验尚未记录，不能据此进入正式实验。']
    if subset_report:
        lines += ['', '## usBIM 局部查看', '',
            '[局部原件 G](private/review-original.ifc) · [局部损坏 D](private/review-damaged.ifc)。', '',
            '这对 IFC 只供查看：保留原目标、参照、宿主墙及墙上的完整洞口／填充关系，移除其余遮挡构件；'
            '空间层级、坐标、几何和表达上下文保持原样。它们不替换完整 G/D，也不能用于正式实验输入或评分。', '',
            '先打开局部 G 确认构件能显示，再看局部 D 的缺失与连续墙面。完整模型中按表中 Name、楼层和位置查找；'
            '地下层可先单独显示，或隐藏上层、楼板及空间体。若局部 G 仍无法显示目标，需继续核查 usBIM 的导入／显示兼容性。', '',
            f'局部 G/D 的 schema＋EXPRESS 均零诊断，所有保留网格及位置与完整原件逐项相同；'
            f'产品数 {subset_report["G"]["product_count"]}/{subset_report["D"]["product_count"]}。'
            '[查看副本核验记录](private/review-subsets.json)。未直接验证用户当前 usBIM 画面。']
    lines += ['', '## 局部对照图', '',
        '[可旋转的同步网格查看器](VIEW.html)。下面是实际 IFC 网格的水平剖切；红色为 G 中删除构件，D 的十字仅标注删除位置，蓝色为保留参照。', '',
        '![同尺度局部剖切对照](REVIEW.png)', '',
        '## 修复验收含义', '',
        f'主目标 {task["required_product_count"]} 个；{task["damage_profile"]["level"]}。'
        '修复需恢复实际构件及洞口／宿主／楼层关系，保留范围外对象。允许新身份和等价序列化。', '',
        scoring, '', '## 澄清与事前答复卡（私有）', '']
    clarification = task.get('clarification') or {}
    required = clarification.get('required_user_facts', [])
    facts = clarification.get('facts') or {}
    if not required:
        lines += ['本题未登记必须补充的用户事实；仍提供普通问答通道，不预设模型必须提问。']
    for required_fact in required:
        fact_id = required_fact if isinstance(required_fact, str) else required_fact.get('fact_id', required_fact.get('id', '未记录'))
        fact = facts.get(fact_id, required_fact if isinstance(required_fact, dict) else {})
        lines += [f'- 缺失事实 `{fact_id}`：{fact.get("why_needed", fact.get("why_required", fact.get("field", "缺项说明未记录")))}']
        if fact.get('target_id'):
            lines += [f'  对应目标：`{fact["target_id"]}`。']
        if fact.get('answer'):
            label = '事前认可答复' if accepted else '事前编写答复（待审）'
            lines += [f'  {label}：**{fact["answer"]}**']
        else:
            lines += ['  答复未记录，不能临时从 G 补造。']
        if fact.get('basis') or fact.get('answer_basis'):
            lines += [f'  答复依据：{fact.get("basis", fact.get("answer_basis"))}']
    lines += ['', '只回答实际问到的事实；未问到的事前答复不提前提供，卡外问题保留待处理。'
        '执行时不查 G 临时补答案；未问碰巧做对与合格澄清分别计分。', '',
        ('用户可按题号给出后续复审或修改意见；当前委托／接受状态以本页记录为准。' if accepted else
         '请按题号给出请求合理性与查看结果的接受／修改意见；开发侧数值核验不代替实际审阅。'), '',
        'private/、REVIEW 和查看器仅用于审阅／评估。初始被测输入只含 public/ 中两个文件；'
        '以上缺失事实与答复只在合格提问后按卡提供，不回填公开请求。', '']
    return '\n'.join(lines)


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
