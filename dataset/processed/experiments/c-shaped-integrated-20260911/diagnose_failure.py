"""Offline replay of the genuine malformed Brief; never repairs its JSON."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(ROOT/'src'))
from text2ifc_agent.live_pipeline import run_design_brief_stage
from text2ifc_agent.openai_compat import OpenAICompatibleLiveProvider, load_openai_compatible_runtime_config

source = OUT/'live-run/runs/cf0a6e858a2a74a8/calls/01-design-brief'
raw = json.loads((source/'response.raw.json').read_text(encoding='utf-8'))
text = (source/'model-text.txt').read_text(encoding='utf-8')
before = hashlib.sha256((source/'response.raw.json').read_bytes()).hexdigest()
try:
    json.loads(text)
    raise AssertionError('Expected malformed JSON')
except json.JSONDecodeError as error:
    syntax = {'message':error.msg, 'line':error.lineno, 'column':error.colno,
              'offset':error.pos, 'context':text[error.pos-100:error.pos+100]}
calls = []
def create(**kwargs):
    calls.append(True)
    return raw
client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
config = load_openai_compatible_runtime_config({'TEXT2IFC_PROVIDER':'deepseek',
    'API_KEY':'fixture-secret-key', 'OPENAI_BASE_URL':'https://example.invalid',
    'TEXT2IFC_DEEPSEEK_MODEL':'fixture','TEXT2IFC_DEEPSEEK_MAX_INPUT_TOKENS':'131072'})
adapter = OpenAICompatibleLiveProvider(config=config,client_factory=lambda **_:client,connection_max_attempts=1)
class Replay:
    def generate_live(self, **kwargs):
        return replace(adapter.generate_live(**kwargs), evidence_class='frozen_replay')
target = ROOT/'.tmp/c-integrated-malformed-replay'
result = run_design_brief_stage(provider=Replay(), output_dir=target,
    design_brief_schema_version='text2ifc/design-brief/2.3',
    case={'case_id':'c-malformed-replay','user_request':(source/'input.txt').read_text(encoding='utf-8'),
          'conversation':json.loads((source/'conversation.json').read_text(encoding='utf-8')),'call_index':1})
assert result['status']=='blocked_prompt_defect' and not result['valid'] and len(calls)==1
assert not (target/'design-brief.json').exists()
assert hashlib.sha256((source/'response.raw.json').read_bytes()).hexdigest()==before
record={'evidence_class':'frozen_replay','network_calls':0,'fake_adapter_calls':len(calls),
        'syntax_error':syntax,'result':result,'source_sha256':before,'source_unchanged':True,
        'diagnosis':'Provider returned syntactically invalid nested JSON despite stop. Strict parsing correctly blocked it. Existing semantic repair requires parse_status=ok and cannot process this response. No byte repair or publication.',
        'rule_observation':'No STAIR_OPENING_SPACE_COLLISION string in this invalid response; not proof of a valid corrected Brief.',
        'design_question':'Independently confirmed original entry door Y=7800..9000 lies opposite stair plan Y=5400..10800; horizontal gap from inner west wall X=200 to stair X=400 is 200 mm. Potential access issue, not a completed clearance/code analysis.'}
with (OUT/'failure-diagnosis.json').open('x',encoding='utf-8') as f:
    json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps({'network_calls':0,'replay_status':result['status'],'source_unchanged':True}))
