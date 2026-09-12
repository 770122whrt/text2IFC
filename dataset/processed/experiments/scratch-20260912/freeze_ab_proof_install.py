import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dataset/processed/proof/generation/phase6.6/three-storey-clarification-ab-20260910'
SOURCE=ROOT/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910'
docs=[OUT/'README.md',OUT/'REPORT.md',*[OUT/b/f for b in ['A-revise','B-retain'] for f in ['REPORT.md','evidence/README.md']],SOURCE/'PROOF-LOCATION.md']
count=0
for p in docs:
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        assert (p.parent/link).exists(),(p,link)
        count+=1
(OUT/'validation/presentation-links.json').write_text(json.dumps(dict(status='passed',checked_links=count,broken_links=0),indent=2),encoding='utf-8')
files=[p for p in sorted(OUT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p!=OUT/'FILES.json']
rows=[dict(path=p.relative_to(OUT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size_bytes=p.stat().st_size) for p in files]
with (OUT/'FILES.json').open('x',encoding='utf-8') as f:
    json.dump(dict(schema_version='text2ifc/curated-evidence-files/1.0',status='human accepted; generation final acceptance revalidated; B retains known issue',files=rows),f,ensure_ascii=False,indent=2)
paths=[*files,OUT/'FILES.json',ROOT/'dataset/processed/proof/PROOF-INVENTORY.json',ROOT/'docs/architecture/semantic-appearance-plan.md',SOURCE/'PROOF-LOCATION.md']
for b,l in [('A-revise','A'),('B-retain','B')]:paths += [SOURCE/b/'generated.ifc',SOURCE/b/f'generated-{l}.ifc']
(ROOT/'.tmp/ab-proof-pathspec.nul').write_bytes(b'\0'.join(p.relative_to(ROOT).as_posix().encode() for p in paths)+b'\0')
print(json.dumps(dict(frozen_files=len(files),staged_explicit_paths=len(paths),links=count)))
