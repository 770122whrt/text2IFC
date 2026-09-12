import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path
OUT=ROOT/'dataset/processed/ifc-presentation-validation/c-shaped-teaching-building-20260910'
def write(path, value):
    with path.open('x',encoding='utf-8') as file:json.dump(value,file,ensure_ascii=False,indent=2)

links=[]
for name in ['README.md','REPORT.md','RUN-HOLD.md']:
    for target in re.findall(r'\]\(([^)]+)\)',(OUT/name).read_text(encoding='utf-8')):
        if '://' in target or target.startswith('#'):continue
        resolved=(OUT/unquote(target.split('#')[0])).resolve()
        links.append(dict(source=name,target=target,exists=resolved.exists()))
assert all(row['exists'] for row in links),links
execution=json.loads((OUT/'live-run/execution.json').read_text(encoding='utf-8'))
assert execution['status']=='exception'
assert execution['budget_after']['calls_used']==1
assert execution['budget_after']['tokens_used_or_reserved']==83996
assert not list((OUT/'live-run').rglob('*.ifc'))
scan=scan_path(OUT)
assert scan['finding_count']==0,scan['findings']
write(OUT/'validation/closeout.json',dict(status='passed_for_failed_run_archival',
    actual_live_status='exception',no_live_ifc=True,links=links,artifact_scan=scan,
    product_fix_applied=False,full_preflight=False,
    missing_evidence=['Real truncated response payload; public Brief stage did not persist exception evidence.'],
    prepared_but_not_executed=['export_views.py; no live IFC exists.']))
files=[]
for path in sorted(OUT.rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts or path.suffix=='.pyc':continue
    files.append(dict(path=path.relative_to(OUT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size))
write(OUT/'FILES.json',dict(status='failed_real_run_preserved_with_declared_evidence_gap',files=files))
paths=[(OUT/row['path']).relative_to(ROOT).as_posix() for row in files]
paths.extend([str((OUT/'FILES.json').relative_to(ROOT)).replace('\\','/'),
    'tests/compiler/test_concave_footprints.py','docs/architecture/semantic-appearance-plan.md'])
(ROOT/'.tmp/cshape-closeout-pathspec.nul').write_bytes(('\0'.join(paths)+'\0').encode())
print(json.dumps(dict(files=len(files),bytes=sum(row['bytes'] for row in files),links=len(links),scan_findings=0)))
