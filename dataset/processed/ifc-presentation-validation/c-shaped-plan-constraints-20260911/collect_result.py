"""Collect actual terminal artifacts and usage; no Provider calls or relabeling."""
import hashlib
import json
from pathlib import Path
import shutil

OUT=Path(__file__).resolve().parent
RUN=OUT/'live-run/runs/defec36086974f4b'
SOURCE=OUT.parent/'c-shaped-clarified-entry-20260911'
PRIOR=OUT.parent/'c-shaped-wall-join-20260911/live-run/runs/916d8afe752160e3/generation-budget.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):
    if p.exists():
        assert read(p)==o,p
        return
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2)

execution=read(OUT/'live-run/execution.json')
assert execution['status']=='compiled' and execution['prior_budget_unchanged']
budget=read(RUN/'generation-budget.json');prior=read(PRIOR)
assert budget['attempts'][:11]==prior['attempts'] and len(budget['attempts'])==17
paths=['calls/01-design-brief','generator','repair','evaluation-rounds/round-01/audit','changeset-round-01','audit']
rows=[]
for path,attempt in zip(paths,budget['attempts'][11:]):
    p=RUN/path/'response-metadata.json';m=read(p);u=m['usage']
    assert m['evidence_class']=='live' and u['total_tokens']==attempt['tokens_charged']
    rows.append({'stage':attempt['stage'],'response_id':m['response_id'],'response_model':m['model'],
        'metadata_path':p.relative_to(OUT).as_posix(),'metadata_sha256':sha(p),
        'input':u['prompt_tokens'],'output':u['completion_tokens'],'reasoning_included_in_output':u['completion_tokens_details']['reasoning_tokens'],
        'cache_hit':u.get('prompt_cache_hit_tokens'),'total':u['total_tokens'],'seconds':attempt['elapsed_seconds']})
assert len({r['response_id'] for r in rows})==6
write(OUT/'usage-summary.json',{'new_real_responses':rows,'new_calls':6,'new_tokens':sum(r['total'] for r in rows),
    'cumulative_calls':17,'cumulative_tokens':sum(a['tokens_charged'] for a in budget['attempts']),
    'cumulative_seconds':sum(a['elapsed_seconds'] for a in budget['attempts']),'limits':budget['limits'],
    'ledger_sha256':sha(RUN/'generation-budget.json'),'prior_unchanged':sha(PRIOR)==execution['prior_budget_sha256'],
    'name_repair_related_observed_tokens':sum(r['total'] for r in rows[-2:]),
    'token_savings_measured':False,'note':'Name-repair ChangeSet and final Audit cost is observed overhead, not proven counterfactual savings.'})
for source,name in [(RUN/'output.ifc','generated.ifc'),(SOURCE/'request.txt','request.txt'),(SOURCE/'conversation.json','conversation.json')]:
    if not (OUT/name).exists():shutil.copyfile(source,OUT/name)
    assert sha(source)==sha(OUT/name)
assert read(OUT/'independent-ifc-check.json')['ifc_sha256']==sha(OUT/'generated.ifc')
first=read(RUN/'evaluation-rounds/round-01/candidate.json');final=read(RUN/'candidate.json')
def diffs(a,b,path=''):
    if type(a)!=type(b):return [path]
    if isinstance(a,dict):return [p for k in a.keys()|b.keys() for p in ([path+'/'+k] if k not in a or k not in b else diffs(a[k],b[k],path+'/'+k))]
    if isinstance(a,list):
        if path in ['/entities','/relationships']:
            left={r['id']:r for r in a};right={r['id']:r for r in b}
            assert len(left)==len(a) and len(right)==len(b)
            return diffs(left,right,path)
        return [path] if len(a)!=len(b) else [p for i,(x,y) in enumerate(zip(a,b)) for p in diffs(x,y,path+'/'+str(i))]
    return [] if a==b else [path]
changed=diffs(first,final)
assert len(changed)==3 and all(p.endswith('/attributes/Name') for p in changed),changed
generator=read(RUN/'repair/invalid-candidate.json')
write(OUT/'candidate-diff.json',{'schema_repair_changed_paths':diffs(generator,first),
    'name_changeset_changed_paths':changed,'before_relationship_count':len(first['relationships']),
    'after_relationship_count':len(final['relationships']),'all_relations_equal':not diffs(first['relationships'],final['relationships'],'/relationships'),
    'scope':'Frozen Provider outputs compared without mutation; no new live test of the later name-gate fix.'})
print(json.dumps(read(OUT/'usage-summary.json'),ensure_ascii=False))
