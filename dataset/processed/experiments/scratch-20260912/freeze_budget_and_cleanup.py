import hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R),str(R/'src')]
from text2ifc_agent.artifact_scan import scan_path
E=R/'dataset/processed/ifc-presentation-validation/c-shaped-brief-budget-experiment-20260910'
C=R/'docs/reports/run-cleanup-review-20260910'
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def files(p):return [x for x in sorted(p.rglob('*')) if x.is_file() and '__pycache__' not in x.parts and x.suffix!='.pyc']
(E/'.gitattributes').write_text('* -text\n',encoding='utf-8')
checked=0
for p in [E/'REPORT.md',C/'REPORT.md',R/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/PROOF-LOCATION.md']:
    for href in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if '://' in href:continue
        assert (p.parent/href).resolve().exists(),(p,href)
        checked+=1
for p in [E,C]:
    scan=scan_path(p);assert scan['finding_count']==0,scan
    write(p/'artifact-scan.json',scan)
ef=files(E)
write(E/'FILES.json',dict(status='completed_single_response_per_arm_no_ifc_no_proof',files=[dict(path=p.relative_to(E).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in ef if p.name!='FILES.json']))
proposal=json.loads((C/'deletion-proposal.json').read_text(encoding='utf-8'))
deleted=[]
for row in proposal['targets'][:2]:
    raw=subprocess.check_output(['git','ls-files','-z','--',row['target']],cwd=R)
    paths=raw.decode().strip('\0').split('\0');assert len(paths)==len(row['files'])
    allowed={row['target']+'/'+f['path'] for f in row['files']};assert set(paths)==allowed
    assert all(not (R/p).exists() for p in paths)
    deleted.extend(paths)
cleanup=[p.relative_to(R).as_posix() for p in files(C)]+deleted+['dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/PROOF-LOCATION.md']
experiment=[p.relative_to(R).as_posix() for p in files(E)]+['docs/architecture/semantic-appearance-plan.md']
for name,paths in [('cleanup',cleanup),('budget-experiment',experiment)]:
    (R/f'.tmp/{name}-stage-paths.nul').write_bytes(('\0'.join(paths)+'\0').encode())
print(json.dumps(dict(cleanup_paths=len(cleanup),deleted_tracked=len(deleted),experiment_paths=len(experiment),experiment_bytes=sum(p.stat().st_size for p in files(E)),report_links=checked,scan_findings=0)))
