"""Explicit local API start/status/stop; prepare-only by default, never loads model keys."""
from pathlib import Path
import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import uuid

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
PORT=int(os.environ.get('TEXT2IFC_API_PORT','4180'))
if not 1024<=PORT<=65535:
    raise ValueError('Invalid API port')
RUNTIME=ROOT/'.tmp'/'repair-ui-api'
RECORD=RUNTIME/f'service-{PORT}.json'


def health():
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/api/health',timeout=1) as r:
            return json.load(r)
    except Exception:
        return None


def main(action):
    if sys.version_info<(3,12):
        raise RuntimeError('Python 3.12 or newer is required; set TEXT2IFC_PYTHON to a compatible interpreter.')
    RUNTIME.mkdir(parents=True,exist_ok=True)
    if action=='config-status':
        from text2ifc_web.live_runtime import provider_configuration_status
        print(json.dumps(provider_configuration_status(ROOT),ensure_ascii=False));return
    if action=='start-live':
        # Explicit local operator action; credentials are never printed or sent to the viewer.
        from text2ifc_web.live_runtime import local_live_factory
        approval=RUNTIME/'live-approval.json'
        enabled_env={**os.environ,'TEXT2IFC_UI_LIVE':'1','TEXT2IFC_UI_LIVE_APPROVAL':str(approval)}
        factory,status=local_live_factory(ROOT,enabled_env)
        if factory is None:
            raise RuntimeError('Live mode not started: '+str(status.get('reason'))+'. Configure this workspace locally; do not paste credentials into chat.')
        current=health()
        if current and current.get('execution_enabled'):
            print(json.dumps(current));return
        if current:
            import sqlite3
            database=RUNTIME/'data/web.sqlite'
            if database.exists():
                with sqlite3.connect(database) as db:
                    active=db.execute("SELECT count(*) FROM tasks WHERE busy=1 OR status='clarification_required'").fetchone()[0]
                if active:raise RuntimeError('Finish the active or waiting task before changing runtime mode.')
            main('stop')
            for _ in range(50):
                if health() is None:break
                time.sleep(.1)
            else:raise RuntimeError('Previous API has not stopped; live mode was not started.')
        os.environ['TEXT2IFC_UI_LIVE']='1'
        os.environ['TEXT2IFC_UI_LIVE_APPROVAL']=str(approval)
        return main('start')
    if action=='serve':
        import uvicorn
        from text2ifc_web.app import create_app
        from text2ifc_web.live_runtime import local_live_factory
        factory,status=local_live_factory(ROOT)
        viewer_port=int(os.environ.get('IFC_VIEWER_PORT','4178'))
        if not 1024<=viewer_port<=65535:
            raise ValueError('Invalid viewer port')
        allowed_origins=tuple(f'http://{host}:{port}' for host in ('127.0.0.1','localhost') for port in (viewer_port,PORT))
        app=create_app(RUNTIME/'data',api_factory=factory,examples_root=ROOT/'ui/ifc-viewer/.artifacts/local-examples',allowed_origins=allowed_origins)
        app.state.repair_service.runtime_status=status
        uvicorn.run(app,host='127.0.0.1',port=PORT,log_level='warning',workers=1)
        return
    current=health()
    if action=='status':
        print(json.dumps(current or {'running':False,'port':PORT}));return
    if action=='stop':
        if current is None:
            print('API is not responding.');return
        saved=json.loads(RECORD.read_text()) if RECORD.exists() else None
        if not saved or current.get('service')!='text2IFC-repair-api' or current.get('instance')!=saved.get('instance') or current.get('pid')!=saved.get('pid'):
            raise RuntimeError('This launcher does not own the API listener; refusing to stop it.')
        os.kill(saved['pid'],signal.SIGTERM)
        RECORD.unlink(missing_ok=True)
        print('Stopped this Repair API.');return
    if current:
        if current.get('service')!='text2IFC-repair-api':
            raise RuntimeError('API port belongs to another service.')
        print(json.dumps(current));return
    instance=uuid.uuid4().hex
    env={**os.environ,'TEXT2IFC_API_INSTANCE':instance,'PYTHONIOENCODING':'utf-8'}
    options={'creationflags':subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
    with (RUNTIME/f'service-{PORT}.log').open('ab') as log:
        child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'serve'],cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,**options)
    for _ in range(80):
        ready=health()
        if ready and ready.get('instance')==instance:
            RECORD.write_text(json.dumps({'pid':ready['pid'],'instance':instance}),encoding='utf-8')
            print(json.dumps({**ready,'url':f'http://127.0.0.1:{PORT}/api/docs'}));return
        if child.poll() is not None:
            break
        time.sleep(.15)
    raise RuntimeError('API failed to start; inspect .tmp/repair-ui-api/service-'+str(PORT)+'.log')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['start','stop','status','serve','config-status','start-live'],default='start',nargs='?')
    main(parser.parse_args().action)
