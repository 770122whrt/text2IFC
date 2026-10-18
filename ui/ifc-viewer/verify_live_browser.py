"""Operator-driven browser UAT against the actual local Repair API.

Only explicit submit/answer commands mutate a task. status/verify never start a run.
Uses an isolated Edge profile; does not read model credentials or archived outputs to
produce model responses. All Provider calls take place in the normal backend service.
"""
from pathlib import Path
import argparse
import base64
from datetime import datetime, timezone
import json
import subprocess
import time
import urllib.request
from verify_browser import CDP, winpath

ROOT=Path.cwd()
BASE='http://127.0.0.1:4178'
OUT=ROOT/'ui/ifc-viewer/.artifacts/live-ui-20261011'
PORT=9364

def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def get(path):
    if not path.startswith('/') or path.startswith('//') or '..' in path:raise ValueError('Not a local API path')
    if not path.startswith('/api/'):path='/api'+path
    with urllib.request.urlopen(BASE+path,timeout=10) as response:return json.load(response)

def connect(start=False):
    url=f'http://127.0.0.1:{PORT}/json'
    try:
        with urllib.request.urlopen(url,timeout=2) as response:pages=json.load(response)
    except Exception:
        if not start:raise RuntimeError('Isolated browser not running; use submit or restore')
        OUT.mkdir(parents=True,exist_ok=True)
        with (OUT/'edge.log').open('ab') as log:
            p=subprocess.Popen(['/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
                '--headless=new','--no-first-run','--disable-extensions','--disable-background-networking',
                f'--remote-debugging-port={PORT}','--remote-allow-origins=*','--use-angle=swiftshader',
                '--enable-unsafe-swiftshader','--user-data-dir='+winpath(OUT/'isolated-profile'),'about:blank'],
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        put(OUT/'browser.json',{'pid':p.pid,'port':PORT,'profile':'isolated-profile'})
        for _ in range(80):
            try:
                with urllib.request.urlopen(url,timeout=1) as response:pages=json.load(response)
                break
            except Exception:time.sleep(.2)
        else:raise RuntimeError('Isolated browser initialization timed out')
    candidates=[p for p in pages if p['type']=='page' and p.get('url','').startswith(BASE+'/ifc-viewer/')]
    if not candidates:candidates=[p for p in pages if p['type']=='page' and p.get('url')=='about:blank']
    if not candidates:raise RuntimeError('Expected isolated viewer target is unavailable; refusing unrelated browser tabs')
    c=CDP(candidates[0]['webSocketDebuggerUrl'])
    c.call('Page.enable');c.call('Runtime.enable')
    c.call('Emulation.setDeviceMetricsOverride',{'width':1600,'height':1000,'deviceScaleFactor':1,'mobile':False})
    return c

def wait(c,expr,seconds=90):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if c.js(expr):return
        time.sleep(.25)
    raise RuntimeError('Browser condition timed out: '+expr)

def click(c,selector):
    point=c.js('(()=>{const e=document.querySelector('+json.dumps(selector)+');if(!e||e.disabled)throw Error("button missing or disabled");e.scrollIntoView({block:"nearest"});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()')
    c.click(**point)

def shot(c,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(base64.b64decode(c.call('Page.captureScreenshot',{'format':'png','fromSurface':True})['data']))

def main(args):
    folder=OUT/args.label;record_path=folder/'task.json'
    if args.action=='close':
        c=connect();c.call('Browser.close')
        # Remove this script's disposable browser profile, never the user's normal profile.
        import shutil
        for _ in range(25):
            try:
                profile=OUT/'isolated-profile'
                if profile.exists() and not profile.is_symlink():shutil.rmtree(profile)
                break
            except OSError:time.sleep(.2)
        # One early capture targeted an unrelated internal browser page; it is not UAT evidence.
        (OUT/'door-1/current.png').unlink(missing_ok=True)
        print('Isolated UAT browser closed; disposable profile cleanup attempted; normal services and IFC evidence retained.');return
    if args.action=='submit':
        if record_path.exists():raise RuntimeError('Task already registered; use status/restore, never duplicate submit')
        folder.mkdir(parents=True,exist_ok=True)
        caps=get('/capabilities')
        if not caps['execution_enabled'] or caps.get('runtime',{}).get('mode')!='live':raise RuntimeError('Real local API is not enabled')
        c=connect(start=True)
        c.navigate(BASE+'/ifc-viewer/?sample=174&engine=native&view=side')
        ident='case-002' if args.case=='door' else 'case-001'
        if args.source_file:
            source_path=Path(args.source_file).resolve()
            if not source_path.is_relative_to(ROOT) or not source_path.is_file():raise ValueError('Invalid local UAT input')
            doc=c.call('DOM.getDocument')['root']['nodeId']
            node=c.call('DOM.querySelector',{'nodeId':doc,'selector':'#file'})['nodeId']
            c.call('DOM.setFileInputFiles',{'nodeId':node,'files':[winpath(source_path)]})
            wait(c,'globalThis.__IFC_READY__ && document.getElementById("modelName").textContent==='+json.dumps(source_path.name))
            click(c,'#selectMode')
        else:
            click(c,'#examplesButton');wait(c,'document.getElementById("examplesDialog").open')
            click(c,'[data-example-id="'+ident+'"][data-example-mode="input"]')
            wait(c,'globalThis.__IFC_READY__ && document.getElementById("modelName").textContent==='+json.dumps(ident+'-input.ifc'))
        if args.case=='multi':
            targets=c.js('__viewer.snapshot().records.filter(r=>(r.name||"").startsWith("UI batch wall ")).sort((a,b)=>a.name.localeCompare(b.name))')
            if len(targets)!=2:raise RuntimeError('Expected the two explicit public-source UAT walls')
            reference=c.js('__viewer.snapshot().records.find(r=>r.type==="IfcWindow"&&(r.name||"").includes("0915")&&(r.name||"").includes("1830"))')
            if not reference:raise RuntimeError('No dimension-compatible public reference window')
            def select_record(rec):
                c.js('(()=>{const e=document.getElementById("treeSearch");e.value='+json.dumps(rec['guid'])+';e.dispatchEvent(new Event("input",{bubbles:true}))})()')
                click(c,'.tree-leaf[data-id="'+str(rec['id'])+'"] .tree-select')
            click(c,'#multiSelect')
            for rec in targets:select_record(rec)
            click(c,'#addAux');select_record(reference)
            put(folder/'selected-objects.json',{'targets':targets,'reference':reference,'fixture':'two test walls in an existing public model, not pristine Gold'})
        if args.request_file:
            path=Path(args.request_file).resolve()
            if not path.is_relative_to(ROOT):raise ValueError('Request file outside workspace')
            text=path.read_text(encoding='utf-8')
            c.js('(()=>{const e=document.getElementById("request");e.value='+json.dumps(text)+';e.dispatchEvent(new Event("input",{bubbles:true}))})()')
        baseline=c.js('({camera:__viewer.camera(),frame:__viewer.frame(),records:__viewer.snapshot().records,request:__viewer.state().draft})')
        put(folder/'input-view.json',baseline)
        shot(c,folder/'input.png')
        click(c,'#submit');wait(c,'!!document.getElementById("repairStart")&&!document.getElementById("repairStart").disabled')
        shot(c,folder/'prepared.png')
        put(folder/'start-attempt.json',{'created_at':datetime.now(timezone.utc).isoformat(),'case':args.case,'through':'actual viewer buttons','live':True})
        click(c,'#repairStart')
        wait(c,'!!new URL(location.href).searchParams.get("task")')
        task_id=c.js('new URL(location.href).searchParams.get("task")')
        put(record_path,{'task_id':task_id,'case':args.case,'input_case':ident,'source_file':str(Path(args.source_file).relative_to(ROOT)) if args.source_file and Path(args.source_file).is_absolute() else args.source_file,'expected_added':2 if args.case=='multi' else 1,'created_at':datetime.now(timezone.utc).isoformat(),'live_provider_requested':True})
        task=get('/repair-tasks/'+task_id);put(folder/'last-task.json',task)
        shot(c,folder/'submitted.png')
        print(json.dumps({'task_id':task_id,'status':task['status'],'native_stage':task['native_stage'],'browser_url':BASE+'/ifc-viewer/?task='+task_id},ensure_ascii=False));return
    record=json.loads(record_path.read_text(encoding='utf-8'));task_id=record['task_id'];task=get('/repair-tasks/'+task_id)
    if args.action=='status':
        end=time.monotonic()+args.wait_seconds
        while task['busy'] and time.monotonic()<end:
            time.sleep(min(3,max(.1,end-time.monotonic())))
            task=get('/repair-tasks/'+task_id)
        events=get('/repair-tasks/'+task_id+'/events');put(folder/'last-task.json',task);put(folder/'events.json',events)
        try:shot(connect(),folder/('waiting.png' if task['clarification'] else 'current.png'))
        except Exception:pass
        print(json.dumps({'task_id':task_id,'status':task['status'],'busy':task['busy'],'native_stage':task['native_stage'],'reason':task.get('reason_code') or task.get('error_code'),'clarification':task['clarification'],'last_activity':events.get('activity',[])[-3:]},ensure_ascii=False,indent=2));return
    c=connect(start=True)
    if args.action=='restore':
        c.call('Page.navigate',{'url':BASE+'/ifc-viewer/?task='+task_id})
        wait(c,'globalThis.__IFC_READY__')
        shot(c,folder/'restored.png');print(json.dumps({'restored_task':task_id,'new_start':False}));return
    if args.action=='answer':
        if task['status']!='clarification_required':raise RuntimeError('Task is not awaiting clarification')
        if not args.answer:raise ValueError('Provide the explicit UAT answer')
        wait(c,'!!document.getElementById("repairAnswer")')
        click(c,'#repairAnswer');c.call('Input.insertText',{'text':args.answer})
        shot(c,folder/'answer-ready.png');click(c,'#repairSendAnswer');time.sleep(.5)
        result=get('/repair-tasks/'+task_id)
        print(json.dumps({'task_id':task_id,'status':result['status'],'answered_question':task['clarification']['clarification_id']},ensure_ascii=False));return
    if args.action=='verify':
        if task['status']!='succeeded' or not task['successful_artifact_publishable']:raise RuntimeError('Task has no published successful IFC')
        wait(c,'document.body.dataset.repairResultReady==="success"',120)
        files=get('/repair-tasks/'+task_id+'/artifacts')['artifacts'];put(folder/'artifact-index.json',files)
        prepared=get('/repair-requests/'+task['prepared_request_id']);put(folder/'prepared-request.json',prepared)
        source=get('/ifc-inputs/'+prepared['input_id'])
        with urllib.request.urlopen(BASE+source['download_url'],timeout=60) as r:(folder/'input.ifc').write_bytes(r.read())
        output=next(f for f in files if f['role']=='successful_ifc')
        with urllib.request.urlopen(BASE+output['download_url'],timeout=60) as r:(folder/'repaired.ifc').write_bytes(r.read())
        evaluation=next(f for f in files if f['name']=='public-evaluation.json')
        put(folder/'evaluation.json',get(evaluation['download_url']))
        put(folder/'summary.json',get('/repair-tasks/'+task_id+'/summary'))
        checks=[]
        def check(name,value):
            checks.append({'name':name,'passed':bool(value)})
            if not value:raise AssertionError(name)
        camera=c.js('__viewer.camera()');frame=c.js('__viewer.frame()');after=c.js('__viewer.snapshot()')
        shot(c,folder/'after.png');click(c,'#viewBefore');before=c.js('__viewer.snapshot()');shot(c,folder/'before.png')
        check('same camera after-to-before',camera==c.js('__viewer.camera()'))
        check('same geometry origin',frame['displayOffset']==c.js('__viewer.frame().displayOffset'))
        check('view toggle does not change next input',frame['baseVersion']==c.js('__viewer.frame().baseVersion'))
        kind='IfcDoor' if record['case']=='door' else 'IfcWindow'
        expected=record.get('expected_added',1)
        check('actual browser IFC has the requested added target count',sum(r['type']==kind for r in after['records'])==sum(r['type']==kind for r in before['records'])+expected)
        click(c,'#viewAfter');check('same camera before-to-after',camera==c.js('__viewer.camera()'))
        click(c,'#locateChange');check('new object actually locates',c.js('__viewer.snapshot().records.find(r=>r.id===__viewer.state().inspected).type')==kind)
        shot(c,folder/'change-after.png');camera=c.js('__viewer.camera()');click(c,'#viewBefore');shot(c,folder/'change-before.png');check('focused before/after camera stable',camera==c.js('__viewer.camera()'));click(c,'#viewAfter')
        put(folder/'browser-checks.json',{'checks':checks,'passed':len(checks),'evidence_class':'live','task_id':task_id,'provider_results':'new real backend calls, no fixture or response replay'})
        print(json.dumps({'task_id':task_id,'checks_passed':len(checks),'artifacts':folder.relative_to(ROOT).as_posix(),'output_bytes':(folder/'repaired.ifc').stat().st_size},ensure_ascii=False));return

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['submit','status','restore','answer','verify','close']);parser.add_argument('--label',default='door-1');parser.add_argument('--case',choices=['door','window','multi'],default='door');parser.add_argument('--source-file');parser.add_argument('--request-file');parser.add_argument('--answer');parser.add_argument('--wait-seconds',type=int,default=0);args=parser.parse_args()
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.label):parser.error('Invalid label')
    main(args)
