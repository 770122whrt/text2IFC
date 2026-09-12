import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'

def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main():
    stage = sys.argv[1]
    dest = OUT / 'admission' / stage
    dest.mkdir(parents=True, exist_ok=False)
    suites = ['tests/agent', 'tests/compiler', 'tests/contract_v2', 'tests/presentation'] if stage == 'generation' else ['tests/ifc_repair']
    cmd = [sys.executable, '-m', 'pytest', *suites, '-q', '--basetemp', str(ROOT / '.tmp' / ('live-stage-'+stage+'-20260908-01')), '--junitxml', str(dest/'pytest.xml')]
    record = {'stage':stage, 'scope':suites, 'command':cmd, 'started_at':dt.datetime.now(dt.timezone.utc).isoformat(), 'python':sys.version, 'platform':platform.platform(), 'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(), 'network_transport_attempted':False, 'status':'running'}
    write(dest/'execution.json',record)
    with (dest/'pytest.log').open('w',encoding='utf-8') as log:
        try:
            run = subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=1500)
            record.update(exit_code=run.returncode,timeout=False)
        except subprocess.TimeoutExpired:
            record.update(exit_code=None,timeout=True)
    record.update(finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),log_sha256=hashlib.sha256((dest/'pytest.log').read_bytes()).hexdigest(), status='checks_complete')
    write(dest/'execution.json',record)
    print(json.dumps(record,ensure_ascii=False))
    return record['exit_code'] if record['exit_code'] is not None else 124

if __name__ == '__main__':
    raise SystemExit(main())
