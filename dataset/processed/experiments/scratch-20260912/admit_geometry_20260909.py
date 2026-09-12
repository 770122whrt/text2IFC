import datetime as dt, hashlib, json, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/admission'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=OUT/'admission.json'
record=json.loads(base.read_text(encoding='utf-8'))
assert record['status']=='admitted'
evidence=[]
for name in ['geometry-contract-green02.xml','geometry-context.xml','geometry-legacy.xml']:
    p=OUT/name;tests=list(ET.parse(p).iter('testcase'))
    assert tests and not any(t.find(k) is not None for t in tests for k in ['failure','error','skipped'])
    evidence.append({'path':name,'sha256':sha(p),'passed':len(tests)})
record['parent_admission']={'path':'admission.json','sha256':sha(base)}
record['scoped_change']={'contract':'text2ifc/generation-authoring-contract/1.1',
    'reason':'Generic rectangle center origin and hierarchical local frames were absent from the registry projection. Actual failed candidate uses corner anchors throughout.',
    'scope':'Read-only authoring context. Public entry, IFC schema, compiler, transaction, Provider transport and budgets unchanged. Prior stage plus affected-context public full-chain and geometry tests remain applicable.',
    'red':'geometry-contract-red.xml','green':evidence,
    'claim':'Contract regression fixed; real stability unknown. No broad geometry recovery whitelist.'}
for p in list(record['files_sha256']): record['files_sha256'][p]=sha(ROOT/p)
record['admitted_at']=dt.datetime.now(dt.timezone.utc).isoformat()
record['head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
record['worktree_scoped']=subprocess.check_output(['git','status','--short','--','src','tests','docs'],cwd=ROOT,text=True)
record['network_transport_attempted']=False
for n,cmd in enumerate([[sys.executable,'-m','compileall','-q','src','tests','scripts'],['git','diff','--check','--','src','tests','docs']]):
    p=OUT/f'geometry-check-{n}.log';start=dt.datetime.now(dt.timezone.utc).isoformat()
    with p.open('x',encoding='utf-8') as f: result=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=180)
    assert result.returncode==0
    record['commands'].append({'command':cmd,'exit_code':0,'started_at':start,'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),'timeout':False,'log':p.name,'log_sha256':sha(p)})
with (OUT/'geometry-admission.json').open('x',encoding='utf-8') as f: json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':'admitted','evidence':evidence}))
