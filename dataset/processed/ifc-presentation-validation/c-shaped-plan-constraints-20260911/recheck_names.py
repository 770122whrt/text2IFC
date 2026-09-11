"""Re-score frozen candidates without compiling, editing, or calling a Provider."""
import hashlib
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.dynamic_gates import evaluate_dynamic_gates

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
run=OUT/'live-run/runs/defec36086974f4b'
facts_path=run/'expected-facts.json'
facts=json.loads(facts_path.read_text(encoding='utf-8'))
rows=[]
for relative in ['evaluation-rounds/round-01/candidate.json','candidate.json']:
    path=run/relative;before=sha(path)
    result=evaluate_dynamic_gates(candidate=json.loads(path.read_text(encoding='utf-8')),expected_facts=facts)
    gate=next(g for g in result if g['name']=='dynamic_storey_name_consistency')
    assert sha(path)==before
    rows.append({'source':relative,'sha256':before,'name_gate':gate,
                 'other_gates':[{k:g[k] for k in ['name','status','issue_codes']} for g in result if g is not gate]})
with (OUT/sys.argv[1]).open('x',encoding='utf-8') as f:
    json.dump({'evidence_class':'frozen_candidate_offline_rescore','provider_calls':0,
        'module_sha256':sha(ROOT/'src/text2ifc_agent/dynamic_gates.py'),'expected_facts_sha256':sha(facts_path),
        'ifc_sha256':sha(run/'output.ifc'),'rows':rows},f,ensure_ascii=False,indent=2)
print(json.dumps([{'source':r['source'],'issues':r['name_gate']['issue_count']} for r in rows]))
