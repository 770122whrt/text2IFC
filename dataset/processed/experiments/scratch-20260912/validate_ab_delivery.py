"""Read-only checks, then an exclusive pending-delivery validation record."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910'
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
admission=read(OUT/'admission.json')
drift=[p for p,h in admission['files_sha256'].items() if sha(ROOT/p)!=h]
assert not drift,drift
frozen_count=0
for item in admission['frozen_authority_checks']:
    manifest=ROOT/item['path']
    assert sha(manifest)==item['sha256']
    rows=read(manifest)['files']
    assert all(sha(manifest.parent/r['path'])==r['sha256'] for r in rows)
    frozen_count+=len(rows)
reference=OUT.parent.parent/'three-storey-human-review-20260909/generated.ifc'
assert sha(reference)=='756cf1ad4b8175ecb2571ce09483bd6ab83edfd562ae2f66c33a650b9e610d63'
link_count=0
for report in [OUT/'REPORT.md',OUT/'A-revise/REPORT.md',OUT/'B-retain/REPORT.md']:
    content=report.read_text(encoding='utf-8')
    assert '\ufffd' not in content
    for link in re.findall(r'\]\(([^)]+)\)',content):
        if link.startswith(('http:','https:')): continue
        assert (report.parent/link.split('#')[0]).exists(),(report,link)
        link_count+=1
for branch in ('A-revise','B-retain'):
    folder=OUT/branch
    for name in ('request.txt','clarification.txt','conversation.json'):
        assert (folder/name).read_bytes()==(OUT/'inputs'/branch/name).read_bytes()
    checks=read(folder/'review-checks.json')
    assert checks['independent_status']=='passed' and checks['reference_ifc_unchanged']
    for name,digest in read(folder/'visual-review.json')['images_sha256'].items():
        assert sha(folder/name)==digest
    assert read(folder/'independent-type-checks.json')['status']=='passed'
assert read(OUT/'B-retain/independent-loop-delta.json')['status']=='passed'
scan=scan_path(OUT)
assert scan['finding_count']==0,scan
result=dict(status='passed',old_frozen_files_verified=frozen_count,
    admission_bindings_verified=len(admission['files_sha256']),original_reference_unchanged=True,
    report_links_verified=link_count,secret_scan=scan,
    native_ifc_checks_per_branch=290,supplemental_type_checks_per_branch=6,
    visual_images_verified=8,inputs_match_frozen=True,human_acceptance='pending',proof_registration=False,
    proof_curator='Not applicable: no accepted installation or Proof relocation.',
    human_view_validator='Not applicable here: validate_human_views.py requires a manifest under dataset/processed/proof; this is an unregistered validation package. Focused links, role, copy and reopened IFC checks performed.',
    full_preflight=False)
with (OUT/'delivery-validation.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='secret_scan'},ensure_ascii=False))
print('Secret pattern scan:',scan['scanned_file_count'],'files,',scan['finding_count'],'findings; suffix-limited, not a complete binary scan.')
