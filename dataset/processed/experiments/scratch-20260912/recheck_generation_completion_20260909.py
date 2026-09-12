"""Read-only run inspection; write a separate, non-accepted human review record."""
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909'
OUT = BASE / 'completion-recheck'
RUN = BASE / 'geometry-continuation/runs/5cd2006f0891913f'
OUT.mkdir(exist_ok=False)

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

gate = read(RUN / 'gate-summary.json')
audit = read(RUN / 'audit/parsed-output.json')
budget = read(RUN / 'generation-budget.json')
independent = read(BASE / 'geometry-continuation/completion-recheck-independent.json')
mesh = read(BASE / 'geometry-continuation/views/overall-mesh.json')
assert independent['ifc_sha256'] == sha(RUN / 'output.ifc') == mesh['source_sha256']
assert independent['request_sha256'] == sha(BASE / 'request.txt')
completed = [a for a in budget['attempts'] if a['status'] == 'completed']
reserved = [a for a in budget['attempts'] if a['status'] == 'reserved']
record = {
    'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'status': 'engineering_blocked_not_ready_for_human_acceptance',
    'publication_verified': False,
    'process_observation': 'read-only elevated Win32_Process query returned no python.exe process; old PTY session unavailable',
    'runtime_observation': 'execution.json remains running; final reserved ChangeSet has no saved response; interruption cause unknown',
    'gate_overall_status': gate['overall_status'],
    'gates': [{'name': g['name'], 'status': g['status'], 'issue_count': g['issue_count']} for g in gate['gates']],
    'audit_blocking': audit['blocking'],
    'completed_calls_in_inherited_budget': len(completed),
    'reported_tokens_completed': sum(a['tokens_charged'] for a in completed),
    'provider_seconds_completed': sum(a['elapsed_seconds'] for a in completed),
    'unresolved_reserved_attempts': reserved,
    'reserved_token_amount_is_not_reported_usage': True,
    'independent_check_count': len(independent['checks']),
    'independent_failed': independent['failed'],
    'ifc_sha256': independent['ifc_sha256'],
    'request_sha256': independent['request_sha256'],
    'represented_physical_products': len(mesh['products']),
    'mesh_failures': mesh['mesh_failures'],
    'proof_installed': False,
    'new_provider_calls': 0,
    'source_artifacts_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in [
        RUN/'gate-summary.json', RUN/'audit/parsed-output.json', RUN/'generation-budget.json',
        RUN/'output.ifc', RUN/'candidate.json', BASE/'request.txt',
        BASE/'geometry-continuation/execution.json',
        BASE/'geometry-continuation/completion-recheck-independent.json',
    ]},
}
(OUT / 'verification.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
request = (BASE / 'request.txt').read_text(encoding='utf-8')
report = f'''# 双层社区阅读活动楼：完成情况核验

当前结论：**已有真实 Provider 生成并编译的完整候选 IFC，但正式门禁失败、运行没有完成终端发布。暂不收纳为待人工验收的成功 Proof。** 此页保留可阅读输入、候选与实际模型图片，供了解进展；不是 accepted 或 pending_human_review 的成功证明。

## 直接查看

- [完整候选 IFC（未发布）](../geometry-continuation/runs/5cd2006f0891913f/output.ifc)
- [原始中文输入](../request.txt)；正文在本页下方按 UTF-8 原文展示。
- [真实模型 JSON](../geometry-continuation/runs/5cd2006f0891913f/candidate.json)
- [本次核验记录](verification.json)

## 完成与未完成

| 项目 | 本次核实结果 |
|---|---|
| 真实生成 | live_model_generator；IFC2X3 候选存在、可重读，163889 字节 |
| 已冻结预期的独立重读 | 再次运行原检查器，167 项通过、0 失败；没有修改预期或候选 |
| 语义及结构 | 2 层、4 空间、10 墙、3 板、10 窗、3 门，直跑楼梯及实际楼板洞口；材料、缺省属性、门窗部件样式通过独立检查 |
| 正式门禁 | 10 类中 9 类通过；geometry 有 3 条阻断，整体 failed |
| 真实 Audit | 已返回 blocking=true / revise；并非仍在等待 Audit |
| 后续纠错 | 两次 ChangeSet 返回均未通过草案路径校验；第 3 次只有预留记录，没有落盘响应 |
| 进程与终端 | 只读进程核实无 python.exe；execution.json 仍是 running，未取得最终发布结果；中断原因未知 |
| 外观 | 27 个实体构件网格化成功；整体、剖看、双窗、门近景已检查，配色协调，几何观感规整 |
| Proof | 未创建新 Proof 包、未登记、未执行 accepted curator；旧 Proof 不变 |

独立 167 项检查回答实际模型是否满足其覆盖的冻结要求，不能替代正式几何门禁、真实 Audit 与终端发布。此前“候选通过当前自动门禁”的进度表述过早，本次明确更正。

## 三个需要工程处理的问题

1. **洞口身份未绑定。** Brief 中楼板洞口没有显式 ID，几何预期代码生成 `opening-second-floor-slab-stair`；候选使用另一个 ID。独立检查能找到实际洞口、宿主关系及真实网格缺口，正式门禁却按预期身份查找失败。应修正通用的洞口身份绑定，覆盖无 ID、显式 ID、多洞口、错误宿主与歧义，不能简单忽略缺失错误。
2. **隔墙预期丢失明确边界。** Brief 的两道隔墙仅保留 connects 和厚度，没有墙的显式边界；预期推导依赖相邻空间共边，但房间净边界之间留有墙厚，二层楼梯平台也只覆盖墙的一段。原请求的完整墙范围不能由这种邻接信息可靠恢复。需检查请求→Brief→预期的事实保全，并让显式边界优先；不能靠移动正确的墙来迎合推导结果。
3. **纠错路由与地址不相容。** 几何预期缺失、Audit 的 gate_dispute 被合并送到 Generator ChangeSet；返回的 missing_facts 引用几何预期／Brief 路径，随后被候选路径解析器以 UNRESOLVED_DRAFT_PATH 拒绝。需先区分候选缺陷与预期／门禁争议，并检验这种问题是否具有合法可写范围，避免继续花费调用修补错误对象。

上述定位来自真实 artifacts 和源码；尚未做这一组新问题的红绿修复，不能声明 Bug fixed 或成功率提高。下一步先冻结这些真实失败及跨场景反例，离线修复并重新检查同一 IFC；通过适用准入后再进行有界真实复验。

## 真实调用与保全

同一任务继承的预算中，已记录完成 {len(completed)} 次真实响应：Brief 1、Generator 2（包含前一次失败）、Audit 1、ChangeSet 2；reported token 合计 {record['reported_tokens_completed']:,}，已测 Provider 活动时间约 {record['provider_seconds_completed']:.1f} 秒。第 7 次 ChangeSet 预留 172,003 token，**用量与结果未知**，保留原预留，不当作实际消费，也不当作零消费。更早 2026-09-08 的 5 次响应另存于旧开发记录，未混入此计数。

本次只做核验，没有新增 Provider 调用、重跑 Full Preflight、改变生成模型或重写运行数据库。原请求、响应、候选、IFC、预算和 running 记录原样保留。新核验结果单独落盘；过程文件缺少终端记录不能由手填 success 补齐。

机器依据：[正式门禁](../geometry-continuation/runs/5cd2006f0891913f/gate-summary.json)、[真实 Audit](../geometry-continuation/runs/5cd2006f0891913f/audit/parsed-output.json)、[独立重读复验](../geometry-continuation/completion-recheck-independent.json)、[调用预算](../geometry-continuation/runs/5cd2006f0891913f/generation-budget.json)、[首次 ChangeSet 拒绝](../geometry-continuation/runs/5cd2006f0891913f/changeset-round-01/validation.json)、[第二次拒绝](../geometry-continuation/runs/5cd2006f0891913f/changeset-round-01/attempt-02/validation.json)。

## 实际 IFC 视图

暖色墙面、深色门窗框、浅色玻璃，南立面门窗上下对齐。模型外观协调但仍较朴素；这是实际网格的静态检查，未加景观或后期生成装饰。按原输入，本例不含栏杆、家具、机电及复杂五金，不能称为施工设计成品。

![整体](../geometry-continuation/views/overall.png)

下图为查看楼梯和层间关系而隐藏屋面及南／东墙的剖看视图，悬空门窗属于显示隐藏的结果，不代表 IFC 缺墙。

![楼层与楼梯](../geometry-continuation/views/cutaway.png)

![双面板窗](../geometry-continuation/views/window-double.png)

![门框和门扇](../geometry-continuation/views/door.png)

图片网格来源 SHA-256 与本次重新打开的 IFC 一致：`{record['ifc_sha256']}`。

## 实际发送的中文输入原文

{request}
'''
(OUT / 'REPORT.md').write_text(report, encoding='utf-8')
links = re.findall(r'\]\(([^)]+)\)', report)
missing = [link for link in links if not (OUT / link).resolve().exists()]
assert not missing, missing
for p,h in record['source_artifacts_sha256'].items():
    assert sha(ROOT / p) == h, f'Source changed: {p}'
(OUT / 'presentation-check.json').write_text(json.dumps({
    'status': 'passed', 'local_links_checked': len(links), 'missing': missing,
    'source_hashes_unchanged': True, 'scope': 'diagnostic report links and source preservation; not Proof acceptance',
}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'report': str(OUT/'REPORT.md'), 'status': record['status'], 'links': len(links)}, ensure_ascii=False))
