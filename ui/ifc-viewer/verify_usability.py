"""Focused real-browser checks for fit, failed file selection, drafts and display switches."""
from pathlib import Path
import argparse, base64, importlib.util, json, math, subprocess, time, urllib.request
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('qa',HERE/'verify_browser.py');qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)

def direction(camera):
    v=[a-b for a,b in zip(camera['position'],camera['target'])];n=math.sqrt(sum(x*x for x in v));return [x/n for x in v]

def main(label):
    out=HERE/'.artifacts/dataset-ifc2x3'/label;out.mkdir(parents=True,exist_ok=False)
    args=['/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','--headless=new','--no-first-run','--disable-extensions','--disable-background-networking','--remote-debugging-port=9344','--remote-allow-origins=*','--use-angle=swiftshader','--enable-unsafe-swiftshader','--user-data-dir='+qa.winpath(out/'profile'),'about:blank']
    log=(out/'edge.log').open('wb');p=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT);client=None;checks=[]
    def check(name,value):checks.append({'name':name,'passed':bool(value)})
    try:
        pages=None
        for _ in range(60):
            try:pages=json.load(urllib.request.urlopen('http://127.0.0.1:9344/json',timeout=1));break
            except Exception:time.sleep(.2)
        if not pages:raise RuntimeError('Browser unavailable')
        client=qa.CDP(next(x['webSocketDebuggerUrl'] for x in pages if x['type']=='page'));client.call('Page.enable');client.call('Runtime.enable')
        client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':960,'deviceScaleFactor':1,'mobile':False})
        client.navigate('http://127.0.0.1:4178/ifc-viewer/?sample=174&engine=native&view=front')
        before=direction(client.js('__viewer.camera()'));client.button('fit')
        check('fit preserves viewing direction',max(abs(a-b) for a,b in zip(before,direction(client.js('__viewer.camera()'))))<1e-8)
        client.button('selectMode');client.button('request');client.call('Input.insertText',{'text':'Keep this draft when loading fails.'})
        old=client.js('({state:__viewer.state(),camera:__viewer.camera(),source:__viewer.report().source,visible:__viewer.snapshot().visible})')
        bad=out/'invalid.ifc';bad.write_text('not an IFC file',encoding='utf8')
        doc=client.call('DOM.getDocument')['root']['nodeId'];node=client.call('DOM.querySelector',{'nodeId':doc,'selector':'#file'})['nodeId']
        client.call('DOM.setFileInputFiles',{'nodeId':node,'files':[qa.winpath(bad)]});time.sleep(2)
        current=client.js('({state:__viewer.state(),camera:__viewer.camera(),source:__viewer.report()?.source,visible:__viewer.snapshot().visible,notice:document.getElementById("loading").textContent})')
        check('failed input preserves old source',current.get('source')==old['source'])
        check('failed input preserves draft and reference state',current['state']==old['state'])
        check('failed input preserves visible geometry',current['visible']==old['visible'])
        check('failed input preserves camera',current['camera']==old['camera'])
        shot=client.call('Page.captureScreenshot',{'format':'png','fromSurface':True});(out/'failed-import.png').write_bytes(base64.b64decode(shot['data']))
        # A syntactically recognizable IFC with no drawable content exercises rollback after OpenModel.
        import ifcopenshell
        empty=out/'empty.ifc';ifcopenshell.file(schema='IFC2X3').write(str(empty))
        client.call('DOM.setFileInputFiles',{'nodeId':node,'files':[qa.winpath(empty)]});time.sleep(2)
        check('empty IFC preserves old drawable model',client.js('__viewer.sourceSize()')==old['source']['bytes'] and len(client.js('__viewer.snapshot().visible'))==len(old['visible']))
        client.navigate('http://127.0.0.1:4178/ifc-viewer/?sample=174&engine=native&view=front')
        client.button('edges')
        doc=client.call('DOM.getDocument')['root']['nodeId'];node=client.call('DOM.querySelector',{'nodeId':doc,'selector':'#file'})['nodeId']
        real=HERE.parents[1]/'dataset/external/bimnet/hxp.ifc'
        client.call('DOM.setFileInputFiles',{'nodeId':node,'files':[qa.winpath(real)]})
        for _ in range(100):
            time.sleep(.1)
            if client.js('__viewer.report()?.source.name')==real.name:break
        check('ordinary file selection loads another IFC2X3',client.js('__viewer.report()?.source.name')==real.name and client.js('__viewer.report()?.source.schema')=='IFC2X3')
        check('edge setting and actual overlays agree after file change',client.js('globalThis.__viewer.displayState ? __viewer.displayState().edgesAgree : false'))
        check('fit tool states its behavior',client.js('document.getElementById("fit").title.includes("朝向")'))
        (out/'checks.json').write_text(json.dumps({'checks':checks,'passed':sum(x['passed'] for x in checks),'total':len(checks),'browser':'Windows Edge SwiftShader WebGL2','repair_called':False},ensure_ascii=False,indent=2),encoding='utf8')
        print(json.dumps(checks,ensure_ascii=False,indent=2));return all(x['passed'] for x in checks)
    finally:
        if client:
            try:client.call('Browser.close')
            except Exception:pass
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.terminate()
        log.close()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);a=ap.parse_args();raise SystemExit(0 if main(a.label) else 2)
