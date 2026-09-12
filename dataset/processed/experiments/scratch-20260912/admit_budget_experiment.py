import hashlib,json,shutil,sys,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'src')]
out=root/'dataset/processed/ifc-presentation-validation/c-shaped-brief-budget-experiment-20260910'
prior=out.parent/'c-shaped-brief-debug-20260910'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parent=read(prior/'admission.json')
drift=[p for p,h in parent['files_sha256'].items() if sha(root/p)!=h]
allowed={'docs/architecture/semantic-appearance-plan.md','src/text2ifc_agent/design_brief.py','prompts/agent/registry.json'}
assert set(drift)<=allowed,drift
post=list(ET.parse(prior/'validation/brief-version-verified.xml').getroot().iter('testcase'))
tests=list(ET.parse(root/'.tmp/budget96-final.xml').getroot().iter('testcase'))
assert len(post)==158 and len(tests)==38
assert all(not any(c.tag in ['failure','error','skipped'] for c in t) for t in post+tests)
validation=out/'validation';validation.mkdir(exist_ok=False)
for name in ['budget96-scoped','budget96-final']:
    for suffix in ['xml','log']:shutil.copyfile(root/'.tmp'/f'{name}.{suffix}',validation/f'{name}.{suffix}')
bound={p:sha(root/p) for p in parent['files_sha256']}
for p in [root/'prompts/agent/design-brief-v2.9.md',prior/'validation/brief-version-verified.xml',prior/'live-attempt/generation-budget.json']:
    bound[p.relative_to(root).as_posix()]=sha(p)
for p in out.rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts:bound[p.relative_to(root).as_posix()]=sha(p)
admission=dict(status='admitted',scope='Current v2.9 Brief output-cap experiment only; no product/default changes.',
    parent_admission_sha256=sha(prior/'admission.json'),changed_bindings=drift,
    changed_binding_validation='158 post-v2.9 tests passed; inherited public path matrix unchanged.38 new experiment/budget/Brief seam checks passed.',
    dependencies=parent['dependencies'],files_sha256=bound,scoped_tests=38,post_prompt_tests=158,
    full_preflight=False,network_transport_attempted=False,
    limitations='One paired exploration. Not an end-to-end IFC or reliability/capability evaluation. Earlier no-tests run was a command path typo; corrected full intended scope passed.')
(out/'admission.json').write_text(json.dumps(admission,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':'admitted','bindings':len(bound),'scoped':38,'post_prompt':158}))
