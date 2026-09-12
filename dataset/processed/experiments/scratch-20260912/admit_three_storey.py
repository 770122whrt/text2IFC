import datetime as dt,hashlib,json,subprocess,shutil
import importlib.metadata as metadata
from pathlib import Path
from xml.etree import ElementTree as ET
out=Path('dataset/processed/ifc-presentation-validation/three-storey-human-review-20260909')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parent=Path('dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/admission/roof-admission.json')
d=json.loads(parent.read_text(encoding='utf-8')); assert d['status']=='admitted'
changed=[p for p,h in d['files_sha256'].items() if sha(p)!=h]
allowed={'src/text2ifc_agent/changeset_stage.py','src/text2ifc_agent/interactive_cli_flow.py',
 'src/text2ifc_agent/issue_normalizers.py','src/text2ifc_agent/live_pipeline.py',
 'src/text2ifc_agent/route_decision.py','src/text2ifc_agent/semantic_coverage.py',
 'src/text2ifc_quality/generated_ifc.py','prompts/agent/registry.json',
 'tests/agent/test_interactive_cli_flow.py','tests/agent/test_interactive_cli_generation.py'}
assert set(changed)==allowed,changed
for p,h in d['evidence_hashes'].items():assert sha(parent.parent/p)==h,p
for package,version in d['dependencies'].items():assert metadata.version(package)==version,package
evidence=[Path('.tmp/three-storey-admission.xml'),
 Path('dataset/processed/ifc-presentation-validation/pipeline-opening-binding-20260909/opening-binding-regression.xml'),
 Path('dataset/processed/ifc-presentation-validation/pipeline-opening-binding-20260909/wall-contract-final.xml')]
test_results=[]
for p in evidence:
    suites=list(ET.parse(p).iter('testsuite'))
    assert suites and all(int(s.get(k,0))==0 for s in suites for k in ['failures','errors','skipped'])
    test_results.append({'path':str(p),'sha256':sha(p),'tests':sum(int(s.get('tests')) for s in suites)})
for cmd in [['.venv/Scripts/python.exe','-m','compileall','-q','src/text2ifc_agent','src/text2ifc_quality'],
            ['git','diff','--check','--','src','tests','prompts','docs']]:
    assert subprocess.run(cmd,check=False).returncode==0
new=['src/text2ifc_quality/floor_openings.py','tests/ifc_quality/test_floor_opening_identity.py',
 'tests/agent/test_explicit_wall_fact_contract.py','tests/agent/test_gate_dispute_recovery.py',
 'prompts/agent/design-brief-v2.3.md','prompts/agent/bim-json-changeset-v1.5.md']
files={p:sha(p) for p in list(d['files_sha256'])+new}
for p in ['request.txt','frozen-expectations.json','check_ifc.py']:files[str(out/p)]=sha(out/p)
record={'status':'admitted','scope':'same Generation stage: new related three-storey development case; legacy_full actual run, staged offline compatibility',
 'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
 'parent_admission':{'path':str(parent),'sha256':sha(parent)},'dependencies':d['dependencies'],
 'changed_scope':changed,'new_files':new,'tests':test_results,'files_sha256':files,
 'assessment':'Additive geometry expectation 1.1 and prompt selection; public signatures, provider transport, truth boundaries, compiler and transactions unchanged. Reuse intact stage seam/full-chain/scale evidence and add current routing/fallback/public/clarification/ChangeSet revalidation. No full preflight.',
 'full_preflight':False,'network_transport_attempted':False,'invalidation':'Any recorded source/input hash or dependency change requires new assessment; failed applicable checks block transport.',
 'limits':'Offline admission only; new related case is not a blind capability comparison. Unknown prior call budget remains untouched in original task.'}
(out/'admission.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(evidence[0],out/'scoped-admission.xml')
print(json.dumps({'status':'admitted','tests':[v['tests'] for v in test_results],'changed':len(changed)}))
