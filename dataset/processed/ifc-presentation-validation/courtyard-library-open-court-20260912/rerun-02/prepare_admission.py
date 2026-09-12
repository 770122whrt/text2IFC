"""Scoped revalidation over the admitted open-layout stage; no network."""
from pathlib import Path
import datetime as dt, hashlib, importlib.metadata, json, subprocess, sys
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))

changed = [
 'src/text2ifc_contract/property_validation.py', 'src/text2ifc_contract/validation_v2.py',
 'src/text2ifc_agent/semantic_requirements.py', 'src/text2ifc_agent/brief_semantic_roles.py',
 'src/text2ifc_agent/design_brief.py', 'src/text2ifc_agent/brief_semantic_repair.py',
 'prompts/agent/registry.json', 'prompts/agent/design-brief-v2.24.md',
 'prompts/agent/design-brief-v2.25.md', 'prompts/agent/design-brief-semantic-repair-v1.6.md',
 'tests/agent/test_wall_layout_constraints.py', 'tests/agent/test_brief_property_admissibility.py',
 'tests/agent/test_stair_appearance_target.py']
parent_path = OUT.parent/'rerun-01/admission.json'
parent = read(parent_path)
assert parent['status'] == 'admitted'
for name, value in parent['files_sha256'].items():
    if name not in changed: assert sha(ROOT/name) == value, name
for name, version in parent['dependencies'].items():
    assert importlib.metadata.version(name) == version, name
xml = OUT.parent/'property-debug/stage-02.xml'
rows = list(ET.parse(xml).getroot().iter('testcase'))
assert rows and all(not any(r.find(k) is not None for k in ['failure','error','skipped']) for r in rows)
from text2ifc_agent.prompt_registry import load_prompt_registry
from text2ifc_agent.design_brief import load_design_brief_schema
load_prompt_registry(); load_design_brief_schema('text2ifc/design-brief/2.7')
commands = []
for command in [[sys.executable,'-m','compileall','-q',*[str(ROOT/p) for p in changed if p.endswith('.py')],str(OUT)],
                ['git','diff','--check','HEAD','--',*changed]]:
    result = subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    commands.append({'command':command,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    assert result.returncode == 0
paths = set(parent['files_sha256']) | set(changed) | {str(xml.relative_to(ROOT)),str(parent_path.relative_to(ROOT))}
paths.update(str(p.relative_to(ROOT)) for p in OUT.iterdir() if p.suffix in {'.py','.json','.txt'} and p.name != 'admission.json')
snapshot = {p.replace('\\','/'):sha(ROOT/p) for p in sorted(paths)}
record = {'status':'admitted','stage':'Brief2.7 property admissibility and visible stair appearance targets',
 'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
 'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 'parent_admission':str(parent_path.relative_to(ROOT)), 'worktree_changes':changed,
 'files_sha256':snapshot,'dependencies':parent['dependencies'],
 'checks':{'stage-02.xml':{'passed':len(rows),'failed':0,'skipped':0,'sha256':sha(xml)}},
 'validation_commands':commands,'full_preflight':False,'network_transport_attempted':False,
 'scope':'Scoped revalidation of shared properties, new Brief roles and immutable prompts, existing recovery preservation, both generation strategies, public full-loop wrapper including compilation/reopen/Audit. Prior unchanged stage-seam checks retained.',
 'limitations':['Offline fake Provider proves wiring, not live reliability or capability improvement.',
 'Prior genuine failures and rejected diagnostic IFC remain unaccepted; next attempt starts with fresh real Brief.']}
with (OUT/'admission.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':'admitted','files':len(snapshot),'passed':len(rows)}))
