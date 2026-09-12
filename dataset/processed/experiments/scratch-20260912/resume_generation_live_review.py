import contextlib
import datetime as dt
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
GEN=OUT/'generation'
evidence=OUT/'admission/clarify-resume-green.xml'
assert all(all(int(s.get(k,'0'))==0 for k in ['failures','errors','skipped']) for s in ET.parse(evidence).iter('testsuite'))
admission=json.loads((OUT/'admission/generation-final/admission.json').read_text(encoding='utf-8'))
changed=[]
for p,h in admission['files_sha256'].items():
 if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:changed.append(p)
assert changed==['src/text2ifc_agent/interactive_cli_flow.py'],changed
addon={'status':'admitted','scope':'same Generation stage; clarification resume restores persisted calls and transcript; no schema/prompt/compiler changes','base_admission_sha256':hashlib.sha256((OUT/'admission/generation-final/admission.json').read_bytes()).hexdigest(),'revalidation_sha256':hashlib.sha256(evidence.read_bytes()).hexdigest(),'changed_source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in changed},'created_at':dt.datetime.now(dt.timezone.utc).isoformat()}
(GEN/'resume-admission.json').write_text(json.dumps(addon,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
answer='室内净长 6000 毫米沿 X 轴（东西向），净宽 4000 毫米沿 Y 轴（南北向）。其余要求保持原文，包括南门、东双竖面板窗和西单面板窗。'
answerfile=GEN/'clarification-answer-01.txt'
answerfile.write_text(answer+'\n',encoding='utf-8')
record={'status':'running','started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'network_transport_attempted':True,'input_answer_sha256':hashlib.sha256(answerfile.read_bytes()).hexdigest(),'answer_author':'Codex acting as user for the authorized demonstration; axis mapping of its own example','session_hash':'bd9a2fd94c6e4be8'}
def save(): (GEN/'resume-execution-01.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
save()
from scripts.agent.run_phase6_2_cli import main
with (GEN/'resume-cli-01.log').open('x',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
 try:
  code=main(['--live','--stop-after','ifc','--env-file',str(ROOT/'.env'),'--output-root',str(GEN/'runtime'),'--resume','bd9a2fd94c6e4be8','--scripted-stdin',str(answerfile)])
  record.update(status='cli_finished',exit_code=code)
 except Exception as e:record.update(status='exception',exception_type=type(e).__name__)
record['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();save();print(json.dumps(record,ensure_ascii=False))
