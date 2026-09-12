import datetime as dt, hashlib, json, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
out=root/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/admission'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=out/'geometry-admission.json'; record=json.loads(parent.read_text(encoding='utf-8'))
assert record['status']=='admitted'
changed=[p for p,h in record['files_sha256'].items() if sha(root/p)!=h]
assert changed==['src/text2ifc_agent/complex_scaffold.py'],changed
xml=root/'.tmp/roof-refactor-green-20260909.xml'; cases=list(ET.parse(xml).iter('testcase'))
assert len(cases)==30 and not any(c.find(k) is not None for c in cases for k in ['failure','error','skipped'])
for name in ['roof-refactor-red-20260909.xml','roof-refactor-green-20260909.xml','roof-refactor-preservation-20260909.json']:
    shutil.copyfile(root/'.tmp'/name,out/name)
for p in changed+['src/text2ifc_agent/geometry_authoring.py','tests/agent/test_geometry_authoring.py']:
    record['files_sha256'][p]=sha(root/p)
record['parent_admission']={'path':parent.name,'sha256':sha(parent)}
record['scoped_change']={'scope':'Roof center lowering only, public entry/schema/transport/truth/transactions unchanged',
    'validated_commit':'da2d043f','green':'roof-refactor-green-20260909.xml','passed':30,
    'preservation':'roof-refactor-preservation-20260909.json','change_assessment':'Same-stage scoped revalidation; no Full Preflight required'}
record['head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
record['admitted_at']=dt.datetime.now(dt.timezone.utc).isoformat()
for n,cmd in enumerate([[sys.executable,'-m','compileall','-q','src','tests','scripts'],['git','diff','--check','--','src','tests','scripts','docs']]):
    p=out/f'roof-check-{n}.log';start=dt.datetime.now(dt.timezone.utc).isoformat()
    with p.open('x',encoding='utf-8') as f: result=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=180)
    assert result.returncode==0
    record['commands'].append({'command':cmd,'exit_code':0,'started_at':start,'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),'timeout':False,'log':p.name,'log_sha256':sha(p)})
record['network_transport_attempted']=False
with (out/'roof-admission.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':'admitted','changed':changed,'scoped_tests':len(cases)}))
