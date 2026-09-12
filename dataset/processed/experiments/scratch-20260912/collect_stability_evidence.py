import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
out = root/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908/scoped-offline-evidence/pipeline-stability-implementation-20260908'
out.mkdir(parents=True, exist_ok=False)
names = ['stability-t1-red', 'stability-t1-final', 'stability-t1-green-02',
 'stability-t2-red', 'stability-t2-green', 'stability-t2-green-02', 'stability-t2-green-03',
 'stability-t3-red','stability-t3-green','stability-t3-public',
 'stability-t4-red','stability-t4-green','stability-t4-public','stability-t4-public-02',
 'stability-t4-public-03','stability-t4-terminal-green','stability-t4-loop-green','stability-t4-loop-green-02',
 'stability-t5-public','stability-t5-public-02','stability-t5-contracts','stability-t5-corrections']
records = []
for name in names:
    source = root/'.tmp'/f'{name}.xml'
    if not source.exists():
        records.append({'name':name,'status':'missing_xml'})
        continue
    target = out/source.name
    shutil.copyfile(source, target)
    suites = ET.parse(target).getroot().findall('testsuite')
    records.append({'name':name, 'file':target.name, 'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'tests':sum(int(s.get('tests', 0)) for s in suites),
        'failures':sum(int(s.get('failures', 0)) for s in suites),
        'errors':sum(int(s.get('errors', 0)) for s in suites),
        'skipped':sum(int(s.get('skipped', 0)) for s in suites),
        'seconds':sum(float(s.get('time', 0)) for s in suites),
        'test_names':[t.get('classname')+'.'+t.get('name') for s in suites for t in s.findall('testcase')]})
changed = subprocess.check_output(['git','diff','--name-only','3626133d','--','src','prompts','tests/agent'], cwd=root, text=True).splitlines()
source_hashes = {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in changed if (root/p).is_file()}
payload = {'schema_version':'text2ifc/scoped-stability-verification/1.0',
 'created_at':datetime.now(timezone.utc).isoformat(), 'python':sys.version,
 'baseline':'3626133d', 'head_before_final_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
 'scope':'T1-T4 production changes and T5 scoped offline public-chain verification',
 'source_hashes':source_hashes, 'runs':records, 'overlapping_tests':True,
 'provider_transport_attempted':False, 'full_preflight_run':False,
 'compileall':'src/text2ifc_agent passed', 'git_diff_check':'task source/test paths passed',
 'live_admission':{'status':'not_admitted', 'reason':'The old admission asserted unchanged production sources; public entry and transactional field recovery have now changed. Generation Stage Preflight has not been performed for this contract.'},
 'proof_status':'No accepted registration, no rewritten real candidates or historical attempts',
 'limitations':['Not a live capability or success-rate comparison', 'Separate Generation Stage Preflight required before a real run',
                'Existing wall/door explicit conflict cases remain fail closed', 'No new real IFC Proof or human acceptance']}
(out/'verification.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'output':str(out),'xml_files':len(list(out.glob('*.xml'))),
 'missing':[r['name'] for r in records if r.get('status')=='missing_xml']}, ensure_ascii=False))
