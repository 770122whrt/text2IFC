"""Install the user-accepted A/B view; retain every frozen source byte."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910'
OUT=ROOT/'dataset/processed/proof/generation/phase6.6/three-storey-clarification-ab-20260910'
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from text2ifc_agent.live_pipeline import run_final_acceptance_stage
from text2ifc_agent.artifact_scan import scan_path
from scripts.proof.package import validate_package

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:
        if isinstance(obj,str):f.write(obj)
        else:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    with src.open('rb') as a,dst.open('xb') as b:shutil.copyfileobj(a,b)

renames={'A-revise/generated.ifc':'A-revise/generated-A.ifc','B-retain/generated.ifc':'B-retain/generated-B.ifc'}
rows=read(SOURCE/'FILES.json')['files']
rows=[*rows,{'path':'FILES.json','sha256':sha(SOURCE/'FILES.json'),'size_bytes':(SOURCE/'FILES.json').stat().st_size}]
for r in rows:
    actual=SOURCE/renames.get(r['path'],r['path'])
    assert actual.stat().st_size==r['size_bytes'] and sha(actual)==r['sha256'],actual
assert not OUT.exists()
OUT.mkdir(parents=True)
write(OUT/'.gitattributes','* -text\n')
entries=[]
for r in rows:
    target='evidence/frozen/'+r['path']
    copy(SOURCE/renames.get(r['path'],r['path']),OUT/target)
    entries.append(dict(legacy_path=r['path'],path=target,sha256=r['sha256'],size_bytes=r['size_bytes']))
manifest=dict(schema_version='text2ifc/workflow-proof-package/0.1',collection_id=OUT.name,
    workflow='generation',status='accepted',human_review_status='accepted',human_review_date='2026-09-10',
    scope='User-accepted faithful Generation, including B retained known issue; not engineering or code-compliance certification.',
    cases=[],legacy_bundles=[dict(id='ab-failure-recovery',old_root=SOURCE.relative_to(ROOT).as_posix(),entries=entries)],
    source_user_renames=renames)
review=dict(status='accepted',date='2026-09-10',reviewer='user',
    user_statement='我改成generated-A和B了！然后这个内容没问题，你做整理一下计入. 具体位置还是E:\\code for project\\bimnet\\dataset\\processed\\proof',
    meaning='A和B模型与呈现已人工验收；B已知净空问题仍保留。不是工程合理性/规范通过。',
    phase_status_changed=False,source_evidence_rewritten=False,source_renames=renames)
write(OUT/'human-review.json',review)
summary=read(SOURCE/'review-summary.json')['branches']
validation={}
for branch,letter in [('A-revise','A'),('B-retain','B')]:
    case=OUT/branch
    runid=summary[branch]['run_id']
    runtime=OUT/'evidence/frozen'/branch/'runtime/runs'/runid
    # Generation's applicable complete deterministic acceptance stage; no Provider.
    recheck=OUT/'validation'/branch
    result=run_final_acceptance_stage(case_dir=runtime,output_dir=recheck,case_id=runid)
    assert result['valid'],result
    validation[branch]=result
    artifacts={}
    aliases={'generated.ifc':f'{branch}/generated.ifc','model.json':f'{branch}/runtime/runs/{runid}/generator/candidate.json'}
    names=['request.txt','clarification.txt','conversation.json','generated.ifc','model.json',
        'independent-ifc-checks.json','independent-type-checks.json','clearance-checks.json','visual-review.json']
    names += ['views/'+n+'.png' for n in ['overall','cutaway','window-double','door']]
    if letter=='B':names.append('independent-loop-delta.json')
    for name in names:
        relative=aliases.get(name,f'{branch}/{name}')
        source=OUT/'evidence/frozen'/relative
        copy(source,case/name)
        artifacts[name]=dict(sha256=sha(source),size_bytes=source.stat().st_size,source=source.relative_to(OUT).as_posix())
    copy(case/'generated.ifc',OUT/f'generated-{letter}.ifc')
    report=(SOURCE/branch/'REPORT.md').read_text(encoding='utf-8')
    report=report.replace('待人工审查，未登记 Proof。','用户已于2026-09-10人工验收，现已登记Proof。')
    report=report.replace(f'runtime/runs/{runid}/',f'../evidence/frozen/{branch}/runtime/runs/{runid}/')
    report+='\n## 收纳与验收\n\n用户已确认该版本内容无误。集合根保留便于识别的 generated-'+letter+'.ifc；本案例的 generated.ifc 是相同字节的标准入口。历史运行报告及JSON中的pending状态是验收前快照，保留原样，当前人工状态以[验收记录](../human-review.json)为准。\n'
    write(case/'REPORT.md',report)
    write(case/'evidence/README.md',f'# 机器证据\n\n[冻结运行](../../evidence/frozen/{branch}/runtime/runs/{runid}) · [运行前后记录](../../evidence/frozen/{branch}/execution.json) · [本次完整确定性验收复核](../../validation/{branch}/acceptance-metrics.json) · [人工验收](../../human-review.json)。\n\n重新编译仅用于独立复核，展示IFC保留用户验收文件原字节；不调用Provider，不重写旧报告或运行。\n')
    write(case/'FILES.json',dict(schema_version='text2ifc/package-artifacts/0.1',artifacts=artifacts))
    manifest['cases'].append(dict(case_id=branch,path=branch,status='accepted',outcome='generated',
        human_review_status='accepted',evidence_mode='live_generation_with_independent_ifc_and_human_review',
        provider_calls=summary[branch]['actual_responses_this_run'],run_id=runid,
        authority=f'evidence/frozen/{branch}/runtime/runs/{runid}/acceptance-metrics.json',
        original_role=None,ifccompare='N/A: Generation',artifacts=artifacts,
        design_review_status='revision_sampled_clearance_passed' if letter=='A' else 'retained_known_issue'))
write(OUT/'manifest.json',manifest)
write(OUT/'README.md','# 三层建筑A/B Proof\n\n用户已于2026-09-10验收。[总报告](REPORT.md) · [A IFC](generated-A.ifc) · [B IFC](generated-B.ifc)。\n\nA采用已批准澄清；B忠实保留已知楼梯净空问题，不能视为工程合规样例。\n')
write(OUT/'REPORT.md','''# 三层建筑A/B：人工已验收

用户于2026-09-10确认两份IFC内容无误，现按Generation格式计入Proof。保留用户命名generated-A / generated-B；案例内同时提供标准generated.ifc入口，字节相同。

| 分支 | 用户决定 | 真实运行与独立检查 | 文件 |
|---|---|---|---|
| A | 澄清后调整内部布局 | 3次响应；290/290项，零净空采样0/108 | [IFC](generated-A.ifc) · [报告与输入](A-revise/REPORT.md) |
| B | 明确保留原设计 | 5次响应；一轮受限洞口标高校正；290/290项，零净空采样3/108 | [IFC](generated-B.ifc) · [报告与输入](B-retain/REPORT.md) |

两案各6项补充Type检查通过，仅4个必要门Style；8张原生IFC图片已检查。原始Provider输入/响应、完整loop、独立检查、历史账本和审批均完整保存在[evidence/frozen](evidence/frozen)。本次收纳另对两案运行完整Generation确定性Final Acceptance，复核Schema、语义、编译重读、几何、Audit决定绑定及secret scan，不调用Provider。

**验收含义：忠实建模与呈现获用户认可。B的已知零净空问题仍存在，不表示安全、工程合理或规范通过。** A的采样也不替代结构、疏散、防火、栏杆等完整审查。[人工验收原文](human-review.json) · [完整原始报告](evidence/frozen/REPORT.md)。

原始报告中的pending仅表示验收前历史状态；冻结文件不重写。此次不改变Phase状态、不声称普遍成功率提升。新案例稳定性检验另行保留全部尝试。
''')
validated=validate_package(OUT,manifest)
assert validated['status']=='passed',validated
scan=scan_path(OUT);assert scan['finding_count']==0,scan
for r in rows:
    assert sha(SOURCE/renames.get(r['path'],r['path']))==r['sha256']
write(OUT/'validation/installation.json',dict(status='passed',human_view=validated,
    final_acceptance=validation,source_frozen_files_verified=len(rows),source_unchanged=True,
    aliases={letter:sha(OUT/f'generated-{letter}.ifc') for letter in ['A','B']},secret_scan=scan,
    full_preflight=False,provider_calls_during_installation=0))
print(json.dumps({'status':'installed','path':str(OUT),'validation':validated},ensure_ascii=False))
