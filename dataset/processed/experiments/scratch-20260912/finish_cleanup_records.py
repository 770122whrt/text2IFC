import hashlib,json,shutil,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R),str(R/'src')]
from scripts.proof.package import validate_package
P=R/'docs/reports/run-cleanup-review-20260910'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result=read(P/'deletion-result.json');assert result['status']=='completed'
proposal=read(P/'deletion-proposal.json');assert all(not (R/r['target']).exists() for r in proposal['targets'])
canonical=read(P/'canonical-paths.json')['files']
for e in canonical:assert hashlib.sha256((R/e['new_path']).read_bytes()).hexdigest()==e['sha256'],e['new_path']
retired=read(P/'retired-paths.json');retired['status']='executed_verified';by={x['old_path']:x for x in canonical}
for group in retired['mappings']:
    if 'files' in group:group['files']=[by[f['old_path']] for f in group['files']]
retired['canonical_authority']='canonical-paths.json; case-specific manifest mappings, not arbitrary hash-equivalent copies'
write(P/'retired-paths.json',retired)
proof=[]
for name,manifest in [('three-storey-clarification-ab-20260910','manifest.json'),('two-storey-community-20260909','review-manifest.json')]:
    p=R/'dataset/processed/proof/generation/phase6.6'/name
    v=validate_package(p,read(p/manifest),reopen=True);assert v['status']=='passed',v
    proof.append(dict(collection=name,validation=v))
old=[]
for name in ['c-shaped-teaching-building-20260910','c-shaped-brief-debug-20260910']:
    p=R/'dataset/processed/ifc-presentation-validation'/name;fs=read(p/'FILES.json')['files']
    for f in fs:assert hashlib.sha256((p/f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
    old.append(dict(package=name,unchanged_files=len(fs)))
write(P/'post-cleanup-validation.json',dict(status='passed',targets_absent=12,canonical_copies_unchanged=len(canonical),proof_reopen=proof,original_C_evidence=old,runner_regression='10 passed; cleanup-post-budget-20260910.xml'))
shutil.copyfile(R/'.tmp/cleanup-post-budget-20260910.xml',P/'cleanup-post-budget-20260910.xml')
shutil.copyfile(R/'.tmp/execute_approved_run_cleanup.ps1',P/'execute-approved-cleanup.ps1')
report=(P/'REPORT.md').read_text(encoding='utf-8')
report=report.replace('状态：只读盘点与证据保全；尚未删除。只有用户批准本清单后才执行。','状态：用户已明确批准，实验完成后已执行并核验。')
report+='''
## 执行结果

用户回复“批准按清单删除”后，等待两次真实Brief实验结束，再核对全部9,378份源文件集合、大小、SHA-256、独占读取、路径包含关系和reparse边界。2026-09-10 15:12:07 UTC完成12目录删除，共117,626,160字节（112.18 MiB）。831份真实运行源文件的规范Proof副本在删除前后哈希一致；A/B与双层人读包重新检查及IFC重开通过。保留A/B脚本的预算回归10项通过，C原始失败与前次诊断冻结证据哈希未变。

第一次检查发现原清单的部分同字节副本指向其他未跟踪集合，第二次按目录推导发现双层request采用人读直放路径；两次均在任何删除之前停止。随后依据各自已提交Proof manifest确定规范映射，源路径/文件集合/哈希与批准清单完全不变。最终去向以[canonical-paths.json](canonical-paths.json)及[retired-paths.json](retired-paths.json)为准，原提案保留当时字节和pending状态，仅作为授权快照。

证据保全已先推送：A/B为4e8a704c，双层为9dfd91b4。双层仍然是人工accepted、机器blocked，不新增机器验收。已验收Proof未改动；测试临时目录不是Provider证据。

[授权](authorization.json)、[删除前核验](pre-deletion-verification.json)、[执行结果](deletion-result.json)、[删除后验证](post-cleanup-validation.json)均已保存。旧admission/FILES中的runtime路径现为历史定位，不改写旧证据，也不能将这些旧准入直接用于新的调用。后续准入须绑定规范Proof；当前额度实验与最新C任务预算完整保留。
'''
(P/'REPORT.md').write_text(report,encoding='utf-8')
location=R/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/PROOF-LOCATION.md'
with location.open('a',encoding='utf-8') as f:f.write('''
2026-09-10 用户批准后，A-revise/runtime及B-retain/runtime的298份重复文件已退役。当前机器权威为上述Proof的evidence/frozen/A-revise/runtime与evidence/frozen/B-retain/runtime，字节未变。旧FILES及admission保持历史快照，不再作为现存源目录完整性声明或新调用准入。逐项去向及验证见[清理记录](../../../../../docs/reports/run-cleanup-review-20260910/REPORT.md)。本目录脚本、输入、报告、预算和早期失败保留。
''')
(P/'.gitattributes').write_text('* -text\n',encoding='utf-8')
print(json.dumps({'status':'passed','canonical':len(canonical),'proof':proof,'old':old},ensure_ascii=False))
