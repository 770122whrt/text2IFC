import hashlib
import json
from pathlib import Path
import subprocess
import types

from text2ifc_agent.semantic_requirements import project_semantic_requirements

out = Path('dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/typed-appearance-rerun-20260910')
run = out/'A-revise/runtime/runs/411166603facdde6'
path = run/'calls/01-design-brief/design-brief.json'
brief = json.loads(path.read_text(encoding='utf-8'))
code = subprocess.check_output(['git','show','06abe9bd:src/text2ifc_agent/semantic_requirements.py'])
baseline = types.ModuleType('source_material_baseline')
exec(compile(code, 'source_material_baseline', 'exec'), baseline.__dict__)
before = baseline.project_semantic_requirements(brief)
after = project_semantic_requirements(brief)
valid_before = [e for e in before['expectations'] if e['kind']=='material' and e['value']]
valid_after = [e for e in after['expectations'] if e['kind']=='material']
assert before['valid'] and not after['valid']
assert len(valid_after)==19 and valid_before==valid_after
assert all(e['value'] for e in after['expectations'] if e['kind']=='material')
result={'evidence_class':'offline replay of revealed live Brief, not fresh Provider or capability metric',
    'source_path':path.as_posix(), 'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'baseline_commit':'06abe9bd','baseline_valid':before['valid'],'candidate_valid':after['valid'],
    'original_material_expectations':len([e for e in before['expectations'] if e['kind']=='material']),
    'preserved_valid_material_expectations':len(valid_after),'issues':after['issues'],
    'source_ifc_modified':False,'provider_called':False}
with (out/'diagnostics/material-source-comparison.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False))
