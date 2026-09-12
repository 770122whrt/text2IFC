"""Stage-scoped admission, preserving initial failures and scoped revalidation."""
from pathlib import Path
import datetime as dt,hashlib,importlib.metadata,json,subprocess,sys,xml.etree.ElementTree as ET
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from text2ifc_agent.prompt_registry import load_prompt_registry
from text2ifc_agent.design_brief import load_design_brief_schema
from text2ifc_contract.schema import load_schema_v23,_load_schema_path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def cases(p):
    rows=list(ET.parse(p).getroot().iter('testcase'))
    assert rows and not any(r.find('skipped') is not None or r.find('error') is not None for r in rows),p
    return {(r.attrib['classname'],r.attrib['name']):r.find('failure') is None for r in rows}

parent_path=ROOT/'dataset/processed/ifc-presentation-validation/courtyard-library-20260912/continuation-01/admission.json'
parent=read(parent_path);assert parent['status']=='admitted'
changed=set(read(OUT/'implementation-paths.json'))
for p,h in parent['files_sha256'].items():
    if p not in changed:assert sha(ROOT/p)==h,p
for p,v in parent['dependencies'].items():assert importlib.metadata.version(p)==v,p
first=cases(OUT/'railing-debug/stage-02.xml');last=cases(OUT/'railing-debug/stage-03.xml')
assert all(last.values())
failures=[key for key,okay in first.items() if not okay]
assert failures and all(last.get(key) for key in failures),failures
assert read(OUT/'railing-debug/stage-02-command.json')['exit_code']==1
assert read(OUT/'railing-debug/stage-03-command.json')['exit_code']==0
checks={}
for name in ['stage-02.xml','stage-03.xml','runner-01.xml','courtyard-open-court-rails-structural-green.xml','courtyard-open-court-public-03.xml']:
    p=OUT/'railing-debug'/name;results=cases(p)
    if name!='stage-02.xml':assert all(results.values()),name
    checks[name]={'passed':sum(results.values()),'failed':sum(not v for v in results.values()),'sha256':sha(p)}
load_prompt_registry();load_design_brief_schema('text2ifc/design-brief/2.6');load_schema_v23()
for path in ['schemas/bim-json/draft/1.3/schema.json','schemas/agent/bim-json-changeset-1.3.schema.json']:_load_schema_path(ROOT/path)
validation_commands=[]
for cmd in [[sys.executable,'-m','compileall','-q','src','tests','scripts',str(OUT)],['git','diff','--check','HEAD','--',*sorted(changed)]]:
    record={'command':cmd,'started_at':dt.datetime.now(dt.timezone.utc).isoformat()}
    completed=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    record.update(exit_code=completed.returncode,stdout=completed.stdout,stderr=completed.stderr,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),timeout=False)
    validation_commands.append(record);assert completed.returncode==0,record
paths=set(parent['files_sha256'])|changed
paths.update(str(p.relative_to(ROOT)).replace('\\','/') for p in OUT.iterdir() if p.suffix in {'.py','.json','.txt'} and p.name not in {'admission.json','authorization.json'})
bound={p:sha(ROOT/p) for p in sorted(paths)}
negative=read(OUT/'railing-debug/independent-negative-first-version.json');assert negative['passed'] is False
ledger=read(ROOT/'dataset/processed/ifc-presentation-validation/courtyard-library-20260912/continuation-01/live-run/generation-budget.json')
assert len(ledger['attempts'])==9 and sum(r['tokens_charged'] for r in ledger['attempts'])==750000
assert all(r['status']!='reserved' for r in ledger['attempts'])
result={'status':'admitted','created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
 'stage':'Generation open-court: Brief2.6/BIM2.3 bounded railing and explicit beam/column facts',
 'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 'scope':'New contract through public Brief, both generation strategies, scoped recovery, review Audit and atomic final IFC; old contracts retained.',
 'parent_admission':str(parent_path.relative_to(ROOT)), 'files_sha256':bound,'dependencies':parent['dependencies'],
 'checks':checks,'validation_commands':validation_commands,'initial_failures':failures,'all_initial_failures_resolved_by':'stage-03.xml',
 'matrix':{'complete':'public suites and new railing chain; real compiler/reopen, fake transport',
 'clarification_resume':'new2.6 and old2.5 persisted interactive invoker and scope recovery tests',
 'ambiguous_unsupported':'template family/scope; bounds/parameters; unsupported old representation; semantic authority',
 'malformed_truncated':'public Brief failure evidence and unchanged admitted adapter; raw errors/tokens preserved',
 'binding_atomic':'missing attachments, ChangeSet scope/rollback, source immutability, no unexpected semantic values',
 'publication_reopen':'actual rod solids, baseline direction, world placement and spatial aggregation; fake Audit3.0 wrapper',
 'private_boundary':'Generation has no Repair source/Gold; frozen independent checker excluded from payload'},
 'independent_negative_control':'First version rejected against new design; does not prove new design success.',
 'full_preflight':False,'network_transport_attempted':False,
 'limitations':['Offline tests do not establish Provider quality or capability improvement.',
 'Initial stage had two spatial-aggregation regressions; preserved and both revalidated with affected family, not erased.',
 'Second real IFC and human review still pending.']}
with (OUT/'admission.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':'admitted','files':len(bound),'resolved_failures':len(failures)},ensure_ascii=False))
