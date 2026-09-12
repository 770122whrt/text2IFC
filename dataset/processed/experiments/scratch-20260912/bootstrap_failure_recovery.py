import json
from pathlib import Path
import shutil
import hashlib

base=Path('dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910')
parent=base/'typed-appearance-rerun-20260910'
out=base/'failure-recovery-rerun-20260910'
out.mkdir(exist_ok=False)
(out/'.gitattributes').write_text('* -text\n',encoding='utf-8',newline='\n')
for name in ['run_branches.py','inspect_branch.py']:
    shutil.copyfile(parent/name,out/name)
shutil.copytree(parent/'inputs',out/'inputs')
diagnostics=out/'diagnostics';diagnostics.mkdir()
for name in ['failure-owner-red','failure-owner-green','audit-terminal-red','audit-terminal-green']:
    for suffix in ['xml','log']:
        shutil.copyfile(Path('.tmp')/(name+'-20260910.'+suffix),diagnostics/(name+'.'+suffix))
history=parent/'A-revise/runtime/runs/411166603facdde6/generation-budget.json'
preview={'status':'proposal_only_not_authorization','destination':'https://api.deepseek.com','model':'deepseek-v4-flash',
    'branch':'A-revise','reason':'Continue same approved A task after offline fixes; retain all prior spend.',
    'current_limits':{'max_calls':32,'max_tokens':2000000,'max_active_seconds':3600},
    'proposed_limits':{'max_calls':32,'max_tokens':3000000,'max_active_seconds':3600},
    'prior_calls':22,'prior_tokens_used_or_reserved':1925775,
    'prior_budget_path':history.as_posix(),'prior_budget_sha256':hashlib.sha256(history.read_bytes()).hexdigest(),
    'request':(out/'inputs/A-revise/request.txt').read_text(encoding='utf-8'),
    'conversation':json.loads((out/'inputs/A-revise/conversation.json').read_text(encoding='utf-8')),
    'subsequent_payloads':['own Design Brief','own candidate JSON','own automatic feedback','own runtime metadata'],
    'excluded':['original IFC bytes','private Gold','other task data','credential text'],
    'budget_refund':False,'github_push_authorized':False}
(out/'A-budget-extension-preview.json').write_text(json.dumps(preview,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Prepared fresh B/A inputs and proposed A budget extension; no Provider call or budget change.')
