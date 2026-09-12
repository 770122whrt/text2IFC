"""Build pending human reports only after both independent and visual reviews."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910'
OUT = BASE/'failure-recovery-rerun-20260910'

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, value):
    with p.open('x', encoding='utf-8') as f:
        if isinstance(value, str):
            f.write(value)
        else:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')

summaries = {}
for branch in ('A-revise', 'B-retain'):
    folder = OUT/branch
    execution = read(folder/'execution.json')
    checks = read(folder/'review-checks.json')
    visual = read(folder/'visual-review.json')
    type_checks = read(folder/'independent-type-checks.json')
    assert execution['status'] == 'compiled'
    assert checks['independent_status'] == 'passed' and not checks['failed_checks']
    assert visual['status'] == 'assistant_review_complete'
    assert type_checks['status'] == 'passed'
    runtime = Path(execution['run_dir'])
    audit = read(runtime/'audit/audit-report.json')
    assert audit['recommendation'] == 'accept' and not audit['blocking']
    assert checks['ifc_sha256'] == sha(folder/'generated.ifc') == sha(runtime/'output.ifc')
    before, after = execution['budget_before'], execution['budget_after']
    attempts = after['attempts'][len(before['attempts']):]
    actual = [a for a in attempts if a['status'] == 'completed']
    assert all(a['status'] != 'reserved' for a in after['attempts'])
    concerns = audit['design_review']['concerns']
    if branch == 'B-retain':
        assert any(c['status'] == 'retained_known_issue' for c in concerns)
        assert checks['clearance']['zero_gap_count'] == 3
    else:
        assert checks['clearance']['zero_gap_count'] == 0
    summary = dict(branch=branch, run_id=runtime.name, ifc_sha256=checks['ifc_sha256'],
        check_count=checks['check_count'], clearance=checks['clearance'],
        actual_responses_this_run=len(actual), slots_this_run=len(attempts),
        actual_tokens_this_run=sum(a['tokens_charged'] for a in actual),
        cumulative_slots=after['calls_used'], cumulative_tokens_used_or_reserved=after['tokens_used_or_reserved'],
        cumulative_actual_response_tokens=sum(a['tokens_charged'] for a in after['attempts'] if a['status']=='completed'),
        cumulative_active_seconds=after['active_seconds'], limits=after['limits'],
        audit_concern_statuses=[c['status'] for c in concerns],
        human_acceptance='pending', proof_registration=False)
    summaries[branch] = summary
    decision = ('按已批准澄清修改内部布局：分隔墙西移300毫米，两个梯段在东西方向并列，楼板洞口、平台和分隔墙门同步调整。外轮廓、楼层标高、外墙门窗和材料风格保持请求值。大厅每层减少2.52平方米。'
        if branch == 'A-revise' else '按用户明确决定保留原设计：两个反向梯段仍共用同一平面。它是忠实建模的保留缺陷版本，不能用于证明楼梯安全、工程合理或规范合规。')
    clearance = ('108个垂直采样点的最小净空约3.00米，零净空点0个。本次采样确认原先的垂直遮挡已消除。Audit发生在独立采样之前，其原始结论仍为not_verified，不回写为已验算。'
        if branch == 'A-revise' else '108个垂直采样点中有3个零净空点，最小净空0米；位于一层通往二层楼梯的北端附近。Audit明确记录retained_known_issue。')
    report = f'''# {'A：澄清后调整内部布局' if branch == 'A-revise' else 'B：明确保留原设计'}

**真实 Generation 已完成；独立检查通过；待人工审查，未登记 Proof。**

{decision}

## 先看这些文件

- [完整中文请求](request.txt)与[已批准澄清](clarification.txt)，[完整对话](conversation.json)。澄清来自本次获批的脚本化分支，并非本轮临场对话能力演示。
- [最终完整 IFC](generated.ifc)。原参考文件未被修改，最终 IFC 从新 Brief 和新候选生成，没有复用历史失败候选。
- [整体视图](views/overall.png)、[内部剖切](views/cutaway.png)、[双竖面板窗](views/window-double.png)、[门框与门扇](views/door.png)。图片均来自该 IFC 的原生网格；剖切只在视图中隐藏屋面、南墙和东墙。

## 逐项结果

| 核对项目 | 本次结果 |
|---|---|
| IFC格式、单位 | IFC2X3、毫米，重开读取通过 |
| 楼层与空间 | 3层、6空间；标高0/3150/6300毫米 |
| 构件数量 | 15墙、3楼板、4门、15窗；楼梯与屋面另按冻结合同核对 |
| 尺寸、位置、开口 | 与该分支冻结预期一致，含梯段、平台、墙门、楼板洞口 |
| 材料 | 明确要求的砖墙、混凝土楼板/屋面存在；无未请求材料 |
| 属性与Type | 未补写未请求性能属性，未额外创建未经请求的类型组织；基础合法附件按合同处理 |
| 外观 | 暖浅色墙面、深色门窗框、玻璃与框/门扇分色；未用颜色推导物理材料 |
| 独立验证 | 重开IFC逐项比较冻结请求，{checks['check_count']}/{checks['check_count']}项通过 |

{clearance}

## 实际运行与边界

运行ID `{runtime.name}`，`legacy_full`，Provider `api.deepseek.com / deepseek-v4-flash`。本轮收到{len(actual)}次真实响应，实际响应用量{summary['actual_tokens_this_run']:,} token。此次任务累计占用{after['calls_used']}个调用槽位、{after['tokens_used_or_reserved']:,} token（包含历史失败预留），活动时间{after['active_seconds']:.3f}秒；原失败账本不退回。详见[运行记录](execution.json)、[预算账本](runtime/runs/{runtime.name}/generation-budget.json)及[原始Audit](runtime/runs/{runtime.name}/audit/audit-report.json)。

独立采样只覆盖本案例适用的梯段垂直净空，不覆盖完整疏散、侧向空间、结构、栏杆、防火及规范审查。四张静态原生视图已由助手查看，不能替代人工在IFC viewer中的交互审查。本轮实证说明这两个冻结案例可运行，不构成普遍成功率或系统能力提升的统计结论。

机器证据：[290项原生检查](independent-ifc-checks.json)、[6项补充Type检查](independent-type-checks.json)、[净空测量](clearance-checks.json)、[视觉检查记录](visual-review.json)。原生IFC均仅有4个必需门Style，未附材料/属性，每门独立对应一个Style；补充检查没有修改冻结的290项评价器。
'''
    if branch == 'B-retain':
        report += '''
## 本轮loop实际修正了什么

首个候选把二层、三层楼板洞口的局部Z坐标多下移150毫米，导致洞口落在楼板底部以下；几何gate报告两项FLOOR_OPENING_BBOX_MISMATCH。一次受限ChangeSet仅将这两个洞口的局部origin.z恢复到0，随后重新编译、重读和Audit通过。它修正的是对已确定洞口位置的错误表达，没有移动梯段、改变楼梯共用平面、扩大洞口或消除用户保留的净空缺陷。

[首轮几何反馈](runtime/runs/8b3add702299a50f/evaluation-rounds/round-01/geometry-feedback.json)、[受限ChangeSet](runtime/runs/8b3add702299a50f/changeset-round-01/changeset.json)。这提供一次实际loop收敛证据，不代表所有几何错误均能稳定修好。
'''
    write(folder/'REPORT.md', report)

write(OUT/'review-summary.json', dict(status='awaiting_human_review', human_acceptance='pending',
    proof_registration=False, branches=summaries, original_reference_unchanged=True))
a, b = summaries['A-revise'], summaries['B-retain']
write(OUT/'REPORT.md', f'''# A/B 三层建筑：真实运行与待人工审查

**A、B均已完成新的真实 Generation / Audit，分别通过290项独立IFC检查。两者均待人工审查，未登记或转入accepted Proof。** 原参考IFC与历史失败运行保持不变。

| 分支 | 用户决定与结果 | 审查入口 |
|---|---|---|
| A | 澄清后调整内部布局；108个净空采样点中零净空为0个，最小约3.00米 | [中文报告](A-revise/REPORT.md) · [IFC](A-revise/generated.ifc) |
| B | 用户坚持保留原设计；仍有3个零净空点，Audit明确保留已知问题 | [中文报告](B-retain/REPORT.md) · [IFC](B-retain/generated.ifc) |

两者都是Generation。共同输入可从各报告进入；A/B的差别来自已批准澄清。原IFC只作本地参考与事后比较，不作为Provider附件；本轮从新Brief开始，未承接旧候选。

A本轮无需修复。B首个候选的两处楼板洞口局部Z多下移150毫米，被真实几何检查发现；一轮受限ChangeSet修正这两个位置后通过再次Audit。没有修改B要求保留的梯段布局。这是本轮实际loop收敛证据，详细前后反馈保留在B报告中。

## 修复了什么，为什么这样处理

1. **源头材料合同**：按实际材料Schema验证提取要求；空对象、不完整分层等不能冻结为合法要求，避免下游追逐无法满足的目标。
2. **错误归属**：保留具体IFC编译/重读错误给Audit；上游失败时几何检查明确记为未执行。源头语义问题回到Brief，编译器问题停止错误的几何修改，真实几何问题仍可进入对应修复。
3. **Audit失败收尾**：首次或后续Audit遇到本地拒绝、截断等错误，保存本次真实证据并持久化provider_failed；不冒用上一次响应、不继续无效调用、不发布成功IFC。
4. **预算延续**：A经明确批准将累计token上限升至300万，仍保留旧22个槽位及1,925,775 token；B维持原200万上限。失败预留未退回。

修改按通用错误边界实施，没有把A/B的位置、名称或数值写入产品修复逻辑。离线验证含材料失败族203项、错误归属/公开路径148项以及预算扩展相关15项；它们来自不同轮次且有重叠，不应简单相加当能力指标。当前准入记录799项有效唯一检查，未执行Full Preflight。错误归属与Audit终止覆盖legacy_full/staged相关路径；本次真实A/B均使用legacy_full。

## 本次真实调用

| 项目 | A | B |
|---|---:|---:|
| 新运行真实响应 | {a['actual_responses_this_run']} | {b['actual_responses_this_run']} |
| 新运行响应token | {a['actual_tokens_this_run']:,} | {b['actual_tokens_this_run']:,} |
| 累计调用槽位 | {a['cumulative_slots']} | {b['cumulative_slots']} |
| 累计使用/失败预留token | {a['cumulative_tokens_used_or_reserved']:,} | {b['cumulative_tokens_used_or_reserved']:,} |

Provider为api.deepseek.com的deepseek-v4-flash；调用前验证了当前阶段准入和已授权输入。所有旧真实失败保留；本次成功不能把旧失败改写成成功，也不能据此宣称普遍成功率提高。[准入](admission.json)、[A扩额批准](A-budget-extension-approval.json)、[汇总机器记录](review-summary.json)。

## 请人工检查

先看A的内部剖切和楼梯，再看B保留的问题是否与您的决定一致；同时检查整体配色和门窗近景。您的验收应分别记录A/B，之后再决定登记Proof。B的验收含义只能是“忠实保留并明确披露问题”，不能等同于工程安全或规范合规。

四张静态原生IFC视图均已由助手检查；未做交互viewer全视角审查、完整建筑规范/结构/疏散验算、真实staged Provider运行或能力统计实验。
''')
print(json.dumps(summaries, ensure_ascii=False, indent=2))
