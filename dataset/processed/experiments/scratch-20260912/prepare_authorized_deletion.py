import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'docs/reports/run-cleanup-review-20260910'
proposal=out/'deletion-proposal.json'
approval=dict(status='approved',date='2026-09-10',question_id='call_7dGHwb687ttmfrweJIqlN3xd:0',
    user_answer='批准按清单删除',proposal_sha256=hashlib.sha256(proposal.read_bytes()).hexdigest(),
    scope='Exactly the12 listed directories after experiment completion and hash recheck; preserve all Proof, C inputs/failures/latest budgets,current experiment, A/B scripts and earlier failed attempts.')
(out/'authorization.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
data=json.loads(proposal.read_text(encoding='utf-8'));mappings=[]
for row in data['targets']:
    if row['target'].startswith('.tmp/'):
        mappings.append(dict(old_root=row['target'],disposition='synthetic_test_output_removed_after_approval',
            retained='Frozen red/green XML,logs,test sources in C diagnostic/evaluation evidence; individual test fixture outputs reproducible.'))
    else:
        mappings.append(dict(old_root=row['target'],disposition='source_duplicate_retired',files=[dict(
            old_path=row['target']+'/'+f['path'],new_path=f['proof_copies'][0],sha256=f['sha256']) for f in row['files']]))
(out/'retired-paths.json').write_text(json.dumps(dict(status='approved_pending_execution',mappings=mappings),ensure_ascii=False,indent=2),encoding='utf-8')
print('Approval and exact retained evidence mapping recorded; no deletion.')
