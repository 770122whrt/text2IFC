import json
from pathlib import Path
P = Path('dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/typed-appearance-rerun-20260910')
run = P/'A-revise/runtime/runs/411166603facdde6'
hold = {'status':'blocked', 'run_id':run.name, 'branch':'A-revise',
    'cause':'Brief material={} was frozen as a requested material; reopened IFC cannot contain an empty material. Duplicate mismatch entries are the same material requirement projected twice, not a Type requirement.',
    'secondary':'Audit02 rejected locally for input token limit and escaped the regeneration path as ProviderOutputError.',
    'provider_responses_this_attempt':5, 'local_rejections_this_attempt':1,
    'calls_used':22,'tokens_used_or_reserved':1925775,
    'action':'No more Provider transport under this admission. Preserve all evidence and debug source material grammar offline. A remaining budget is insufficient for a fresh Brief reservation.'}
with (P/'RUN-HOLD.json').open('x',encoding='utf-8') as f: json.dump(hold,f,ensure_ascii=False,indent=2)
report = '''# A/B 真实运行：空材料要求阻断

**A 未产出可交付 IFC；B 未启动；未登记 Proof，未人工验收。** 运行代码 `06abe9bd`，A 会话 `411166603facdde6`。原参考 IFC 保持不变。

本轮 Brief 2.3 一次通过；主题与部件风格正确保留，19项实际材料要求和19项门窗模板均在。生成模型另有1项 IFC2X3 属性名错误，被现有 repair loop 修正。但入口门的模板记录还夹带了 `material: {}`；当前材料投影仅检查对象类型，把它冻结成了必须满足的要求。两条重读 mismatch 来自同一材料要求的两次投影，**不是 Type 错误**。

这使 reopened IFC 无法满足冻结预期。对下游的反馈又将具体语义失败概括为 compile/reopen 失败；模型开始修改楼梯编码而非修复源头提取。随后 Audit02 输入超过本地限制，在发送前拒绝，并从再生成分支抛出未处理异常。最终发布未发生；没有可交付 IFC。

新运行实际收到5次 Provider 响应（Brief、Generator、格式 Repair、Audit、ChangeSet）；1次 Audit 本地拒绝。A 整个获批任务共22个账本槽位，20次真实响应、2次本地拒绝；预算含失败预留1925775 token、1695.485秒。剩余74225 token 不足预留新的完整 Brief；不退回历史失败预留、不擅自增额。

最小下一步是从真实 BIM JSON 材料 Schema 验证请求值，非法对象不能冻结为权威、也不能阻止受限 Brief 校正；覆盖空值、字段缺失、单材料、完整分层、非法厚度、跨构件和合法要求保全。另需后续处理“语义错误被笼统归类”和再生成 Audit 异常退出；本报告不声称这些问题已经修复。

当前已运行284项聚焦离线检查；结合未变路径共有712项有效检查。失败表明这些检查仍未覆盖空材料来源，不能把回归通过或真实尝试称为系统能力提升。没有执行 Full Preflight。

## 文件入口

- [中文输入](inputs/A-revise/request.txt)、[A 澄清](inputs/A-revise/clarification.txt)、[B 澄清](inputs/B-retain/clarification.txt)
- [本轮运行状态](A-revise/execution.json)、[暂停记录](RUN-HOLD.json)
- [Brief](A-revise/runtime/runs/411166603facdde6/calls/01-design-brief/design-brief.json)
- [独立重读失败](A-revise/runtime/runs/411166603facdde6/evaluation-rounds/round-01/ifc-verification.json)
- [Audit](A-revise/runtime/runs/411166603facdde6/audit/audit-report.json)
- [真实预算账本](A-revise/runtime/runs/411166603facdde6/generation-budget.json)
- [阶段准入](admission.json)
'''
with (P/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
plan=Path('docs/architecture/semantic-appearance-plan.md')
with plan.open('a',encoding='utf-8') as f:
    f.write('\n- 2026-09-10 typed-appearance 真实 A `411166603facdde6`：Brief 外观已正确，但门模板记录附带 `material:{}`；源头投影仅检查 Mapping，错误冻结空要求。reopen 拒绝该要求，下游概括为编译失败导致错误修复方向，Audit02 本地输入超限异常退出；5次真实响应、1次本地拒绝，无终态 IFC，B未启动。A累计22槽位/1925775含预留token，准入已暂停。下一小步先建立材料源值格式失败族并复用实际材料Schema，保持合法要求与几何；不手动退回预算，不把本案例当盲测能力证据。\n')
print('Preserved hold/report and recorded diagnosis before code changes')
