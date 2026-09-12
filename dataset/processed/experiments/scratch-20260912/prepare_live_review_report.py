import datetime as dt
import hashlib
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
GEN, REPAIR = BASE / 'generation', BASE / 'repair'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
assert json.loads((GEN / 'independent-review.json').read_text(encoding='utf-8'))['status'] == 'passed'
assert json.loads((REPAIR / 'independent-review.json').read_text(encoding='utf-8'))['status'] == 'passed'
evidence = BASE / 'review-evidence'
evidence.mkdir(exist_ok=False)
for name in ['check_repair_review.py', 'check_generation_review.py', 'continue_generation_corrective_review.py', 'run_generation_corrective_review.py', 'run_repair_live_review.py', 'export_ifc_review_png.py']:
    shutil.copyfile(ROOT / '.tmp' / name, evidence / name)
write(GEN / 'audit-blocked.json', {'recorded_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'status': 'blocked_before_transport', 'network_transport_attempted': False,
    'action': '.venv/Scripts/python.exe .tmp/continue_generation_corrective_review.py',
    'reason': 'Automatic approval review usage limit', 'retry_after_reported_local': '2026-09-09 00:07 Asia/Shanghai',
    'candidate_checks': 'corrective-02-general-revalidation/binding-admission.json',
    'note': 'Provider authorization already given; approval-service quota is the blocker. No Audit response exists and no accepted Proof is installed.'})
private = json.loads((REPAIR / 'evaluator-private/mutation.json').read_text(encoding='utf-8'))
forbidden = [private['removed_relationship']['GlobalId'], '01-original.ifc', 'evaluator-private', 'mutation.json']
prompt_files = [REPAIR / 'runtime-live-04/runs/repair-vvo-property-relation-live-04/intent/renderer-input.json',
                *list((REPAIR / 'runtime-live-04/runs/repair-vvo-property-relation-live-04/changeset').rglob('*prompt*'))]
prompt_files = [p for p in prompt_files if p.is_file()]
leaks = [{'path': p.relative_to(BASE).as_posix(), 'forbidden': value} for p in prompt_files
         for value in forbidden if value in p.read_text(encoding='utf-8')]
assert not leaks
write(evidence / 'public-boundary-check.json', {'status': 'passed', 'checked_files': [p.relative_to(BASE).as_posix() for p in prompt_files],
    'checks': 'Public prompt/input artifacts exclude pristine original filename, private evaluator paths, mutation recipe name and removed relationship identity.',
    'request_file_sha256': sha(REPAIR / 'request.txt'),
    'request_text_utf8_sha256': hashlib.sha256((REPAIR / 'request.txt').read_text(encoding='utf-8').encode()).hexdigest(),
    'request_hash_note': 'The runtime hashes UTF-8 request text after newline decoding; frozen file hash covers raw CRLF bytes. No request content changed.'})
attempts = []
for mode in ['runtime-02', 'runtime-live-04']:
    folder = REPAIR / mode
    intent = next(folder.rglob('live-attempt-001.json'))
    changeset = next(folder.rglob('live-response.json'))
    for stage, path in [('intent', intent), ('changeset', changeset)]:
        value = json.loads(path.read_text(encoding='utf-8'))
        response = value['response'] if stage == 'intent' else value
        attempts.append({'workflow': 'repair', 'attempt': mode, 'stage': stage,
                         'response_id': response.get('id'), 'model': response.get('model'),
                         'path': path.relative_to(BASE).as_posix(), 'sha256': sha(path)})
for stage, path in [
    ('design-brief-clarification', GEN / 'runtime/runs/bd9a2fd94c6e4be8/calls/01-design-brief/response.raw.json'),
    ('design-brief-resume', GEN / 'runtime/runs/bd9a2fd94c6e4be8/calls/02-design-brief/response.raw.json'),
]:
    response = json.loads(path.read_text(encoding='utf-8'))
    attempts.append({'workflow': 'generation', 'stage': stage, 'response_id': response.get('id'),
                     'model': response.get('model'), 'path': path.relative_to(BASE).as_posix(), 'sha256': sha(path)})
for folder in [GEN / 'runtime/runs/bd9a2fd94c6e4be8/generator', GEN / 'corrective-attempt-02/generator']:
    path = folder / 'metrics.json'
    value = json.loads(path.read_text(encoding='utf-8'))
    attempts.append({'workflow': 'generation', 'stage': 'generator', 'response_id': value.get('response_id'),
                     'path': path.relative_to(BASE).as_posix(), 'sha256': sha(path)})
