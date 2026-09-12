import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'src')]
from scripts.proof.package import validate_package
from text2ifc_agent.artifact_scan import scan_path
p=root/'dataset/processed/proof/generation/phase6.6/two-storey-community-20260909'
document=json.loads((p/'review-manifest.json').read_text(encoding='utf-8'))
result=validate_package(p,document,reopen=True)
assert result['status']=='passed',result
assert document['accepted_proof_installed'] is False and document['machine_acceptance_status']=='blocked'
scan=scan_path(p);assert not scan['finding_count'],scan['findings']
files=[x for x in sorted(p.rglob('*')) if x.is_file() and '__pycache__' not in x.parts]
inventory=[dict(path=x.relative_to(p).as_posix(),sha256=hashlib.sha256(x.read_bytes()).hexdigest(),bytes=x.stat().st_size) for x in files]
out=root/'docs/reports/run-cleanup-review-20260910'
(out/'two-storey-preservation.json').write_text(json.dumps(dict(validation=result,scan=scan,files=inventory,
    human_review='accepted',machine='blocked',accepted_machine_install=False),ensure_ascii=False,indent=2),encoding='utf-8')
(root/'.tmp/two-storey-preserve-pathspec.nul').write_bytes(('\0'.join(x.relative_to(root).as_posix() for x in files)+'\0').encode())
print(json.dumps({'files':len(files),'validation':result,'scan_findings':0}))
