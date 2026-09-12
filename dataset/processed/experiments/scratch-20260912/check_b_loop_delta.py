import json
from pathlib import Path

folder=Path(__file__).resolve().parents[1]/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/B-retain'
run=folder/'runtime/runs/8b3add702299a50f'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
before=read(run/'evaluation-rounds/round-01/candidate.json')
after=read(run/'evaluation-rounds/round-02/candidate.json')
for document in (before, after):
    for section in ('entities','relationships'):
        items=document[section]
        assert len({item['id'] for item in items})==len(items)
        document[section]={item['id']:item for item in items}
changes=[]
def diff(a,b,path=''):
    if type(a)!=type(b):
        changes.append(dict(path=path,before=a,after=b))
    elif isinstance(a,dict):
        for key in sorted(set(a)|set(b)):
            if key not in a or key not in b:
                changes.append(dict(path=path+'/'+key,before=a.get(key),after=b.get(key)))
            else: diff(a[key],b[key],path+'/'+key)
    elif isinstance(a,list):
        assert len(a)==len(b), path
        for i,(x,y) in enumerate(zip(a,b)): diff(x,y,path+'/'+str(i))
    elif a!=b:
        changes.append(dict(path=path,before=a,after=b))
diff(before,after)
assert len(changes)==2, {'change_count':len(changes),'first_changes':changes[:4]}
assert all(c['path'].endswith('/attributes/ObjectPlacement/origin/2') and c['before']==-150 and c['after']==0 for c in changes), changes
result=dict(status='passed', changes=changes, unchanged='All other candidate values, stable IDs, geometry, material and appearance data are identical.', basis='Structural comparison of both frozen evaluation-round candidates, entities/relationships keyed by unique stable ID; serialization order is irrelevant.', inspection_note='Initial positional comparison rejected because ChangeSet canonicalizes entity/relationship order; no product change or Provider retry.')
with (folder/'independent-loop-delta.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False))
