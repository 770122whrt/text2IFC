"""One authorized real Generation run after current admission; raw attempts preserved."""
import contextlib
import datetime as dt
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909'

def main():
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    admission=json.loads((OUT/'admission/admission.json').read_text(encoding='utf-8'))
    assert admission['status']=='admitted', 'Current Generation admission is required'
    for p,h in admission['files_sha256'].items():
        assert sha(ROOT/p)==h, f'Stale admission: {p}'
    expected=json.loads((OUT/'frozen-expectations.json').read_text(encoding='utf-8'))
    assert sha(OUT/'request.txt')==expected['request_sha256']
    from scripts.agent.run_phase6_2_cli import main as cli, load_env_file
    from text2ifc_agent.openai_compat import load_openai_compatible_config
    import os
    load_env_file(ROOT/'.env')
    config=load_openai_compatible_config(dict(os.environ))
    assert config['configured'], 'Provider is not configured'
    if '--check-only' in sys.argv:
        print(json.dumps(config,ensure_ascii=False))
        return
    runtime=OUT/'runtime'
    assert not runtime.exists(), 'New run cannot overwrite prior attempts'
    execution={'status':'running','started_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'provider':'DeepSeek api.deepseek.com','strategy':'legacy_full','network_transport_attempted':True,
        'admission_sha256':sha(OUT/'admission/admission.json'),'request_sha256':expected['request_sha256'],
        'scope':'Public CLI Brief -> Generation -> bounded correction -> Audit -> IFC. No Repair source/private Gold inputs.',
        'claim':'same frozen development request reattempt, not blind improvement evidence'}
    def save():
        (OUT/'execution.json').write_text(json.dumps(execution,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save()
    with (OUT/'cli.log').open('x',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        try:
            code=cli(['--live','--stop-after','ifc','--env-file',str(ROOT/'.env'),
                '--output-root',str(runtime),'--prompt',(OUT/'request.txt').read_text(encoding='utf-8').rstrip('\r\n')],
                stdin=io.StringIO(''))
            execution.update(status='finished',exit_code=code)
        except Exception as error:
            execution.update(status='exception',exception_type=type(error).__name__)
            # Detailed exception may include endpoint or transport details; keep local.
            import traceback
            traceback.print_exc()
    execution['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat()
    save()
    print(json.dumps(execution,ensure_ascii=False))

if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
