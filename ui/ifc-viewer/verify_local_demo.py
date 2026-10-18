"""Local viewer multi-target + archived examples in real Edge. No live model calls."""
from pathlib import Path
import argparse,base64,json,subprocess,time,urllib.request
from verify_browser import CDP,winpath


def main(label):
    out=Path('ui/ifc-viewer/.artifacts/local-demo')/label;out.mkdir(parents=True,exist_ok=False)
    checks=[];c=None;proc=None
    def check(name,value):
        checks.append({'name':name,'passed':bool(value)})
        if not value:raise AssertionError(name)
    def button(selector):
        point=c.js('(()=>{const e=document.querySelector('+json.dumps(selector)+');e.scrollIntoView({block:"nearest"});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()');c.click(**point)
    def pick(ident):
        c.js('(()=>{const i=document.getElementById("treeSearch"),r=__viewer.snapshot().records.find(r=>r.id==='+str(ident)+');i.value=r.guid;i.dispatchEvent(new Event("input",{bubbles:true}));})()')
        button('.tree-leaf[data-id="'+str(ident)+'"] .tree-select')
    def wait(expr,seconds=60):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if c.js(expr):return
            time.sleep(.15)
        raise AssertionError('Timeout: '+expr)
    def shot(name):
        data=c.call('Page.captureScreenshot',{'format':'png','fromSurface':True});(out/name).write_bytes(base64.b64decode(data['data']))
    with (out/'edge.log').open('wb') as log:
        try:
            proc=subprocess.Popen(['/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','--headless=new','--no-first-run','--disable-extensions','--disable-background-networking','--remote-debugging-port=9360','--remote-allow-origins=*','--use-angle=swiftshader','--enable-unsafe-swiftshader','--user-data-dir='+winpath(out/'profile'),'about:blank'],stdout=log,stderr=log)
            pages=None
            for _ in range(70):
                try:pages=json.load(urllib.request.urlopen('http://127.0.0.1:9360/json',timeout=1));break
                except Exception:time.sleep(.2)
            c=CDP(next(p['webSocketDebuggerUrl'] for p in pages if p['type']=='page'));c.call('Page.enable');c.call('Runtime.enable')
            c.call('Emulation.setDeviceMetricsOverride',{'width':1600,'height':1000,'deviceScaleFactor':1,'mobile':False})
            c.navigate('http://127.0.0.1:4178/ifc-viewer/?sample=174&engine=native&view=side')
            check('actual source remains 250 drawable products',c.js('__viewer.report().geometry.renderedProducts===250'))
            classification=c.js('__viewer.report().displayClassification')
            check('seven spatial records are not reported as missing geometry',len(classification['spatial'])==7 and not classification['missing'])
            check('five actual roof/stair assemblies have drawable parts',len(classification['aggregates'])==5 and not classification['incompleteAggregates'] and not classification['otherWithoutRepresentation'])
            check('one-line summary omits routine counts but retains a material notice',c.js('document.getElementById("stats").textContent.includes("250") && document.getElementById("stats").textContent.includes("材质") && !document.getElementById("stats").textContent.includes("101") && !document.getElementById("stats").textContent.includes("12 个对象")'))
            shot('current-clean-view.png')
            button('#reportButton')
            detail=c.js('document.getElementById("diagnosticSummary").textContent')
            check('expanded diagnostics preserve the original repeated material error','Error' in detail and '32' in detail and '#1145' in detail)
            style=c.js('__viewer.report().native.diagnosticAudit.style_audit')
            check('actual mesh material indices are assigned without claiming pixel equivalence',style['rendered_products']==250 and style['products_with_explicit_style']==236 and style['unassigned_triangles']==0)
            shot('official-classification-detail.png')
            button('#reportButton')
            cap=c.js('fetch("/api/capabilities").then(r=>r.json())');check('multi-target API ready, no paid mode enabled',cap['multiple_targets'] and not cap['execution_enabled'])
            walls=c.js('__viewer.snapshot().records.filter(r=>r.type.includes("IfcWall")&&r.parsedBoundsMetres).slice(0,2).map(r=>r.id)')
            window=c.js('__viewer.snapshot().records.find(r=>r.type==="IfcWindow"&&r.parsedBoundsMetres).id')
            button('#selectMode');button('#multiSelect');pick(walls[0]);pick(walls[1])
            selected=c.js('__viewer.selectionDetails()')
            check('both operation targets remain selected and highlighted',set(walls).issubset(selected['highlightedIds']) and selected['targetIds']==walls)
            check('multi selection list contains both targets',c.js('document.querySelectorAll("#targetList .target-row").length===2'))
            button('#addAux');pick(window)
            check('common reference does not replace the targets',c.js('__viewer.state().auxReference.id')==window and c.js('__viewer.selectionDetails().targetIds')==walls)
            button('#request');c.call('Input.insertText',{'text':'在这两面墙上各增加一扇窗，尺寸参考这扇窗。'})
            camera=c.js('__viewer.camera()');button('#submit');wait('!!document.getElementById("repairStart")')
            text=c.js('document.getElementById("repairPanel").textContent')
            check('real API prepares two explicit natural-language targets','对象 1' in text and '对象 2' in text)
            check('prepare preserves camera and targets',c.js('__viewer.camera()')==camera and c.js('__viewer.selectionDetails().targetIds')==walls)
            shot('multiple-targets.png')
            button('#viewMode');pick(window)
            check('view mode inspections do not alter targets',c.js('__viewer.selectionDetails().targetIds')==walls)
            pick(walls[0]);button('.tree-leaf[data-id="'+str(walls[0])+'"] .tree-visibility')
            check('hiding a selected target preserves reference but hides highlight',walls[0] in c.js('__viewer.selectionDetails().targetIds') and walls[0] not in c.js('__viewer.selectionDetails().highlightedIds'))
            button('#undoHide');button('#langEn')
            check('language switch preserves both targets and pending text',c.js('__viewer.selectionDetails().targetIds')==walls and '在这两面墙上' in c.js('__viewer.state().draft'))
            button('#langZh');button('#selectMode');button('#multiSelect')
            check('disabling multi does not silently discard another target',c.js('__viewer.selectionDetails().targetIds')==walls)
            if not c.js('document.getElementById("targetGroup").open'):button('#targetGroup > summary')
            button('#clearTargets');check('explicit clear removes all targets',c.js('__viewer.selectionDetails().targetIds.length===0'))
            button('#multiSelect')
            button('#examplesButton');wait('document.getElementById("examplesDialog").open')
            check('two archived actual successful examples are available',c.js('document.querySelectorAll(".example-card").length===2'))
            shot('examples-menu.png')
            for ident,kind in [('case-001','IfcWindow'),('case-002','IfcDoor')]:
                if not c.js('document.getElementById("examplesDialog").open'):button('#examplesButton')
                button('[data-example-id="'+ident+'"][data-example-mode="history"]')
                wait('document.body.dataset.repairResultReady==="history" && document.getElementById("modelName").textContent==="archived-result.ifc"')
                check(ident+' is explicitly archived, not a new run','历史成功记录' in c.js('document.getElementById("exampleBanner").textContent') and c.js('__viewer.state().requests.length===0'))
                after=c.js('__viewer.snapshot().records.filter(r=>r.type==='+json.dumps(kind)+').length');camera=c.js('__viewer.camera()');offset=c.js('__viewer.frame().displayOffset')
                shot(ident+'-after.png');button('#viewBefore');before=c.js('__viewer.snapshot().records.filter(r=>r.type==='+json.dumps(kind)+').length')
                check(ident+' archived actual IFC adds exactly one target',after==before+1)
                check(ident+' before/after preserve camera and common origin',c.js('__viewer.camera()')==camera and c.js('__viewer.frame().displayOffset')==offset)
                button('#viewAfter');button('#locateChange');check(ident+' added object can be individually located',c.js('__viewer.snapshot().records.find(r=>r.id===__viewer.state().inspected).type')==kind)
                shot(ident+'-located.png');button('#resetExample');wait('!document.body.dataset.repairResultReady')
                check(ident+' restart restores the input and editable request without execution',c.js('__viewer.snapshot().records.filter(r=>r.type==='+json.dumps(kind)+').length')==before and c.js('__viewer.state().draft.length>0 && __viewer.state().requests.length===0'))
            for width,height in [(1366,768),(1024,900)]:
                c.call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False});time.sleep(.2)
                check('no horizontal overflow '+str(width),c.js('document.documentElement.scrollWidth<=innerWidth+1'))
            result={'checks':checks,'passed':sum(x['passed'] for x in checks),'browser':'Windows Edge / SwiftShader WebGL2','paid_calls':0,'examples':'two archived actual successful runs; no new Repair execution'}
            (out/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
        except Exception as e:
            (out/'checks.json').write_text(json.dumps({'checks':checks,'error':str(e)},ensure_ascii=False,indent=2),encoding='utf-8')
            if c:
                try:shot('failure.png')
                except Exception:pass
            raise
        finally:
            if c:
                try:c.call('Browser.close')
                except Exception:pass
            if proc:
                try:proc.wait(timeout=6)
                except subprocess.TimeoutExpired:proc.terminate()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);main(parser.parse_args().label)
