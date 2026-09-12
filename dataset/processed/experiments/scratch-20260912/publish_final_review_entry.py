import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root), str(root / 'src')]
from scripts.presentation.render_ifc_review import render

base = root / 'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
gen = base / 'generation'
case = gen / 'corrective-02-general-revalidation'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
execution = json.loads((case / 'execution.json').read_text(encoding='utf-8'))
assert execution['status'] == 'succeeded' and execution['final']['valid']
review = json.loads((gen / 'final-independent-review.json').read_text(encoding='utf-8'))
assert review['status'] == 'passed' and all(review['checks'].values())
assert review['sha256'] == sha(case / 'output.ifc')
assert not (gen / 'generated.ifc').exists()
shutil.copyfile(case / 'output.ifc', gen / 'generated.ifc')
render(gen / 'generated.ifc', gen / 'review-final.html')

def payload(path):
    text = path.read_text(encoding='utf-8')
    return json.loads(re.search(r'const data=(.*?);const canvas=', text).group(1))
old, final = payload(gen / 'review.html'), payload(gen / 'review-final.html')
assert old['products'] == final['products']
assert old['mesh_failures'] == final['mesh_failures'] == []
def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
write(gen / 'final-view-equivalence.json', {
    'status': 'passed', 'prior_ifc_sha256': old['sha256'], 'final_ifc_sha256': final['sha256'],
    'products_equal': True, 'mesh_style_and_property_payload_equal': True,
    'mesh_failures': 0, 'existing_pngs_applicable': True,
    'note': 'Final IFC meshes, styles, GUIDs and direct/effective properties equal the already visually inspected model. Existing PNGs remain linked to the prior file and this equivalence record.'})

calls_path = base / 'review-evidence/actual-provider-attempts.json'
calls = json.loads(calls_path.read_text(encoding='utf-8'))
shutil.copyfile(calls_path, base / 'review-evidence/actual-provider-attempts-before-audit.json')
metric = case / 'audit/metrics.json'
calls['actual_calls'].append({'workflow': 'generation', 'stage': 'audit',
    'response_id': execution['audit']['response_id'], 'model': 'deepseek-v4-flash',
    'path': metric.relative_to(base).as_posix(), 'sha256': sha(metric)})
calls['count'] = len(calls['actual_calls'])
calls['not_counted'] = [v for v in calls['not_counted'] if 'Audit blocked' not in v]
calls['not_counted'].append('Previous blocked Audit submissions and local payload preview had no transport')
write(calls_path, calls)

pending_path = base / 'pending-review.json'
pending = json.loads(pending_path.read_text(encoding='utf-8'))
shutil.copyfile(pending_path, base / 'pending-review-before-audit.json')
pending['generation_status'] = 'pending_human_review'
pending['generation_live_audit'] = 'accepted'
for name in ['generation/generated.ifc', 'generation/final-independent-review.json']:
    pending['artifacts_sha256'][name] = sha(base / name)
write(pending_path, pending)

gen_report = (gen / 'REPORT.md').read_text(encoding='utf-8')
gen_report = gen_report.replace('当前状态为 **pending_live_audit_and_human_review**，尚未通过真实 Audit 和最终发布阶段，不能称为完整真实 CLI 首次成功或 accepted Proof。',
    '真实 Audit 已接受，最终验收通过；当前状态为 **pending_human_review**。本结果经历真实失败、通用代码修复和同例复验，不是完整 CLI 首次成功或盲测能力提升；尚未安装 accepted Proof。')
