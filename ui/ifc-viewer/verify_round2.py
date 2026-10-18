"""Actual browser integration review: selected-object X-ray and native offline Repair.
Runs isolated loopback servers, never reads keys, preserves the user's normal services.
"""
from pathlib import Path
import argparse
import base64
import json
import os
import subprocess
import time
import urllib.request
from verify_browser import CDP,winpath


def main(label):
    out=Path('ui/ifc-viewer/.artifacts/api-wiring')/label
    out.mkdir(parents=True,exist_ok=False)
    runtime=Path('.tmp')/('ui-round2-'+label)
    checks=[];children=[];c=None;logs=[]
    def check(name,condition):
        checks.append({'name':name,'passed':bool(condition)})
        if not condition:raise AssertionError(name)
    def launch(args,env=None):
        log=(out/('process-'+str(len(children))+'.log')).open('wb');logs.append(log)
        p=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT);children.append(p);return p
    def wait_js(expr,seconds=150):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if c.js(expr):return
            err=c.js('globalThis.__IFC_ERROR__||null')
            if err:raise RuntimeError(err)
            time.sleep(.2)
        raise AssertionError('Timed out '+expr)
    def button(selector):
        r=c.js('(()=>{const e=document.querySelector('+json.dumps(selector)+');if(!e)throw Error("missing element");e.scrollIntoView({block:"nearest"});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()')
        c.click(**r)
    def shot(name):
        time.sleep(.15)
        image=c.call('Page.captureScreenshot',{'format':'png','fromSurface':True})
        (out/name).write_bytes(base64.b64decode(image['data']))
    def tree_pick(id):
        c.js('(()=>{const i=document.getElementById("treeSearch"),r=__viewer.snapshot().records.find(r=>r.id==='+str(id)+');i.value=r.guid;i.dispatchEvent(new Event("input",{bubbles:true}));})()')
        button('.tree-leaf[data-id="'+str(id)+'"] .tree-select')
    try:
        launch(['python.exe','tests/web/offline_browser_server.py',str(runtime)])
        launch(['node','ui/ifc-viewer/serve.mjs'],env={**os.environ,'IFC_VIEWER_PORT':'4191','TEXT2IFC_API_PORT':'4190'})
        for _ in range(100):
            try:
                json.load(urllib.request.urlopen('http://127.0.0.1:4191/api/health',timeout=1));break
            except Exception:time.sleep(.2)
        launch(['/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','--headless=new','--no-first-run','--disable-extensions','--disable-background-networking','--remote-debugging-port=9358','--remote-allow-origins=*','--use-angle=swiftshader','--enable-unsafe-swiftshader','--user-data-dir='+winpath(out/'profile'),'about:blank'])
        pages=None
        for _ in range(80):
            try:pages=json.load(urllib.request.urlopen('http://127.0.0.1:9358/json',timeout=1));break
            except Exception:time.sleep(.2)
        c=CDP(next(p['webSocketDebuggerUrl'] for p in pages if p['type']=='page'))
        c.call('Page.enable');c.call('Runtime.enable')
        c.call('Emulation.setDeviceMetricsOverride',{'width':1600,'height':1000,'deviceScaleFactor':1,'mobile':False})
        c.navigate('http://127.0.0.1:4191/ifc-viewer/?sample=174&engine=native&view=side')
        check('actual sample retains 250 product meshes and 149378 triangles',c.js('__viewer.report().geometry.renderedProducts===250&&__viewer.report().geometry.triangles===149378'))
        tree_pick(1895)
        check('whole selected IFC identity is retained',c.js('__viewer.state().inspected===1895'))
        shot('highlight-front.png')
        # Move to the opposite side by real orbit pointer dragging, not selecting another wall.
        camera=c.js('__viewer.camera()')
        c.call('Input.dispatchMouseEvent',{'type':'mousePressed','x':720,'y':510,'button':'left','clickCount':1})
        for i in range(1,13):c.call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':720+i*25,'y':510,'button':'left','buttons':1})
        c.call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':1020,'y':510,'button':'left','clickCount':1})
        check('orbit to another side preserves selection',c.js('__viewer.state().inspected===1895') and c.js('__viewer.camera()')!=camera)
        camera=c.js('__viewer.camera()');shot('highlight-back-through.png')
        button('#throughHighlight');shot('highlight-back-normal.png')
        check('through toggle preserves camera and selected identity',c.js('__viewer.camera()')==camera and c.js('__viewer.state().inspected===1895'))
        button('#throughHighlight');button('#reportButton')
        text=c.js('document.getElementById("diagnosticSummary").textContent')
        check('diagnostics retain original material error and correct exclusion categories','1145' in text and 'IfcOpeningElement × 75' in text and 'IfcSpace × 23' in text and 'IfcAnnotation × 3' in text)
        compact=c.js('document.getElementById("stats").textContent')
        check('compact status has one material notice; original 32 errors remain in detail','32' not in compact and '1' in compact and '32' in text and 'Error' in text)
        classification=c.js('__viewer.report().displayClassification')
        check('actual source has seven normal spatial records and five verified part-based assemblies',len(classification['spatial'])==7 and len(classification['aggregates'])==5 and not classification['missing'] and not classification['incompleteAggregates'] and not classification['otherWithoutRepresentation'])
        check('source style audit is shown separately from optional geometry','236/250' in text and '1145' in text)
        check('model tree names the source aggregate rather than a lost mesh','由子构件显示' in c.js("document.querySelector('.tree-leaf[data-id=\"115777\"]').textContent"))
        shot('diagnostics.png');button('#reportButton')
        button('.tree-leaf[data-id="1895"] .tree-visibility')
        check('explicitly hiding the selected object removes its highlight',c.js('__viewer.state().inspected===null&&!__viewer.snapshot().visible.includes(1895)'))
        button('#undoHide');check('undo preserves real IFC product count',c.js('__viewer.snapshot().visible.length===250'))
        # Actual public development input through the file chooser; no private reference.
        public=Path('dataset/processed/ifc-repair/repair-comparison/development/case-001/public')
        doc=c.call('DOM.getDocument')['root']['nodeId']
        file_node=c.call('DOM.querySelector',{'nodeId':doc,'selector':'#file'})['nodeId']
        c.call('DOM.setFileInputFiles',{'nodeId':file_node,'files':[winpath(public/'model.ifc')]})
        wait_js('__IFC_READY__ && document.getElementById("modelName").textContent==="model.ifc"')
        button('#selectMode');button('#request');c.call('Input.insertText',{'text':(public/'request.txt').read_text(encoding='utf-8')})
        button('#submit');wait_js('!!document.getElementById("repairStart")')
        check('offline test execution is explicitly labelled',c.js('document.getElementById("repairPanel").textContent.includes("fixture")'))
        button('#repairStart');wait_js('!!document.getElementById("repairAnswer")',180)
        taskid=c.js('new URL(location.href).searchParams.get("task")')
        state=c.js('fetch("/api/repair-tasks/'+taskid+'").then(r=>r.json())')
        check('native task is genuinely waiting for clarification',state['status']=='clarification_required')
        before_runs=len(list((runtime/'native/runs').glob('*/state.json')))
        shot('clarification.png')
        c.call('Page.reload',{'ignoreCache':True});wait_js('!!document.getElementById("repairAnswer")',90)
        check('refresh restores the same question without starting a new native run',c.js('new URL(location.href).searchParams.get("task")')==taskid and len(list((runtime/'native/runs').glob('*/state.json')))==before_runs)
        button('#repairAnswer');c.call('Input.insertText',{'text':'宽915毫米。'})
        button('#langEn');check('locale switch keeps unsent clarification answer',c.js('document.getElementById("repairAnswer").value')=='宽915毫米。');button('#langZh')
        button('#repairSendAnswer');wait_js('document.body.dataset.repairResultReady==="success"',180)
        final=c.js('fetch("/api/repair-tasks/'+taskid+'").then(r=>r.json())')
        check('HTTP answer produces a natively published IFC',final['status']=='succeeded' and final['successful_artifact_publishable'])
        check('real output is loaded into the viewer',c.js('document.getElementById("modelName").textContent==="repaired.ifc"'))
        summary=c.js('fetch("/api/repair-tasks/'+taskid+'/summary").then(r=>r.json())')
        check('per-operation summary comes from native output and publication',summary['available'] and summary['operation_total']==1 and summary['published_operations']==1 and len(summary['rows'][0]['created'])==1)
        check('each resulting object has an individual locate action',c.js('document.querySelectorAll("#operationResults [data-result-guid]").length>=2'))
        count_after=c.js('__viewer.snapshot().records.filter(r=>r.type==="IfcWindow").length')
        camera=c.js('__viewer.camera()');base=c.js('__viewer.state().baseVersion');frame=c.js('__viewer.frame()');shot('result-after.png')
        check('output UI no longer claims that no repaired file exists','只有当前源文件' not in c.js('document.getElementById("resultHint").textContent'))
        button('#viewBefore');count_before=c.js('__viewer.snapshot().records.filter(r=>r.type==="IfcWindow").length');shot('result-before.png')
        check('exactly one window added in actual output IFC',count_after==count_before+1)
        check('before view preserves camera and next request base',c.js('__viewer.camera()')==camera and c.js('__viewer.state().baseVersion')==base)
        check('actual before and after geometry share the original display offset',c.js('__viewer.frame().displayOffset')==frame['displayOffset']==frame['comparisonOffset'] and c.js('__viewer.frame().engine')==frame['engine'])
        button('#viewAfter');check('after view preserves camera and next request base',c.js('__viewer.camera()')==camera and c.js('__viewer.state().baseVersion')==base)
        check('original request and answer history remain readable',(public/'request.txt').read_text(encoding='utf-8') in c.js('document.getElementById("messages").textContent') and '宽915毫米' in c.js('document.getElementById("repairPanel").textContent'))
        events=c.js('fetch("/api/repair-tasks/'+taskid+'/events").then(r=>r.json())')
        check('real application and evaluation events are present',all(any(e['stage']==s and e['action']=='completed' for e in events['activity']) for s in ['application','evaluation']))
        button('#locateChange');check('new object can be located without changing request reference',c.js('__viewer.snapshot().records.find(r=>r.id===__viewer.state().inspected).type==="IfcWindow"'));shot('new-window.png')
        c.call('Page.reload',{'ignoreCache':True});wait_js('document.body.dataset.repairResultReady==="success"',90)
        check('finished task refresh restores output with no new run',len(list((runtime/'native/runs').glob('*/state.json')))==before_runs)
        files=c.js('fetch("/api/repair-tasks/'+taskid+'/artifacts").then(r=>r.json())')['artifacts']
        check('actual attempt diagnostics and raw responses are exposed',any(f['name']=='raw-response.txt' for f in files) and any(f['role']=='selection_check' for f in files))
        for width,height in [(1366,768),(1024,900)]:
            c.call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False});time.sleep(.2)
            check('no horizontal overflow '+str(width),c.js('document.documentElement.scrollWidth<=innerWidth+1'))
        result={'passed':sum(x['passed'] for x in checks),'checks':checks,'live_provider_calls':0,'provider':'offline fixture only','native_apply_and_evaluation':True,'browser':'Windows Edge / SwiftShader WebGL2','task_id':taskid,'runtime':str(runtime)}
        (out/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception as error:
        if c:
            try:shot('failure.png')
            except Exception:pass
        (out/'checks.json').write_text(json.dumps({'checks':checks,'error':str(error)},ensure_ascii=False,indent=2),encoding='utf-8')
        raise
    finally:
        if c:
            try:c.call('Browser.close')
            except Exception:pass
        for p in reversed(children):
            if p.poll() is None:p.terminate()
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.kill()
        for log in logs:log.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);main(parser.parse_args().label)
