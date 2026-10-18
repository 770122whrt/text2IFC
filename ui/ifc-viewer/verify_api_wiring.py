"""Actual Edge -> local HTTP -> IFC selection context. Prepare-only; never enables a model."""
from pathlib import Path
import argparse
import base64
import json
import subprocess
import time
import urllib.request
from verify_browser import CDP, winpath


def main(label):
    out=Path('ui/ifc-viewer/.artifacts/api-wiring')/label
    out.mkdir(parents=True,exist_ok=False)
    checks=[];c=None;p=None
    def check(name,value):
        checks.append({'name':name,'passed':bool(value)})
        if not value:raise AssertionError(name)
    def wait(expression):
        for _ in range(250):
            if c.js(expression):return
            time.sleep(.1)
        raise AssertionError('Timed out: '+expression)
    def button(selector):
        r=c.js('(()=>{const e=document.querySelector('+json.dumps(selector)+');e.scrollIntoView({block:"nearest"});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()')
        c.click(**r)
    def pick(id):
        c.js('(()=>{const input=document.getElementById("treeSearch");const rec=__viewer.snapshot().records.find(r=>r.id==='+str(id)+');input.value=rec.guid;input.dispatchEvent(new Event("input",{bubbles:true}));})()')
        button('.tree-leaf[data-id="'+str(id)+'"] .tree-select')
    def shot(name):
        image=c.call('Page.captureScreenshot',{'format':'png','fromSurface':True})
        (out/name).write_bytes(base64.b64decode(image['data']))
    with (out/'edge.log').open('wb') as log:
        try:
            p=subprocess.Popen(['/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','--headless=new','--no-first-run','--disable-extensions','--disable-background-networking','--remote-debugging-port=9356','--remote-allow-origins=*','--use-angle=swiftshader','--enable-unsafe-swiftshader','--user-data-dir='+winpath(out/'profile'),'about:blank'],stdout=log,stderr=log)
            pages=None
            for _ in range(60):
                try:pages=json.load(urllib.request.urlopen('http://127.0.0.1:9356/json',timeout=1));break
                except Exception:time.sleep(.2)
            if not pages:raise RuntimeError('Isolated Edge did not start')
            c=CDP(next(x['webSocketDebuggerUrl'] for x in pages if x['type']=='page'))
            c.call('Page.enable');c.call('Runtime.enable');c.call('Network.enable')
            c.call('Emulation.setDeviceMetricsOverride',{'width':1600,'height':1000,'deviceScaleFactor':1,'mobile':False})
            c.navigate('http://127.0.0.1:4178/ifc-viewer/?sample=174&engine=native&view=side')
            check('actual IFC has 250 geometry products',c.js('__viewer.report().geometry.renderedProducts===250'))
            caps=c.js('fetch("/api/capabilities").then(r=>r.json())')
            check('same-origin API available and live execution off',caps['selection_text'] and caps['execution_enabled'] is False)
            button('#selectMode');pick(1895)
            reference=c.js('__viewer.snapshot().records.find(r=>r.type==="IfcWindow"&&r.parsedBoundsMetres).id')
            button('#addAux');pick(reference)
            original='在这面墙上加一扇窗，尺寸参考选中的窗。用户原文不改。'
            button('#request');c.call('Input.insertText',{'text':original})
            before=c.js('({camera:__viewer.camera(),state:__viewer.state(),bytes:__viewer.sourceSize(),visible:__viewer.snapshot().visible})')
            button('#submit')
            wait('!!document.getElementById("repairStart")')
            after=c.js('({camera:__viewer.camera(),state:__viewer.state(),bytes:__viewer.sourceSize(),visible:__viewer.snapshot().visible})')
            for key in before:check('prepare preserves '+key,before[key]==after[key])
            text=c.js('document.getElementById("repairPanel").textContent')
            names=c.js('[1895,'+str(reference)+'].map(id=>__viewer.snapshot().records.find(r=>r.id===id).name)')
            check('generated context includes both actual IFC names',all(n in text for n in names))
            check('context uses world coordinates not viewer camera', 'IFC世界坐标' in text and '不是新增构件放置点' in text)
            check('full input retains exact user words',original in text)
            check('start is explicitly disabled rather than a fake repair',c.js('document.getElementById("repairStart").disabled && __viewer.state().requests.length===0'))
            shot('prepare-chinese.png')
            context=c.js('Array.from(document.querySelectorAll("#repairPanel pre")).map(x=>x.textContent)')
            button('#langEn')
            check('English headings and unchanged prepared natural language',c.js('document.querySelector("#repairPanel h3").textContent==="Actual Repair request"') and c.js('Array.from(document.querySelectorAll("#repairPanel pre")).map(x=>x.textContent)')==context)
            shot('prepare-english.png')
            button('#viewMode')
            check('view mode does not invalidate prepared context',c.js('!!document.getElementById("repairStart")'))
            # Geometry interactions remain useful while the input context is prepared.
            camera=c.js('__viewer.camera()')
            c.call('Input.dispatchMouseEvent',{'type':'mousePressed','x':700,'y':440,'button':'left','clickCount':1})
            c.call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':755,'y':430,'button':'left','buttons':1})
            c.call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':755,'y':430,'button':'left','clickCount':1})
            check('rotation still works after API prepare',c.js('__viewer.camera()')!=camera)
            check('rotation does not change request references',c.js('__viewer.state().reference')==before['state']['reference'])
            button('#selectMode');button('#request');c.call('Input.insertText',{'text':' 新增修改'})
            check('editing request invalidates the prepared request',c.js('!document.getElementById("repairStart") && document.getElementById("repairPanel").textContent.includes("changed")'))
            button('#submit');wait('!!document.getElementById("repairStart")')
            button('#removeAux')
            check('changing reference also invalidates preparation',c.js('!document.getElementById("repairStart")'))
            c.call('Network.setBlockedURLs',{'urls':['*api/capabilities*']})
            button('#submit');wait('document.getElementById("repairPanel").textContent.includes("retained")')
            check('API failure retains user draft and real IFC',c.js('__viewer.state().draft.includes("新增修改") && __viewer.report().geometry.renderedProducts===250'))
            c.call('Network.setBlockedURLs',{'urls':[]})
            for width,height in [(1366,768),(1024,900)]:
                c.call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False});time.sleep(.2)
                check('no horizontal overflow '+str(width),c.js('document.documentElement.scrollWidth<=innerWidth+1'))
            result={'checks':checks,'passed':sum(x['passed'] for x in checks),'browser':'Windows Edge + SwiftShader WebGL2','actual_http':True,'live_provider_calls':0,'scope':'API preparation and state preservation; native task tests run separately'}
            (out/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(result,ensure_ascii=False,indent=2))
        except Exception as error:
            (out/'checks.json').write_text(json.dumps({'checks':checks,'error':str(error)},ensure_ascii=False,indent=2),encoding='utf-8')
            if c:
                try:shot('failure.png')
                except Exception:pass
            raise
        finally:
            if c:
                try:c.call('Browser.close')
                except Exception:pass
            if p:
                try:p.wait(timeout=6)
                except subprocess.TimeoutExpired:p.terminate()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);main(parser.parse_args().label)
