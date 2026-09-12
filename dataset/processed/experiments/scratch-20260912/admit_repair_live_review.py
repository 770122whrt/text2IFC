import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
DEST=BASE/'admission/repair-property-final';DEST.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
tests=ET.parse(BASE/'admission/repair-property/pytest.xml')
failed=[t for t in tests.iter('testcase') if t.find('failure') is not None]
assert len(failed)==1 and failed[0].get('name')=='test_large_building_indexes_initial_scope_and_source_identity'
for name in ['index-version-final.xml','repair-public-family-02.xml']:
 assert all(all(int(s.get(k,'0'))==0 for k in ['failures','errors','skipped']) for s in ET.parse(BASE/'admission'/name).iter('testsuite'))
checks=[]
for name,cmd in [('compile',[sys.executable,'-m','compileall','-q','src','scripts','tests']),('diff',['git','diff','--check'])]:
 start=dt.datetime.now(dt.timezone.utc).isoformat()
 with (DEST/(name+'.log')).open('w',encoding='utf-8') as log:r=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 assert r.returncode==0
 checks.append({'command':cmd,'started_at':start,'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),'exit_code':r.returncode,'timeout':False,'log_sha256':sha(DEST/(name+'.log'))})
files=[p for f in ['src/text2ifc_ifc_repair','src/text2ifc_agent','src/text2ifc_knowledge','schemas','prompts'] for p in (ROOT/f).rglob('*') if p.is_file() and p.suffix in ['.py','.json','.md']]
record={'status':'admitted','stage':'existing-occurrence-exact-property-repair','created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'python':sys.version,'platform':platform.platform(),'network_transport_attempted':False,'scope':'public RepairAPI on dataset vvo, one occurrence four exact PSD properties; source and geometry preserved. No create/reuse-Type/new geometry/natural-property RAG acceptance.','tests':{'baseline':'../repair-property/pytest.xml','baseline_sha256':sha(BASE/'admission/repair-property/pytest.xml'),'passed':379,'failure':'indexer version 0.6 assertion outdated; corrected to released 0.7 and 9 index tests passed','rechecks':{n:sha(BASE/'admission'/n) for n in ['index-version-final.xml','repair-public-family-02.xml']}},'checks':checks,'seams':{'truth_boundary':'test_relation_damage_public_path; test_phase12_ground_truth_isolation; test_r1_state_isolation_contract','prompt_transport_and_intent':'test_request_stage; test_selected_provider_profiles; test_phase6_2_openai_compat','clarification_restart':'test_relation_damage_public_path (3 variants); test_clarification_state; test_run_state','resolution_binding':'test_property_admissibility; test_property_binding_security; test_target_query; test_resolution_flow','apply_atomicity_reopen_L0_L1_L2_preservation':'test_apply_transaction; test_occurrence_property_operation; test_requested_property_l2; test_compare; actual public relation-damage path','publication':'test_orchestrator_terminal_matrix; test_r1_h3_final_authority; test_property_resolution_recovery','scale':'actual vvo 48935 entities in public chain; test_indexer LargeBuilding and source identity; bounded public prompt <262144 chars'},'prior_broader_attempt':{'path':'../repair/execution.json','sha256':sha(BASE/'admission/repair/execution.json'),'status':'timed_out_not_admission','scope_difference':'broader Beam/Column/door creation and historical Proof suites; outside this exact-property live case; no claim of full Repair or Phase12 acceptance'},'invalidating_boundaries':['Provider transport','public API contracts','binding/apply/source/private boundary','schema/prompt/evaluator'],'files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files},'frozen_case_sha256':sha(BASE/'repair/evaluator-private/frozen-expectations.json'),'claim':'single viability sample pending independent verification and human review'}
(DEST/'admission.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Exact property repair stage admitted; broader Repair preflight remains timed out.')