write(evidence / 'actual-provider-attempts.json', {'actual_calls': attempts, 'count': len(attempts),
    'not_counted': ['startup-01 rejected run-id before transport', 'runtime-offline-03 fake Provider',
                    'deterministic revalidation copies', 'Audit blocked by approval quota']})
generation_report = '''# Generation 人工检查

真实 DeepSeek 已返回 Design Brief 和完整 Formal 2.1；确定性代码已生成可重读的完整 IFC2X3，45 项独立请求核对通过。当前状态为 **pending_live_audit_and_human_review**，尚未通过真实 Audit 和最终发布阶段，不能称为完整真实 CLI 首次成功或 accepted Proof。

## 输入与输出

- [实际用户输入](request.txt)；[澄清回答](clarification-answer-01.txt)：6000 沿 X、4000 沿 Y，其他要求不变。该演示输入和回答由 Codex 按授权编写。
- [完整待检查 IFC](generated-review.ifc)；[交互查看模型](review.html)。打开属性区域可查看实际 IFC 直接／有效属性。
- [整体图](overall.png)、[双面板窗近景](window-double.png)、[单面板窗近景](window-single.png)、[门框门扇近景](door.png)。这些是实际 IFC 网格渲染，颜色受查看器照明影响。

| 明确要求 | IFC 独立重读结果 |
|---|---|
| IFC2X3、毫米 | 通过 |
| 室内净尺寸 6000×4000×3000 | 通过，原点位于地坪中心 |
| 四面砖墙，厚 200、高 3000 | 通过；IfcWallStandardCase 的砖以合法单层 usage 表达 |
| 混凝土地坪厚 150、顶面 Z=0 | 通过，覆盖 6400×4400 外包范围 |
| 南面居中左单开门 1000×2100 | 通过；门框与门扇分色，左开由 IFC2X3 DoorStyle 表达 |
| 东侧双竖面板窗、西侧单面板窗 | 各 1600×1200，窗台 900，居中；实际存在 2／1 片玻璃 |
| 开口、宿主、框深和位置 | 开口名义宽高一致、穿透墙厚；门窗均位于允许的安装深度范围 |
| warm-residential 协调风格 | 米色墙、棕色门扇、深色框、淡色玻璃；实际玻璃 transparency=0.45 |
| 未指定的材料与性能属性 | 未创建；仅有内部身份、构造参数来源、外观溯源属性及最小合法门 Style |
| 明确无屋顶、无吊顶 | 未创建 |

[独立检查的 45 项及实际值](independent-review.json)不使用 Agent 的 represented 标签作为证据。[冻结请求](frozen-expectations.json)在 Provider 前建立，未按输出改写。

## 真实过程及限制

共 4 次真实调用：初始 Brief 提出轴向澄清，回答后 Brief ready；第一份 Generator 候选重复旋转窗体，被正确阻断；第二份真实 Generator 响应纠正放置。该响应未被人工改写。后续离线调试修复了稳定 ID 映射、墙体子类计数、几何／宿主匹配以及关系名称编译问题。

最新确定性检查在 [corrective-02-general-revalidation](corrective-02-general-revalidation/binding-admission.json)。它复用了第二份真实响应；这是开发纠错后的同例回放，不是盲测或能力提升证据。真实 Audit 请求被自动审批额度阻断，尚未发出；详见 [阻断记录](audit-blocked.json)。完整历史与失败响应保留在 runtime 和 corrective-attempt-02。

人工检查重点：整体颜色是否协调；单窗、双窗分格是否清晰；框／扇比例是否合适；尺寸和材料是否忠实于输入。门为关闭状态，不含把手、复杂五金或开门动画。视觉审查不能代替模型尺寸、类型和属性检查。
'''
repair_report = '''# Repair 人工检查

真实 DeepSeek 经公共 RepairAPI 完成实例属性修复，发布成功；独立重读核对通过。状态为 **pending_human_review**，尚未安装 accepted Proof。

## 原始、破坏、修复三份 IFC

| 角色 | IFC | 可交互视图 |
|---|---|---|
| 原始 dataset 文件 | [01-original.ifc](01-original.ifc) | [原始视图](review-original.html) |
| 删除一条属性关联后，实际输入 | [02-damaged.ifc](02-damaged.ifc) | [破坏视图](review-damaged.html) |
| 真实 RepairAPI 发布的完整输出 | [03-repaired.ifc](03-repaired.ifc) | [修复视图](review-repaired.html) |

来源为 `dataset/external/bimnet/vvo.ifc`。original 的 `private_ground_truth` 角色在执行前冻结，仅供执行后评估；没有向 Provider 提供 pristine 原文件、删除关系的身份或 mutation 配方。

[实际公共请求](request.txt)指定目标墙 `2CsmzAChHF6O6maGXlo6PS`（基本墙:240:223174）的实例 Pset_WallCommon。只删除了一条 IfcRelDefinesByProperties；保留了原属性集和所有几何。公开请求值来自 damaged IFC 中尚存的独立属性集，见 [公开输入事实](public-input-facts.json)。

| 直接实例属性 | 原始 | damaged | repaired | IFC 类型 |
|---|---|---|---|---|
| Reference | "240" | 此直接关联缺失 | "240" | IfcIdentifier |
| IsExternal | true | 此直接关联缺失 | true | IfcBoolean |
| ExtendToStructure | false | 此直接关联缺失 | false | IfcBoolean |
| LoadBearing | false | 此直接关联缺失 | false | IfcBoolean |

注意：损坏的是**实例直接关联**；Type 中已有的继承属性仍可能显示部分值。请查看 DirectProperties，不能只看 EffectiveProperties。[定位原始目标](review-original.html#2CsmzAChHF6O6maGXlo6PS)／[定位损坏目标](review-damaged.html#2CsmzAChHF6O6maGXlo6PS)／[定位修复目标](review-repaired.html#2CsmzAChHF6O6maGXlo6PS)。

## 独立验证及视觉检查

- 三份 IFC 均可重读；每份 152 个可见构件均可网格化。三份的世界网格、有效样式完全相同。
- repaired 相对 damaged 没有修改或删除任何既有 STEP 实体，只新增 4 个属性值、1 个属性集和 1 条关联。Type、材料、样式、几何及其他对象保留。
- 原始 dataset 文件与 damaged 输入哈希未变。恢复的是同值、同类型的合法属性附件，未伪造恢复删除关系的原 GlobalId。
- 实際三维整体视图已检查，修复前后外观相同；本次不美化或升级 Repair 门窗。[整体图](overall-depth.png)。
- [独立核对明细](independent-review.json)；[真实公共结果](result-live-04.json)；[机器评估](runtime-live-04/runs/repair-vvo-property-relation-live-04/.terminal-bundles/6395e2e7aa4c4e3c86e42a9146133e42/evaluation/public-evaluation.json)。

公共评估的 L1 与 preservation 通过；其 conditional L2 属性项为 not_required，不能拿该标签证明请求值正确。本案请求值由独立重读另行逐项核对。该语义评估适用于冻结三元组，不宣称运行了整个 IFCCompare 基准或系统能力评测。

## Attempts 与保留边界

成功的 live-04 有 2 次真实调用（Intent、ChangeSet），模型 deepseek-v4-flash。此前 attempt-02 也有 2 次真实调用，但执行包装器缺少 Windows multiprocessing 主入口保护，校验子进程失败，未发布成功 IFC；其原始响应、诊断 IFC 和失败结果全部保留。offline-03 是明确标记的 fake Provider 回归，不能算真实调用。startup-01 的非法 run-id 在网络前失败，见 startup-01-correction.json。

人工确认三元组和属性后，仍须执行适用 curator／人读格式检查，才能安装到 processed/proof；本页不是 accepted 标记。
'''
(GEN / 'REPORT.md').write_text(generation_report, encoding='utf-8')
(REPAIR / 'REPORT.md').write_text(repair_report, encoding='utf-8')
(BASE / 'REPORT.md').write_text('''# text2IFC 真实运行与人工检查

本批次尚未进入 accepted Proof。请分别检查两条链路：

| 链路 | 当前结果 | 人工入口 |
|---|---|---|
| Generation | 完整真实 Generator 响应已编译为 IFC，45 项独立检查通过；真实 Audit 因审批额度未执行 | [输入、输出与逐项报告](generation/REPORT.md)／[三维视图](generation/review.html) |
| Repair | dataset 原始→删除属性关联→真实修复，公共发布和独立核对通过 | [三元组与属性对照](repair/REPORT.md)／[三维视图](repair/review-repaired.html) |

[浏览器总览](index.html)可直接打开本地 HTML，或通过本地 HTTP 查看。每页使用实际 IFC 三角网格、深度遮挡、部件颜色；下拉选择构件，展开属性，拖动旋转、滚轮缩放。

## 已完成的通用修复

1. 冻结请求 ID 与规范实体 ID 在语义、几何和宿主检查中一致绑定；重复身份、错误类别继续阻断，跨楼层错误保留明确诊断。
2. IfcWallStandardCase 计入 IfcWall 家族，不混入非墙构件。
3. 合法关系 Name／Description 按文本保留，不能当作实体引用；覆盖开洞、填充、聚合、Type 和路径连接。
4. Design Brief 在解析前保留真实请求／响应；网络失败保留脱敏错误；澄清恢复不覆盖首轮；重复 call index 在网络前阻断。
5. 旧数据集／Proof 测试路径按已有迁移映射读取，不修改既有 Proof。

最终通用范围测试 82 passed，公共入口、staged 与恢复 34 passed；此前身份／几何相关 84 passed，关系／模板相关 77 passed。各组有重叠，不合并成能力样本数。更早 Generation 阶段 807 passed / 1 failed（旧回放合同修复后聚焦 110 passed）；Repair 全目录尝试超时且非全绿，后续属性阶段 379 passed / 1 failed 的旧 index 版本断言经 9 项复验通过；真实关系破坏公共入口族 3 passed。所有失败 XML 保留。

未运行：Full Preflight、全库 pytest、真实 Generation Audit、accepted curator、用户人工验收。普通单例真实运行是可行性证据，不能证明系统能力提升。[真实调用清单](review-evidence/actual-provider-attempts.json)、[公开输入隔离检查](review-evidence/public-boundary-check.json)、[测试记录目录](admission/)。

后续：审批额度恢复后，按 .tmp/continue_generation_corrective_review.py 的当前 admission 校验运行真实 Audit；不要重新生成或改写该真实候选。两条链路均得到人工确认及适用机器检查后，才整理为 accepted Proof。
''', encoding='utf-8')
cards = [
    ('Generation', '完整 IFC 已生成；真实 Audit 待执行，人工审查待确认。', 'generation', [('request.txt','用户输入'),('generated-review.ifc','完整 IFC'),('review.html','三维与属性'),('REPORT.md','逐项报告')], 'overall.png'),
    ('Repair', '真实修复发布成功；人工审查待确认。', 'repair', [('request.txt','修复请求'),('01-original.ifc','原始 IFC'),('02-damaged.ifc','损坏 IFC'),('03-repaired.ifc','修复 IFC'),('review-repaired.html','三维与属性'),('REPORT.md','三元组报告')], 'overall-depth.png')]
