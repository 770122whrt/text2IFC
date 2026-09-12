import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'src'))
from text2ifc_agent.artifact_scan import scan_path
base = root / 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
execution = load(base / 'A-revise/execution.json')
runtime = root / execution['run_dir']
budget = load(runtime / 'generation-budget.json')
assert execution['status'] == 'audit_blocked'
assert not (runtime / 'output.ifc').exists()
assert not (base / 'A-revise/generated.ifc').exists()
assert not (base / 'B-retain/runtime').exists()
stages = []
for directory, attempt in zip(['calls/01-design-brief', 'generator', 'audit', 'changeset-round-01'], budget['attempts'], strict=True):
    metrics = load(runtime / directory / 'metrics.json')
    stages.append({'stage': attempt['stage'], 'response_id': metrics['response_id'],
                   'reported_model': metrics['model'], 'tokens': metrics['usage']['total_tokens'],
                   'provider_seconds': attempt['elapsed_seconds'], 'status': attempt['status']})
scan = scan_path(base)
assert scan['finding_count'] == 0, scan['findings']
save(base / 'live-artifact-scan.json', scan)
original = base.parent / 'three-storey-human-review-20260909'
original_hashes = {'generated.ifc': sha(original / 'generated.ifc'), 'request.txt': sha(original / 'request.txt')}
assert original_hashes == {'generated.ifc': '756cf1ad4b8175ecb2571ce09483bd6ab83edfd562ae2f66c33a650b9e610d63',
                          'request.txt': '2046a23ec544596aead827abe9ef734aa118694f9af6c8bc20c2649b9a2f818e'}
summary = {'recorded_at': dt.datetime.now(dt.timezone.utc).isoformat(),
           'A': {'status': execution['status'], 'session_hash': execution['session_hash'], 'ifc_published': False,
                 'stages': stages, 'completed_calls': len(stages),
                 'reported_tokens': sum(s['tokens'] for s in stages),
                 'provider_seconds': sum(s['provider_seconds'] for s in stages),
                 'wall_seconds': (dt.datetime.fromisoformat(execution['finished_at']) - dt.datetime.fromisoformat(execution['started_at'])).total_seconds()},
           'B': {'status': 'not_started_shared_deterministic_defect', 'completed_calls': 0, 'ifc_published': False},
           'original_hashes_unchanged': original_hashes, 'provider_authorization': 'live-authorization-20260910.json',
           'admission_status': 'suspended_after_shared_deterministic_defect',
           'proof_registered': False, 'human_review_ready': False, 'github_push_authorized': False,
           'claim': 'real attempt plus offline failure localization; no successful new IFC or capability improvement'}
save(base / 'live-run-summary.json', summary)
save(base / 'RUN-HOLD.json', {'status': 'suspended', 'supersedes_for_future_transport': 'admission.json',
                             'reason': 'Real A attempt exposed shared deterministic issue-path truncation and cross-storey name false positives.',
                             'required_before_any_further_transport': 'Offline failure-family fix, affected public-path validation, fresh applicable admission; preserve cumulative authorized per-branch budget.',
                             'A_calls_used': 4, 'B_calls_used': 0, 'authorization_remains_bounded': True})