gen_report = gen_report.replace('(generated-review.ifc)', '(generated.ifc)').replace('(review.html)', '(review-final.html)').replace('(independent-review.json)', '(final-independent-review.json)')
gen_report = gen_report.replace('共 4 次真实调用：', '共 5 次真实调用：')
gen_report = gen_report.replace('真实 Audit 尚未发出：此前审批额度阻断已保留；最近自动审批要求明确授权具体载荷发送到 api.deepseek.com，详见 [当前阻断记录](audit-approval-blocked-02.json) 与 [本地载荷预览](audit-payload-preview/audit/prompt-rendered.md)。',
    '用户明确批准具体载荷后，真实 Audit 已接受，响应 ID `a7baee6f-658a-4856-8e4c-d9d464c7d67e`；[最终验收](corrective-02-general-revalidation/acceptance-metrics.json)的编译、重读、几何和敏感信息扫描均通过。此前 [审批阻断记录](audit-approval-blocked-02.json) 和 [本地载荷预览](audit-payload-preview/audit/prompt-rendered.md)作为历史保留。')
gen_report += '\n最终发布 IFC 已独立复核 45 项。其网格、样式、GUID 及直接／继承属性与已查看模型完全一致，见 [视图等价检查](final-view-equivalence.json)，因此已有整体图和门窗近景仍适用；最终查看器明确绑定最终 IFC。\n'
(gen / 'REPORT.md').write_text(gen_report, encoding='utf-8')

report_path = base / 'REPORT.md'
text = report_path.read_text(encoding='utf-8').replace('完整真实 Generator 响应已编译为 IFC，45 项独立检查通过；真实 Audit 被自动审批阻断，待具体载荷授权',
    '真实 Generator → Audit 接受 → 最终 IFC 验收通过，45 项独立检查通过')
text = text.replace('(generation/review.html)', '(generation/review-final.html)').replace('、真实 Generation Audit', '')
text = text.replace('后续：具体 Audit 载荷授权并通过自动审批后，按 .tmp/continue_generation_corrective_review.py 的当前 admission 校验运行真实 Audit；不要重新生成或改写该真实候选。两条链路均得到人工确认及适用机器检查后，才整理为 accepted Proof。',
    '后续：请分别人工确认 Generation 的输入／最终 IFC 与 Repair 的原始／损坏／修复 IFC。人工确认及适用机器检查通过后，才整理为 accepted Proof。真实 Generation 共 5 次调用，Repair 共 4 次调用（其中失败尝试 2 次保留）；不是首次盲测成功。')
report_path.write_text(text, encoding='utf-8')
index = base / 'index.html'
text = index.read_text(encoding='utf-8').replace('Generation 还需完成真实 Audit；', 'Generation 真实 Audit 与最终验收已通过；')
text = text.replace('完整 IFC 已生成；真实 Audit 待执行，人工审查待确认。', '真实 Audit 与最终 IFC 验收通过；人工审查待确认。')
text = text.replace('generation/generated-review.ifc', 'generation/generated.ifc').replace('generation/review.html', 'generation/review-final.html')
index.write_text(text, encoding='utf-8')

plan = root / 'docs/architecture/semantic-appearance-plan.md'
text = plan.read_text(encoding='utf-8')
text = text.replace('真实 Audit 尚未发出：此前审批额度阻断，最近自动审批又要求对具体载荷发往 DeepSeek 明确授权；因此当前不是完整真实 CLI 首次成功，最终发布及 accepted Proof 仍待完成。',
    '用户明确授权具体载荷后，真实 Audit 接受且最终发布验收通过；最终 IFC 再独立核对 45 项通过。该结果经历开发纠错及同例复验，不是完整真实 CLI 首次成功或盲测能力提升，accepted Proof 仍待人工确认。')
text = text.replace('完整 `generated-review.ifc`', '最终完整 `generated.ifc`')
text = text.replace('下一步先完成待执行的真实 Audit，再等待用户对两条链路分别确认，最后按适用检查整理 Proof。',
    '下一步等待用户对两条链路分别确认，再按适用检查整理 Proof。真实尝试清单记录 9 次调用（Generation 5、Repair 4，包含此前失败尝试）。')
plan.write_text(text, encoding='utf-8')
print(json.dumps({'status': 'ready_for_human_review', 'actual_provider_calls': calls['count'], 'final_ifc': str(gen / 'generated.ifc')}))