sections = ''
for title, status, folder, links, picture in cards:
    sections += f'<article><h2>{title}</h2><p>{status}</p><img src="{folder}/{picture}" alt="实际 IFC 整体视图"><nav>' + ''.join(f'<a href="{folder}/{path}">{label}</a>' for path, label in links) + '</nav></article>'
(BASE / 'index.html').write_text('''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>text2IFC · 人工检查</title><style>body{background:#f3f4f0;color:#283c32;font:16px system-ui;margin:36px auto;max-width:1200px;padding:0 24px}h1{font-size:30px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:24px}article{background:white;border:1px solid #dce2db;border-radius:12px;padding:24px}img{width:100%;border-radius:6px}nav{display:flex;gap:10px;flex-wrap:wrap}a{color:#315f49;padding:9px;background:#eaf0e8;border-radius:6px;text-decoration:none}p{line-height:1.65}.notice{padding:16px;background:#fff7df;border-radius:8px;margin-bottom:24px}</style><h1>text2IFC · 输入与 IFC 人工检查</h1><p>2026-09-08 · 实际模型、实际属性、保留完整尝试</p><div class="notice">待人工验收，尚未安装 accepted Proof。Generation 还需完成真实 Audit；Repair 请重点核对实例直接属性关联。</div><main>''' + sections + '</main><p><a href="REPORT.md">详细状态与验证记录</a></p></html>', encoding='utf-8')
artifacts = ['generation/request.txt', 'generation/generated-review.ifc', 'generation/independent-review.json',
             'repair/request.txt', 'repair/01-original.ifc', 'repair/02-damaged.ifc', 'repair/03-repaired.ifc', 'repair/independent-review.json']
write(BASE / 'pending-review.json', {'status': 'pending_human_review', 'accepted_proof_installed': False,
    'generation_status': 'pending_live_audit_and_human_review', 'repair_status': 'pending_human_review',
    'artifacts_sha256': {p: sha(BASE / p) for p in artifacts}})
print('Wrote pending human review reports; no accepted Proof installation.')
