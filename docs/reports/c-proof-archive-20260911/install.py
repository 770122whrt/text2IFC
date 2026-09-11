"""Curate the accepted C result and copy prior experiments without deleting sources."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from scripts.proof.package import contained, validate_package
from text2ifc_agent.live_pipeline import run_final_acceptance_stage
from text2ifc_agent.artifact_scan import scan_path

BASE = ROOT / 'dataset/processed/ifc-presentation-validation'
SOURCE = BASE / 'c-shaped-current-provider-20260911'
OUT = ROOT / 'dataset/processed/proof/generation/phase6.6/c-shaped-teaching-20260911'
ARCHIVE = ROOT / 'dataset/processed/experiments'
HERE = Path(__file__).resolve().parent
RUN = '05c6de3a19ed20f9'
NAMES = [
    'audit-token-pair-20260911', 'c-shaped-brief-budget-experiment-20260910',
    'c-shaped-brief-debug-20260910', 'c-shaped-clarified-entry-20260911',
    'c-shaped-gate-debug-20260911', 'c-shaped-integrated-20260911',
    'c-shaped-plan-constraints-20260911', 'c-shaped-teaching-building-20260910',
    'c-shaped-wall-join-20260911',
]

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    with p.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='\n') as stream:
        if isinstance(value, str):
            stream.write(value)
        else:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')

def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as src, target.open('xb') as dst:
        shutil.copyfileobj(src, dst)
    assert sha(source) == sha(target), target

assert not OUT.exists() and not ARCHIVE.exists(), 'Refuse to overwrite a collection'
rows = read(SOURCE / 'FILES.json')['files']
rows += [dict(path='FILES.json', sha256=sha(SOURCE/'FILES.json'), bytes=(SOURCE/'FILES.json').stat().st_size)]
renames = {'generated.ifc': 'generated-C.ifc'}
for row in rows:
    p = contained(SOURCE, renames.get(row['path'], row['path']))
    assert p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], p
assert sha(SOURCE/'generated-C.ifc') == sha(SOURCE/f'live-run/runs/{RUN}/output.ifc')
entries = []
for row in rows:
    target = 'evidence/frozen/' + row['path']
    copy(SOURCE / renames.get(row['path'], row['path']), OUT / target)
    entries.append(dict(legacy_path=row['path'], path=target, sha256=row['sha256'], size_bytes=row['bytes']))
write(OUT/'.gitattributes', '** -text\n')
runtime = OUT / f'evidence/frozen/live-run/runs/{RUN}'
recheck = run_final_acceptance_stage(case_dir=runtime, output_dir=OUT/'validation/final-acceptance', case_id=RUN)
assert recheck['valid'], recheck
case = OUT / 'C-teaching'
artifacts = {}
aliases = {'model.json': f'live-run/runs/{RUN}/generator/candidate.json'}
names = ['request.txt', 'conversation.json', 'CLARIFICATIONS.md', 'generated.ifc', 'model.json',
         'independent-ifc-check.json', 'usage-summary.json']
names += ['views/'+p.name for p in sorted((SOURCE/'views').iterdir()) if p.is_file()]
for name in names:
    source = OUT / 'evidence/frozen' / aliases.get(name, name)
    copy(source, case/name)
    artifacts[name] = dict(sha256=sha(source), size_bytes=source.stat().st_size, source=source.relative_to(OUT).as_posix())
copy(case/'generated.ifc', OUT/'generated-C.ifc')
write(case/'FILES.json', dict(schema_version='text2ifc/package-artifacts/0.1', artifacts=artifacts))
write(OUT/'human-review.json', dict(status='accepted', date='2026-09-11', reviewer='user',
    user_statement='非常好！整理一下内容和之前的实验内容 我已经检验完毕了这个是可以放进proof中的内容。',
    meaning='本次C型教学楼模型及呈现人工验收通过；不是完整工程规范认证。',
    run_id=RUN, ifc_sha256=sha(case/'generated.ifc'), source_renames=renames,
    source_evidence_rewritten=False, phase_status_changed=False))
manifest = dict(schema_version='text2ifc/workflow-proof-package/0.1', collection_id=OUT.name,
    workflow='generation', status='accepted', human_review_status='accepted', human_review_date='2026-09-11',
    scope='User-accepted faithful Generation; not full engineering/code-compliance certification.',
    cases=[dict(case_id='C-teaching', path='C-teaching', status='accepted', outcome='generated',
        human_review_status='accepted', evidence_mode='live_generation_with_independent_ifc_and_human_review',
        provider_calls=3, run_id=RUN, authority=f'evidence/frozen/live-run/runs/{RUN}/acceptance-metrics.json',
        original_role=None, ifccompare='N/A: Generation', artifacts=artifacts)],
    legacy_bundles=[dict(id='frozen', old_root=SOURCE.relative_to(ROOT).as_posix(), entries=entries)],
    source_user_renames=renames)
write(OUT/'manifest.json', manifest)
write(OUT/'README.md', '# C 型教学楼 Proof\n\n人工已验收，2026-09-11。[报告](REPORT.md) · [generated-C.ifc](generated-C.ifc) · [中文输入](C-teaching/request.txt)。\n')
write(OUT/'REPORT.md', '''# C 型教学楼：人工已验收

用户于2026-09-11确认本次模型可以收入Proof。保留用户命名 [generated-C.ifc](generated-C.ifc)，案例内的标准 generated.ifc 与它逐字节一致。

- [案例报告、输入与图片](C-teaching/REPORT.md) · [人工验收记录](human-review.json)
- 真实运行 `05c6de3a19ed20f9`：Brief、Generator、Audit 共3次调用，首次通过，无修复loop；本轮220,720 token。
- 独立重开IFC检查485/485；三层、每层3个空间、21窗、7门、2梯段。入口按用户澄清位于西墙距南侧4.2米。
- 本次收纳重新执行完整Generation确定性Final Acceptance，检查Schema、语义、几何、编译重读、Audit绑定及secret scan；未调用Provider。

历史报告和JSON中的pending是验收前快照，原字节保存在 [冻结证据](evidence/frozen/REPORT.md)。当前人工状态以本集合human-review.json为准。重编译只用于复核，展示IFC保持用户验收字节。

Audit原文“每层9个空间”为叙述错误；实际每层3个、全楼9个。人工验收不代表结构、消防、楼梯净高或可施工性全面认证，不改变Phase状态，也不证明系统成功率提升。
''')
write(case/'REPORT.md', '''# 三层 C 型教学活动楼

**人工已验收，2026-09-11。** [完整IFC](generated.ifc) · [原始中文请求](request.txt) · [真实澄清](CLARIFICATIONS.md) · [完整对话](conversation.json) · [正式BIM JSON](model.json)。

本次从原始请求和已批准入口澄清开始真实生成，没有复用旧Brief、候选或IFC作为输入，也没有手工修改IFC。`legacy_full`；代码d0c39dc4；请求模型deepseek-v4-flash，响应字段deepseek-flash。

| 阶段 | Input | Output（含推理） | 其中推理 | 总token |
|---|---:|---:|---:|---:|
| Brief | 19715 | 46754 | 35821 | 66469 |
| Generator | 43246 | 39777 | 17184 | 83023 |
| Audit | 62316 | 8912 | 7334 | 71228 |
| 本轮 | 125277 | 95443 | 60339 | 220720 |

[独立IFC检查](independent-ifc-check.json)485项通过；C历史账本累计20次、1,597,750 token，包含失败尝试。新增token与历史累计不能相加重复统计；独立Audit去重实验使用另一份账本。

[整体图片](views/overall.png) · [首层](views/ground-floor.png) · [窗](views/IfcWindow.png) · [门](views/IfcDoor.png) · [原有旋转视图](views/viewer.html)。原生网格64个有表示实体、失败0；图片直接来自IFC，未生成额外概念图或网页。

模型按请求表达C型、墙角、洞口、宿主、材料和部件颜色。原Audit“每层9空间”的口误以独立IFC结果更正为每层3个、全楼9个；真实响应保留原样。

[机器证据入口](evidence/README.md)。本案例证明一次已见场景的真实运行与人工验收通过，不是完整工程合规认证或盲测能力提升。
''')
write(case/'evidence/README.md', f'# 机器证据\n\n[冻结运行](../../evidence/frozen/live-run/runs/{RUN}) · [原报告](../../evidence/frozen/REPORT.md) · [收纳复核](../../validation/final-acceptance/acceptance-metrics.json) · [人工验收](../../human-review.json)。旧路径通过集合manifest逐文件还原。\n')
validated = validate_package(OUT, manifest)
assert validated['status'] == 'passed', validated
scan = scan_path(OUT)
assert scan['finding_count'] == 0, scan
write(OUT/'validation/installation.json', dict(status='passed', human_view=validated, final_acceptance=recheck,
    source_frozen_files_verified=len(rows), source_unchanged=True, secret_scan=scan,
    full_preflight=False, provider_calls_during_installation=0))

# The experiment namespace preserves relative sibling paths and historical bytes.
ARCHIVE.mkdir()
write(ARCHIVE/'.gitattributes', '** -text\n')
bundles = []
for name in NAMES:
    source = BASE/name
    records = []
    for item in sorted(source.rglob('*')):
        rel = item.relative_to(source).as_posix()
        contained(source, rel)
        if not item.is_file() or '__pycache__' in item.parts:
            continue
        target = ARCHIVE/name/rel
        copy(item, target)
        records.append(dict(legacy_path=rel, path=f'{name}/{rel}', sha256=sha(item), size_bytes=item.stat().st_size))
    bundles.append(dict(id=name, old_root=source.relative_to(ROOT).as_posix(), entries=records))
write(ARCHIVE/'c-token-archive-20260911.json', dict(status='archived_not_accepted_proof',
    source_bytes_unchanged=True, source_directories_deleted=False, bundles=bundles))
write(ARCHIVE/'README.md', '''# C 型建造与 token 实验记录

本目录独立保存实验和调试历史，含成功、失败、原始Provider响应、token账本、配置、脚本和验证记录。它们不因最终C被验收而自动成为accepted Proof。旧报告中的“下一步”和pending为当时状态，原字节不改。旧路径至当前路径、大小与SHA-256见 [归档索引](c-token-archive-20260911.json)。不收纳可重建的 __pycache__。

## 阅读顺序

| 内容 | 原记录 | 结论 |
|---|---|---|
| Brief输出额度96K/64K | [实验](c-shaped-brief-budget-experiment-20260910/REPORT.md) | 两次均完整但待澄清；提高上限不能证明稳定性提升 |
| Audit真实full/去重配对 | [实验](audit-token-pair-20260911/REPORT.md) | input减少24.20%；仅一个已见案例，质量非劣效尚未证明 |
| C首次Brief截断 | [原案例](c-shaped-teaching-building-20260910/) | 保留失败；最初缺失的raw响应不能补造 |
| Brief失败记录修复与单阶段诊断 | [记录](c-shaped-brief-debug-20260910/) | 单阶段成功不等于完整IFC成功 |
| C公共链路与入口澄清 | [集成](c-shaped-integrated-20260911/) · [入口](c-shaped-clarified-entry-20260911/REPORT.md) | 入口4.2米是用户真实批准；诊断IFC未获最终放行 |
| 门禁与去重零收益定位 | [记录](c-shaped-gate-debug-20260911/) | 首次Audit没有足量相同大对象，回退full；不能把字节估算当真实token |
| 墙界与局部修复失败 | [记录](c-shaped-wall-join-20260911/REPORT.md) | 旧完整JSON修复丢关系；保留失败分母 |
| 墙约束与名称误报修复 | [记录](c-shaped-plan-constraints-20260911/REPORT.md) | 前一轮IFC及后续离线修复，属于开发比较 |
| 最新C人工验收 | [Proof](../proof/generation/phase6.6/c-shaped-teaching-20260911/REPORT.md) | 新3次真实调用，无修复loop，独立485/485 |

唯一后续计划为 [token-efficiency-plan.md](../../../docs/architecture/token-efficiency-plan.md)。既有 [离线去重分析](../../../docs/validation/token-efficiency/20260911-audit-dedup/REPORT.md) 和 [C消耗归因](../../../docs/validation/token-efficiency/20260911-c-scope-diagnosis/REPORT.md) 仍保留原处，通过此入口串联。

## 计量与复用边界

C累计20次/1,597,750 token包括额度实验等C历史；Audit配对另计2次/171,516 token。各阶段累计值不可求和。reasoning已包含在output中。不同代码、Prompt和随机输出下的两次C运行不是受控token消融。

冻结admission、数据库引用和日志里的原绝对路径仅表示历史环境；不能直接复用为新真实调用准入。原脚本原样保存用于审计，受影响的回归测试应改用本归档路径；任何真实重跑须创建新运行目录并建立当前准入。
''')
for row in rows:
    assert sha(SOURCE/renames.get(row['path'],row['path'])) == row['sha256']
write(HERE/'copy-validation.json', dict(status='passed', proof=validated,
    proof_frozen_files=len(rows), experiment_collections=len(bundles),
    experiment_files=sum(len(b['entries']) for b in bundles),
    experiment_bytes=sum(e['size_bytes'] for b in bundles for e in b['entries']),
    deletion_performed=False, provider_calls=0))
print((HERE/'copy-validation.json').read_text(encoding='utf-8'))
