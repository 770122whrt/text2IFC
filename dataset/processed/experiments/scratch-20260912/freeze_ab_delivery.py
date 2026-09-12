import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910'
files=[p for p in sorted(OUT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='FILES.json']
rows=[dict(path=p.relative_to(OUT).as_posix(),size_bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
manifest=dict(schema_version='text2ifc/curated-evidence-files/1.0',
    status='A/B real Generation complete; independent and assistant visual review complete; pending human review; no accepted Proof',
    files=rows)
with (OUT/'FILES.json').open('x',encoding='utf-8') as f:
    json.dump(manifest,f,ensure_ascii=False,indent=2)
stage=[*files,OUT/'FILES.json',ROOT/'tests/agent/test_authorized_budget_extension.py',ROOT/'docs/architecture/semantic-appearance-plan.md']
(ROOT/'.tmp/ab-delivery-pathspec.nul').write_bytes(b'\0'.join(p.relative_to(ROOT).as_posix().encode('utf-8') for p in stage)+b'\0')
print(json.dumps({'frozen_files':len(files),'total_bytes':sum(r['size_bytes'] for r in rows),'stage_paths':len(stage)}))
