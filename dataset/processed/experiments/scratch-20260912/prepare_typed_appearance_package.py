import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

root = Path.cwd()
base = root/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910'
parent = base/'semantic-authority-rerun-20260910'
out = base/'typed-appearance-rerun-20260910'
out.mkdir(exist_ok=True)
assert not (out/'admission.json').exists() and not (out/'A-revise').exists() and not (out/'B-retain').exists()
def put(path, content):
    if path.exists():
        assert path.read_bytes() == content or path.read_bytes().replace(b'\r\n', b'\n') == content, path
    else:
        path.write_bytes(content)
put(out/'.gitattributes', b'* -text\n')
if not (out/'inputs').exists():
    shutil.copytree(parent/'inputs',out/'inputs',ignore=shutil.ignore_patterns('__pycache__'))
for p in (out/'inputs').rglob('*'):
    if p.is_file():
        assert p.read_bytes() == (parent/'inputs'/p.relative_to(out/'inputs')).read_bytes()
runner=(parent/'run_branches.py').read_text(encoding='utf-8').replace("design_brief_schema_version='text2ifc/design-brief/2.2'", "design_brief_schema_version='text2ifc/design-brief/2.3'")
put(out/'run_branches.py', runner.encode())
put(out/'inspect_branch.py', (parent/'inspect_branch.py').read_bytes())
diag=out/'diagnostics';diag.mkdir(exist_ok=True)
for suffix in ['xml','log']:
    for name in ['typed-brief-red-20260910', 'typed-brief-green2-20260910']:
        if name == 'typed-brief-green2-20260910' and suffix == 'log':
            continue
        put(diag/(name+'.'+suffix), (root/'.tmp'/(name+'.'+suffix)).read_bytes())
source=parent/'A-revise/runtime/runs/135976189dc358f9/calls/01-design-brief/design-brief.json'
brief=json.loads(source.read_text(encoding='utf-8'))
baseline_path=diag/'baseline-semantic-requirements-2231c06b.py'
baseline_path.write_bytes(subprocess.check_output(['git','show','2231c06b:src/text2ifc_agent/semantic_requirements.py'],cwd=root))
spec=importlib.util.spec_from_file_location('frozen_projection_baseline',baseline_path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from text2ifc_agent.semantic_requirements import project_semantic_requirements
old=module.project_semantic_requirements(brief);new=project_semantic_requirements(brief)
assert old['valid'] and not new['valid']
assert sum(e['kind']=='material' for e in old['expectations'])==sum(e['kind']=='material' for e in new['expectations'])==19
report={'evidence_class':'offline mechanism replay, no Provider', 'source_path':source.relative_to(root).as_posix(),
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'baseline_commit':'2231c06b',
    'baseline_valid':old['valid'],'candidate_valid':new['valid'],
    'baseline_appearance_authorities':sum(e['kind']=='appearance' for e in old['expectations']),
    'candidate_appearance_authorities':sum(e['kind']=='appearance' for e in new['expectations']),
    'preserved_material_expectations':19, 'candidate_issues':new['issues'],
    'limits':'Local source-grammar boundary; not a complete pipeline benchmark or unseen capability claim.'}
(diag/'projection-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['baseline_valid','candidate_valid','baseline_appearance_authorities','candidate_appearance_authorities','preserved_material_expectations']}))