stage_lines = '\n'.join(f"| {s['stage']} | `{s['response_id']}` | {s['tokens']:,} | {s['provider_seconds']:.3f} |" for s in stages)
report = f'''# A 分支真实运行：已停止，尚无新 IFC

**本次运行失败，不能进入待验收 Proof。** 4次真实调用后终止为 `audit_blocked`，没有编译发布 IFC。B 尚未启动：A 暴露的修复范围映射和跨层名称检查缺口属于共用路径，需要先离线修复。

## 输入与实际运行

[原请求](request.txt)与旧例相同；[追加澄清](clarification.txt)选择内部调整，隔墙西移300毫米，两段楼梯错开；[完整对话](conversation.json)标明用户授权的测试脚本来源。旧 IFC 仅作为参考，原始 IFC 文件没有发送 Provider。

默认 `legacy_full`；请求模型 `deepseek-v4-flash`，响应元数据为 `deepseek-flash`，目的地 `api.deepseek.com`。会话 `{execution['session_hash']}`。

| 阶段 | 真实响应 ID | reported token | Provider 活动秒数 |
| --- | --- | ---: | ---: |
{stage_lines}

共 **{summary['A']['reported_tokens']:,} token，{summary['A']['provider_seconds']:.3f}秒 Provider 活动时间**；墙钟约{summary['A']['wall_seconds']:.3f}秒。预留额度没有计入实际用量。没有人工候选替代、合成成功或 IFC 手工补救。

## 在哪里停止，原因是什么

1. Brief 首次 ready，结构检查通过，已提取修订后的隔墙、空间、楼梯及洞口坐标。
2. 首个 Generator 候选通过 JSON 合同，但材料门禁拒绝18个 Type 上未授权作用域的材料；因此未进入成功编译发布。相关错误在不同门禁中重复呈现，不能当成36个独立材料问题。
3. 名称门禁还把“第一段楼梯（首层至二层）”“第二段楼梯（二层至三层）”中的合法到达层文字当成归属错误。独立重放表明，这两处到达层均与冻结起止层一致；这是名称检查的误报，不能据此说楼梯真的放错层。
4. Audit 3.0 保留用户决定、参考问题和 `not_verified`，遵守阻断门禁，未声称布局已通过工程审查。
5. ChangeSet 返回合法 Draft：门禁指向 `/materials`，但 normalizer 把具体字段统一写成 `#/attributes`，导致 CHANGE_SCOPE 不允许修改材料。模型选择不越权并提出澄清。这里缺少的是内部正确修复范围，不是用户再次批准建筑设计。

[离线复现](offline-failure-diagnosis.json)用原始候选／门禁重放，确认18个 Type 的修复路径不可达、2个楼梯名称误报；补充的4个合成边界探针中3项不满足目标不变量、1项未知目标保全通过。只是失败定位，未修改生产代码，也不声称已修好或能力提升。原运行文件哈希核对不变。

## 下一步的小步修复

- 保留确定性报错的组件 ID 和精确 JSON 字段路径，材料问题只开放对应材料字段；未知／冲突目标保持阻断，不扩为整实体权限。覆盖实例／Type、不同场景、嵌套字段、多个目标和非法路径，再验证公共 ChangeSet 应用／回滚与范围外保全。
- 楼梯名称检查应结合已经确认的起止楼层，允许描述合法终点，同时继续阻断无关楼层名称及真实错误归属；不靠删除合法人类名称掩盖检查器缺陷。
- 适用测试和新的准入通过之后，才可继续剩余有界运行；不得重置已有调用预算。B 的原授权仍有效但尚未使用，当前共用缺陷先阻断执行。

## 证据和边界

- [原始公共报告](runtime/runs/{execution['session_hash']}/report.md)、[首次候选](runtime/runs/{execution['session_hash']}/generator/candidate.json)、[Audit](runtime/runs/{execution['session_hash']}/audit/audit-report.json)、[ChangeSet Draft](runtime/runs/{execution['session_hash']}/changeset-round-01/draft.json)。原始报告仍沿用历史 Mimo 标题，实际 Provider 以本次响应元数据为准。
- [预算](runtime/runs/{execution['session_hash']}/generation-budget.json)、[终端执行结果](execution.json)、[暂停原因](../RUN-HOLD.json)、[敏感信息扫描](../live-artifact-scan.json)（0项发现）。
- 没有新增 IFC，因此没有本次 IFC 重读、净空测量或真实模型图片；不复用旧图伪称新结果。旧请求和 IFC 哈希不变。
- 运行前离线准入有效；live 暴露共用确定性缺陷后，后续调用暂停。没有执行 Full Preflight。未登记 Proof、未进行新模型人工验收、未推送 GitHub。
'''
with (base / 'A-revise/REPORT.md').open('x', encoding='utf-8', newline='\n') as f:
    f.write(report)
with (base / 'B-retain/REPORT.md').open('x', encoding='utf-8', newline='\n') as f:
    f.write('# B 分支：授权保留，尚未启动\n\nA 的真实尝试暴露共用修复范围映射和跨层名称检查缺口，当前暂停 B，避免重复消耗 Provider 预算。B 没有调用、候选或新 IFC，未登记 Proof。\n\n[本分支对话](clarification.txt)仍要求忠实表达原设计，并保留零净空问题；不改变此已确认选择。后续先完成共用缺陷的离线修复及适用准入，再在既定预算内执行。\n\n见 [A 的失败报告](../A-revise/REPORT.md)及 [当前运行汇总](../live-run-summary.json)。\n')
with (base / 'REPORT.md').open('x', encoding='utf-8', newline='\n') as f:
    f.write('# 三层 A/B 真实运行报告\n\n**A 已真实运行但失败，B 因共用工程缺陷暂停；尚无两份新 IFC，不登记 Proof。**\n\n| 分支 | 实际结果 | 入口 |\n| --- | --- | --- |\n| A：澄清后调整 | 4次调用、288,462 token；材料门禁阻断，ChangeSet 因范围错误返回 Draft；无 IFC | [完整报告](A-revise/REPORT.md) |\n| B：坚持原要求 | 0次调用；等待共用缺陷离线修复及更新准入 | [状态说明](B-retain/REPORT.md) |\n\n确认的工程缺口是材料报错路径在修复范围中被截断，以及合法起止层楼梯名称被误判；新 Audit 保留决定和已知问题的行为已在真实响应中观察到。不能把这次失败说成两条链路通过，也不能将预运行离线回归等同真实成功。\n\n[运行汇总](live-run-summary.json) · [具体暂停原因](RUN-HOLD.json) · [离线复现](A-revise/offline-failure-diagnosis.json) · [原参考 IFC](../three-storey-human-review-20260909/generated.ifc)\n\nREADME 和 admission-initial/admission 保存运行前准备状态；最新执行结论以本报告和 RUN-HOLD 为准。原请求、IFC、全部真实响应和失败证据保留。下一步无需重新选择布局：先修精确字段范围与名称适用性，再按原有授权预算继续。GitHub 推送仍未获本次具体载荷授权。\n')
files = []
for p in sorted(base.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:
        files.append({'path': p.relative_to(base).as_posix(), 'sha256': sha(p), 'size_bytes': p.stat().st_size})
save(base / 'LIVE-ATTEMPT-FILES.json', {'role': 'frozen first-attempt files; no success or Proof claim', 'files': files})
print(json.dumps({'status': 'reported_failed_attempt', 'A_calls': len(stages), 'B_calls': 0,
                  'tokens': summary['A']['reported_tokens'], 'files': len(files), 'secret_findings': scan['finding_count']}))
