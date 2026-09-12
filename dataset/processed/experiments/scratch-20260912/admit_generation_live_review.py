import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
DEST=OUT/'admission/generation-final'
DEST.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
tests=['tests/agent/test_design_brief_attempt_preservation.py','tests/agent/test_interactive_cli_flow.py','tests/agent/test_interactive_cli_generation.py','tests/agent/test_interactive_cli_session.py','tests/agent/test_phase6_2_fix_repl_cli.py','tests/agent/test_phase6_2_openai_compat.py','tests/agent/test_semantic_public_paths.py','tests/agent/test_generation_semantic_closure.py','tests/agent/test_generation_semantic_versions.py','tests/agent/test_live_clarification.py','tests/agent/test_prompt_registry.py']
commands=[[sys.executable,'-m','pytest',*tests,'-q','--basetemp',str(ROOT/'.tmp/live-generation-final-20260908-01'),'--junitxml',str(DEST/'pytest.xml')],[sys.executable,'-m','compileall','-q','src','tests','scripts'],['git','diff','--check']]
checks=[]
for i,cmd in enumerate(commands):
    start=dt.datetime.now(dt.timezone.utc).isoformat()
    with (DEST/f'check-{i}.log').open('w',encoding='utf-8') as f:
        r=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=600)
    checks.append({'command':cmd,'started_at':start,'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),'exit_code':r.returncode,'timeout':False,'log':f'check-{i}.log','sha256':sha(DEST/f'check-{i}.log')})
    write(DEST/'checks.json',checks)
    if r.returncode:raise SystemExit(r.returncode)
suites=list(ET.parse(DEST/'pytest.xml').iter('testsuite'))
assert all(all(int(s.get(k,'0'))==0 for k in ['failures','errors','skipped']) for s in suites)
original=ET.parse(OUT/'admission/generation/pytest.xml')
failures=[t.get('classname')+'.'+t.get('name') for t in original.iter('testcase') if t.find('failure') is not None]
assert failures==['tests.agent.test_phase6_2_fix_repl_cli.test_default_live_repl_design_brief_trace_is_session_scoped']
files=[p for folder in ['src/text2ifc_agent','src/text2ifc_compiler','src/text2ifc_contract','src/text2ifc_presentation','schemas','prompts'] for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in ['.py','.json','.md']]
write(DEST/'admission.json',{'status':'admitted','stage':'generation-semantic-appearance-public-cli','strategy':'legacy_full','created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'python':sys.version,'platform':platform.platform(),'network_transport_attempted':False,'checks':checks,'current_focused_tests':sum(int(s.get('tests')) for s in suites),'baseline_regression':{'path':'../generation/pytest.xml','sha256':sha(OUT/'admission/generation/pytest.xml'),'passed':807,'failed':failures,'resolution':'new Brief2.1/Formal2.1 replay fixture covered by current focused successful test'},'seams':{'input_and_brief':'test_design_brief.py; test_generation_semantic_versions.py','transport_and_failure_retention':'test_phase6_2_openai_compat.py; test_design_brief_attempt_preservation.py','clarification_and_persistence':'test_live_clarification.py; test_interactive_cli_session.py','public_cli_reopen_and_terminal':'test_interactive_cli_generation.py; test_phase6_2_fix_repl_cli.py; test_semantic_public_paths.py','compile_atomic_rollback_and_semantics':'tests/compiler; test_generation_semantic_closure.py','staged_and_multistorey_scale':'test_phase6_5_staged_generation.py; test_phase6_5_multistorey_matrix.py','repair_source_and_gold':'not applicable: this admission covers text-only Generation, no source IFC or benchmark Gold'},'case_expectations':{'path':'../../generation/frozen-expectations.json','sha256':sha(OUT/'generation/frozen-expectations.json')},'invalidating_boundaries':['public API/CLI behavior','schema/prompt/profile versions','provider transport','compiler/transaction/semantics/evaluator','case request changes'],'files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files},'claim':'single live viability run only; human review pending; no capability improvement or accepted Proof'})
print('Generation admission complete.')
