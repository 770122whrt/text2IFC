import hashlib,importlib.util,json,shutil,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/c-shaped-brief-debug-20260910'
SOURCE=OUT.parent/'c-shaped-teaching-building-20260910'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
spec=importlib.util.spec_from_file_location('brief_diagnostic',OUT/'run_brief.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
from tests.agent.test_public_brief_failure_evidence import provider_for
from tests.agent.test_phase6_1_live import _RecordingLiveProvider
for kind in ['truncated','ready']:
    if kind=='truncated':provider=provider_for(kind)[0]
    else:
        fixture=next((SOURCE/'offline-runner').rglob('design-brief.json'))
        provider=_RecordingLiveProvider(read(fixture))
    result=runner.execute(OUT/('offline-'+kind),provider,'synthetic_offline')
    assert result['status']==('exception' if kind=='truncated' else 'ready'),result
validation=OUT/'validation';validation.mkdir(exist_ok=False)
for name in ['brief-evidence-red','brief-evidence-green','brief-evidence-core-final']:
    for ext in ['xml','log']:shutil.copyfile(ROOT/'.tmp'/f'{name}.{ext}',validation/f'{name}.{ext}')
shutil.copyfile(ROOT/'.tmp/brief-fixture-baseline.log',validation/'brief-fixture-baseline.log')
merged={}
for name in ['brief-evidence-green','brief-evidence-core-final']:
    for row in ET.parse(validation/f'{name}.xml').getroot().iter('testcase'):
        merged[(row.attrib['classname'],row.attrib['name'])]=not any(child.tag in ['failure','error','skipped'] for child in row)
assert all(merged.values()),[key for key,value in merged.items() if not value]
parent=read(SOURCE/'admission.json')
drift=[p for p,h in parent['files_sha256'].items() if sha(ROOT/p)!=h]
allowed={'src/text2ifc_agent/live_pipeline.py','tests/agent/test_phase6_1_live.py','docs/architecture/semantic-appearance-plan.md',
         (SOURCE/'README.md').relative_to(ROOT).as_posix()}
assert set(drift)<=allowed,drift
compile_result=subprocess.run([sys.executable,'-m','compileall','-q',str(OUT),str(ROOT/'src/text2ifc_agent/live_pipeline.py'),
    str(ROOT/'tests/agent/test_public_brief_failure_evidence.py')],capture_output=True)
assert compile_result.returncode==0
(validation/'compileall.log').write_bytes(compile_result.stdout+compile_result.stderr)
write(OUT/'authorization.json',dict(status='approved',destination='https://api.deepseek.com',model='deepseek-v4-flash',
    request_sha256=sha(SOURCE/'request.txt'),prior_authorization_sha256=sha(SOURCE/'authorization.json'),
    user_instruction='design brief被截断？ 定位了原因了吗？ 你可以直接进行尝试一阶段看看能不能复现并进行debug。其他看你来说明',
    scope='One additional Design Brief response for the already authorized frozen C input; no Generation/Audit or automatic correction call. Same destination/model/configuration; inherit 1 call,83996 tokens,282.296 seconds.',
    limits=dict(max_calls=32,max_tokens=2000000,max_active_seconds=3600),date='2026-09-10'))
bound={p:sha(ROOT/p) for p in parent['files_sha256']}
bound['tests/agent/test_public_brief_failure_evidence.py']=sha(ROOT/'tests/agent/test_public_brief_failure_evidence.py')
for path in OUT.rglob('*'):
    if path.is_file() and '__pycache__' not in path.parts:bound[path.relative_to(ROOT).as_posix()]=sha(path)
write(OUT/'admission.json',dict(status='admitted',scope='Design Brief exception persistence and immutable attempts; one-stage diagnostic only.',
    parent_admission_sha256=sha(SOURCE/'admission.json'),parent_admission= str((SOURCE/'admission.json').relative_to(ROOT)),
    changed_bindings=drift,dependencies=parent['dependencies'],files_sha256=bound,
    effective_unique_scoped_tests=len(merged),prior_test_failures='3 outdated Phase6.1 fixtures reproduced against unchanged baseline; explicit empty semantic_requirements added; all superseded by current 53-test pass.',
    baseline_red='14 failed,3 passed; 17-case failure family frozen before product edit.',
    public_paths='Existing public stage ready/clarification + caller failure; exact diagnostic runner offline ready/truncated with inherited task budget and identical rendered prompt. Existing complete semantic Generation public paths revalidated.',
    inherited_stage_tests=799,network_transport_attempted=False,full_preflight=False,
    limitations='Preserves exceptions and rejects overwrites. Does not fix or explain Provider truncation. Same revealed case retry, not blind evaluation.'))
print(json.dumps(dict(status='admitted',scoped_tests=len(merged),bound_files=len(bound),offline=['ready','truncated'])))
