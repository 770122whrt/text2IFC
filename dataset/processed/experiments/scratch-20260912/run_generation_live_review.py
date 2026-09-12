import contextlib
import datetime as dt
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
admission=json.loads((OUT/'admission/generation-final/admission.json').read_text(encoding='utf-8'))
assert admission['status']=='admitted'
for path,expected in admission['files_sha256'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
gen=OUT/'generation'
assert hashlib.sha256((gen/'frozen-expectations.json').read_bytes()).hexdigest()==admission['case_expectations']['sha256']
assert not (gen/'runtime').exists()
from scripts.agent.run_phase6_2_cli import main
record={'stage':'generation','provider_execution':'real','started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'network_transport_attempted':True,'status':'running','admission_sha256':hashlib.sha256((OUT/'admission/generation-final/admission.json').read_bytes()).hexdigest(),'request_sha256':hashlib.sha256((gen/'request.txt').read_bytes()).hexdigest()}
def save(): (gen/'execution.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
save()
with (gen/'cli.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
    try:
        code=main(['--live','--stop-after','ifc','--env-file',str(ROOT/'.env'),'--output-root',str(gen/'runtime'),'--prompt',(gen/'request.txt').read_text(encoding='utf-8').strip()],stdin=io.StringIO(''))
        record.update(exit_code=code,status='cli_finished')
    except Exception as error:
        record.update(exit_code=1,status='exception',exception_type=type(error).__name__)
record['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat()
save()
print(json.dumps(record,ensure_ascii=False))
