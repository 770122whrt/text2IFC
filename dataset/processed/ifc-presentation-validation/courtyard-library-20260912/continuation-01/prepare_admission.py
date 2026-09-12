"""Scoped revalidation of admitted Generation; freeze continuation before transport."""
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent; BASE=OUT.parent; ROOT=OUT.parents[4]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from text2ifc_agent.artifact_scan import scan_path
from text2ifc_agent.prompt_registry import load_prompt_registry

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

parent=read(BASE/'rerun-04/admission.json');assert parent['status']=='admitted'
changed=['src/text2ifc_agent/filling_relationship_recovery.py','src/text2ifc_agent/live_pipeline.py',
    'src/text2ifc_agent/interactive_cli_flow.py','src/text2ifc_presentation/generation.py',
    'src/text2ifc_compiler/semantic_verification.py','tests/agent/test_filling_relationship_recovery.py',
    'tests/compiler/test_transparency_only_appearance.py','docs/architecture/semantic-appearance-plan.md']
for p,h in parent['files_sha256'].items():
    if p not in changed:assert sha(ROOT/p)==h,p
for p,v in parent['dependencies'].items():assert importlib.metadata.version(p)==v,p
checks={}
for name in ['scoped.xml','public-loops.xml','public-continuation-final.xml']:
    p=OUT/name;cases=list(ET.parse(p).getroot().iter('testcase'))
    assert cases and not any(n.tag in {'failure','error','skipped'} for c in cases for n in c),name
    checks[name]={'passed':len(cases),'sha256':sha(p)}
assert read(OUT/'offline-continuation-result.json')['source_unchanged']
load_prompt_registry()
assert subprocess.run([sys.executable,'-m','compileall','-q','src/text2ifc_agent','src/text2ifc_compiler','src/text2ifc_presentation'],cwd=ROOT).returncode==0
assert subprocess.run(['git','diff','--check','HEAD','--',*changed],cwd=ROOT).returncode==0
origin=BASE/'rerun-04/live-run/runs/3cd339b0be4fd872'
ledger=origin/'generation-budget.json';a=read(ledger)['attempts']
assert len(a)==8 and sum(r['tokens_charged'] for r in a)==626258
assert all(r['status']!='reserved' for r in a)
preview=read(BASE/'rerun-04/payload-preview.json')
preview.update(purpose='Continue the unchanged live Generator response through deterministic missing-attachment repair and one new real Audit; no new Brief or Generator call.',
    previous_budget_sha256=sha(ledger),inherited_calls=8,inherited_tokens=626258,
    source_generator_response_id='c71fd68d-5df7-4e56-91b3-444eb4937315',
    excluded=['IFC bytes','independent evaluators and their results','private Gold','other-case data','credential values'])
write(OUT/'payload-preview.json',preview)
approval=read(BASE/'rerun-04/authorization.json');approval.update(
    payload_preview_sha256=sha(OUT/'payload-preview.json'),previous_budget_sha256=sha(ledger),
    basis='Existing explicit user authorization for courtyard real Provider Generation/Audit, GitHub evidence push and exact part appearance. This is the same frozen case and destination within its unchanged cumulative budget.')
write(OUT/'authorization.json',approval)
bound=dict(parent['files_sha256'])
for p in [*(ROOT/n for n in changed),*(p for p in origin.rglob('*') if p.is_file()),
    BASE/'rerun-04/admission.json',BASE/'check_ifc.py',BASE/'check_part_colours.py',
    *(OUT/n for n in ['run_case.py','test_continuation.py','prepare_admission.py','payload-preview.json','authorization.json','offline-continuation-result.json',*checks])]:
    bound[p.relative_to(ROOT).as_posix()]=sha(p)
scan=scan_path(OUT);assert scan['finding_count']==0,scan
write(OUT/'admission.json',{'status':'admitted','created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
    'stage':'Same Generation stage: frozen attachment and alpha-only recovery; declared Audit continuation',
    'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'changed_scope':changed,'parent_admission':'rerun-04/admission.json','files_sha256':bound,
    'dependencies':parent['dependencies'],'checks':checks,'scan':scan,
    'validation_level':'scoped revalidation of previously admitted stage, including complete public loops and exact continuation entry',
    'inherited_boundary':'Unchanged registered schemas/prompts, Provider adapter, clarification/resume, private isolation, atomic compiler and budget contracts remain bound to parent admission.',
    'source_lineage':'Original failed run immutable; no fake Generator call, no supervisor edits to entities. Production bounded repair appends only frozen void/fill links.',
    'limitations':['Tests are offline, including real-source replay plus fake Audit; no capability improvement claim.',
        'The new real run is a declared stage continuation, not a fresh automatic end-to-end run.',
        'Original failures and all budget attempts remain in their original locations. Human IFC acceptance is pending.'],
    'full_preflight':False,'network_transport_attempted':False})
print(json.dumps({'status':'admitted','checks':checks,'inherited_tokens':626258}))
