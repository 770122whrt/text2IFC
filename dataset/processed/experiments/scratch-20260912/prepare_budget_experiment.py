import hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/c-shaped-brief-budget-experiment-20260910'
SOURCE=OUT.parent/'c-shaped-teaching-building-20260910'
PRIOR=OUT.parent/'c-shaped-brief-debug-20260910'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
from text2ifc_agent.context_selection import select_design_brief_context
from text2ifc_agent.design_brief import load_design_brief_schema,design_brief_template_id
from text2ifc_agent.prompt_registry import render_prompt
request=(SOURCE/'request.txt').read_text(encoding='utf-8')
conversation=read(SOURCE/'live-run/runs/41edcb4296d1b826/calls/01-design-brief/conversation.json')
selection=select_design_brief_context(user_request=request,conversation=conversation,schema_version='bim-json/2.1')
rendered=render_prompt(template_id=design_brief_template_id('text2ifc/design-brief/2.3',design_review_enabled=False),
    inputs=dict(USER_REQUEST=request,CONVERSATION=conversation,DESIGN_BRIEF_SCHEMA=load_design_brief_schema('text2ifc/design-brief/2.3'),EVIDENCE_CATALOG=selection['evidence'],FEW_SHOTS=selection['few_shots']))
(OUT/'frozen-prompt.md').write_text(rendered['text'],encoding='utf-8')
write(OUT/'protocol.json',dict(request_sha256=sha(SOURCE/'request.txt'),prior_budget_sha256=sha(PRIOR/'live-attempt/generation-budget.json'),
    prompt_sha256=sha(OUT/'frozen-prompt.md'),prompt_identity=rendered['metadata'],output_caps_in_order=[98304,65536],
    reason_for_order='Predeclared 96K then64K; one paired exploratory observation, not randomised reliability evaluation.',
    model='deepseek-v4-flash',destination='https://api.deepseek.com',thinking='enabled',
    limits=dict(max_calls=32,max_tokens=2000000,max_active_seconds=3600),max_new_responses=2,
    invariants=['Same request/conversation/schema/prompt/config except max_completion_tokens','One response per arm; no semantic correction,Generation,Audit or IFC',
                'Continue existing2 calls/147630 tokens/447.655 seconds; preserve originals'],
    metrics=['finish_reason','valid/ready','prompt/output/reasoning/total tokens','activity time','material/template/source preservation observations'],
    claims='Exploratory comparison only. A 96K success below64K does not demonstrate benefit; randomness and cache/order are confounds.'))
write(OUT/'authorization.json',dict(status='approved',protocol_sha256=sha(OUT/'protocol.json'),
    prior_authorization_sha256=sha(SOURCE/'authorization.json'),
    user_instruction='然后对于这个进行实验！实验结束后给我一个结论 和节省token的修改建议',
    scope='C Brief64K/96K experiment discussed and authorised; same approved destination/payload, shared original whole-loop budget, no unrelated data.'))
print(json.dumps({'prepared':True,'prompt':rendered['metadata']['template_id'],'arms':[98304,65536]}))
