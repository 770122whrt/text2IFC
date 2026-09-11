"""Collect this fresh real run, preserving the earlier run and cumulative budget."""
import hashlib
import json
from pathlib import Path
import shutil

OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'c-shaped-clarified-entry-20260911'
PARENT=OUT.parent/'c-shaped-plan-constraints-20260911'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2)

execution=read(OUT/'live-run/execution.json')
assert execution['status']!='running'
run=OUT/'live-run/runs'/execution['run_id']
budget=read(run/'generation-budget.json')
prior=PARENT/'live-run/runs/defec36086974f4b/generation-budget.json'
assert budget['attempts'][:17]==read(prior)['attempts']
assert sha(prior)==execution['prior_budget_sha256']
seen={}
for p in sorted(run.rglob('response-metadata.json')):
    m=read(p)
    if m.get('evidence_class')!='live':continue
    identity=m['response_id'];usage=m['usage']
    if identity in seen:
        assert seen[identity]['usage']==usage
        seen[identity]['paths'].append(p.relative_to(OUT).as_posix())
    else:seen[identity]={'response_id':identity,'model':m['model'],'usage':usage,'paths':[p.relative_to(OUT).as_posix()]}
fresh=budget['attempts'][17:]
summary={'run_id':execution['run_id'],'status':execution['status'],'source_commit':read(OUT/'admission.json')['head'],
    'new_calls':len(fresh),'new_actual_responses':len(seen),'new_tokens_charged':sum(a['tokens_charged'] for a in fresh),
    'new_input_tokens':sum(r['usage']['prompt_tokens'] for r in seen.values()),
    'new_output_tokens_including_reasoning':sum(r['usage']['completion_tokens'] for r in seen.values()),
    'new_reasoning_tokens':sum(r['usage'].get('completion_tokens_details',{}).get('reasoning_tokens',0) or 0 for r in seen.values()),
    'cumulative_calls':len(budget['attempts']),'cumulative_tokens_charged':sum(a['tokens_charged'] for a in budget['attempts']),
    'cumulative_active_seconds':sum(a['elapsed_seconds'] for a in budget['attempts']),
    'fresh_attempts':fresh,'responses':list(seen.values()),'ledger_sha256':sha(run/'generation-budget.json'),
    'prior_unchanged':True,'reused_old_brief_or_candidate':False,'full_preflight':False}
write(OUT/'usage-summary.json',summary)
for source,name in [(SOURCE/'request.txt','request.txt'),(SOURCE/'conversation.json','conversation.json')]:
    assert not (OUT/name).exists();shutil.copyfile(source,OUT/name)
    assert sha(source)==sha(OUT/name)
if execution['status']=='compiled':
    result=read(run/'case-result.json');checked=read(OUT/'independent-ifc-check.json')
    assert result['audit_passed'] and result['deterministic_gates_passed'] and result['compile_reopen_passed']
    assert checked['status']=='passed' and checked['ifc_sha256']==sha(run/'output.ifc')
    assert not (OUT/'generated.ifc').exists();shutil.copyfile(run/'output.ifc',OUT/'generated.ifc')
    assert sha(OUT/'generated.ifc')==checked['ifc_sha256']
print(json.dumps({k:v for k,v in summary.items() if k not in {'responses','fresh_attempts'}},ensure_ascii=False))
