import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01/admission/repair-property'
DEST.mkdir(exist_ok=False)
names=['request_stage','provider_stage','selected_provider_profiles','operation_prompt_profiles','relation_damage_public_path','property_intent','property_intent_v03','property_scope','property_admissibility','property_binding_security','property_authoring','property_confirmation','property_claim_scope_normalization','occurrence_property_operation','requested_property_l2','production_evidence','run_state','clarification_state','r1_state_isolation_contract','r1_h3_final_authority','repair_api_resource_lifecycle','orchestrator_security','orchestrator_terminal_matrix','orchestrator_application','orchestrator_resolution','resolution_flow','target_query','target_context','indexer','index_store','apply_transaction','compare','compare_fingerprints','semantic_conflict_v010','phase12_ground_truth_isolation','property_resolution_api','property_resolution_recovery']
tests=['tests/ifc_repair/test_'+n+'.py' for n in names]+['tests/agent/test_phase6_2_openai_compat.py']
cmd=[sys.executable,'-m','pytest',*tests,'-q','--basetemp',str(ROOT/'.tmp/live-repair-property-admission-20260908-01'),'--junitxml',str(DEST/'pytest.xml')]
r={'scope':'existing occurrence exact property repair only; no creation, Type reuse, new geometry or natural-property RAG','command':cmd,'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'network_transport_attempted':False,'status':'running'}
def save(): (DEST/'execution.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
save()
with (DEST/'pytest.log').open('w',encoding='utf-8') as f:
 try:
  result=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
  r.update(exit_code=result.returncode,timeout=False)
 except subprocess.TimeoutExpired:
  r.update(exit_code=None,timeout=True)
r.update(status='checks_complete',finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),log_sha256=hashlib.sha256((DEST/'pytest.log').read_bytes()).hexdigest())
save();print(json.dumps(r,ensure_ascii=False))
