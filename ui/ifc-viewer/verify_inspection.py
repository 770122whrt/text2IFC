"""Real-pointer review of file opening, selected surfaces, tree and property UI. No Repair.
Usage: python3 ui/ifc-viewer/verify_inspection.py --label baseline [--baseline]
"""
from pathlib import Path
import argparse,base64,json,subprocess,time,urllib.request
from verify_browser import CDP,winpath


def main():
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--baseline',action='store_true');a=p.parse_args()
 out=Path('ui/ifc-viewer/.artifacts/inspection')/a.label;out.mkdir(parents=True,exist_ok=False)
 log=(out/'edge.log').open('wb');proc=None;c=None;checks=[]
 def check(name,value):
  checks.append({'name':name,'passed':bool(value)})
  if not value:raise AssertionError(name)
 def shot(name):
  time.sleep(.2);r=c.call('Page.captureScreenshot',{'format':'png','fromSurface':True});(out/name).write_bytes(base64.b64decode(r['data']))
 try:
  proc=subprocess.Popen(['/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','--headless=new','--no-first-run','--disable-extensions','--disable-background-networking','--remote-debugging-port=9339','--remote-allow-origins=*','--use-angle=swiftshader','--enable-unsafe-swiftshader','--user-data-dir='+winpath(out/'profile'),'about:blank'],stdout=log,stderr=log)
  pages=None
  for _ in range(70):
   try:pages=json.load(urllib.request.urlopen('http://127.0.0.1:9339/json',timeout=1));break
   except Exception:time.sleep(.2)
  if not pages:raise RuntimeError('Isolated Edge unavailable')
  c=CDP(next(x['webSocketDebuggerUrl'] for x in pages if x['type']=='page'));c.call('Page.enable');c.call('Runtime.enable');c.call('Emulation.setDeviceMetricsOverride',{'width':1600,'height':1000,'deviceScaleFactor':1,'mobile':False})
  c.navigate('http://127.0.0.1:4178/ifc-viewer/?sample=174&engine=native&view=side')
  check('native model loaded',c.js('__viewer.report().geometry.renderedProducts')==250)
  shot('workbench.png')
  # Use actual pointer picking in the lower-wing facade, not a mutation backdoor.
  rect=c.js('(()=>{const r=document.getElementById("canvas").getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})()')
  picked=None
  for fx,fy in [(0.46,.59),(.4,.63),(.5,.58),(.45,.7),(.63,.7)]:
   c.click(rect['x']+rect['w']*fx,rect['y']+rect['h']*fy)
   s=c.js('__viewer.state()');rec=c.js('__viewer.snapshot().records.find(r=>r.id===__viewer.state().inspected)')
   if rec and rec['type'] in ('IfcWall','IfcWallStandardCase'):picked=rec;break
  check('facade wall selected by pointer',picked is not None)
  (out/'selected-wall.json').write_text(json.dumps(picked,ensure_ascii=False,indent=2),encoding='utf8')
  shot('wall-selected.png');c.button('propertiesBtn');time.sleep(.5);shot('properties.png')
  (out/'property-text.txt').write_text(c.js('document.getElementById("properties").textContent'),encoding='utf8')
  if a.baseline:
   checks.append({'name':'tree control exists','passed':bool(c.js('document.getElementById("treeToggle")'))})
  else:
   check('readable instance properties present',c.js('document.querySelectorAll(".property-table tr").length')>3)
   check('property contains source pset terminology',c.js('document.getElementById("properties").textContent.includes("Pset_")'))
   check('raw JSON secondary',not c.js('document.getElementById("rawProperty").open'))
   c.button('closeProperty')
   check('tree visible',not c.js('document.getElementById("modelTree").hidden'))
   check('tree node count matches source records',c.js('document.querySelectorAll(".tree-leaf").length')==len(c.js('__viewer.snapshot().records')))
   c.js('(()=>{const e=document.getElementById("treeSearch");e.value='+json.dumps(picked['guid'])+';e.dispatchEvent(new Event("input",{bubbles:true}));})()')
   check('GUID search yields exact object',c.js('Array.from(document.querySelectorAll(".tree-leaf")).filter(e=>!e.hidden).length')==1)
   c.js('document.querySelector(".tree-leaf:not([hidden]) .tree-select").focus()');shot('tree-search.png')
   row=c.js('(()=>{const r=document.querySelector(".tree-leaf:not([hidden]) .tree-select").getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()');c.click(**row)
   check('tree click resolves same wall',c.js('__viewer.state().inspected')==picked['id'])
   c.button('propertiesBtn');time.sleep(.25);check('tree-selected properties stable',c.js('document.getElementById("properties").textContent.includes('+json.dumps(picked['guid'])+')'));c.button('closeProperty')
   c.js('(()=>{const e=document.getElementById("treeSearch");e.value="";e.dispatchEvent(new Event("input",{bubbles:true}));})()')
  if not a.baseline:
   # Download is a real button click; compare file bytes, not just reported length.
   downloads=out/'downloads';downloads.mkdir();c.call('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':winpath(downloads)})
   c.button('saveSource')
   target=downloads/'model_174.ifc'
   for _ in range(50):
    if target.exists():break
    time.sleep(.1)
   check('download preserves exact source IFC bytes',target.exists() and target.read_bytes()==Path('ui/ifc-viewer/.artifacts/sample-174/source.ifc').read_bytes())
   # A small overlapping-face fixture tests visible selection AND foreground occlusion.
   pixels=c.js('''(async()=>{
    const T=await import('./vendor/three.module.js'),{SelectionHighlighter}=await import('./selection-highlight.mjs');
    const r=new T.WebGLRenderer({antialias:false,preserveDrawingBuffer:true});r.setSize(64,64);r.outputColorSpace=T.SRGBColorSpace;r.toneMapping=T.NoToneMapping;
    const sc=new T.Scene(),cam=new T.OrthographicCamera(-2,2,2,-2,.1,10);cam.position.z=4;cam.lookAt(0,0,0);
    const selected=new T.Group(),plane=new T.Mesh(new T.PlaneGeometry(3,3),new T.MeshBasicMaterial({color:0x999999}));selected.add(plane);sc.add(selected);
    const conflict=new T.Mesh(new T.PlaneGeometry(3,3),new T.MeshBasicMaterial({color:0x888888}));sc.add(conflict);
    const front=new T.Mesh(new T.PlaneGeometry(1,1),new T.MeshBasicMaterial({color:0x0044aa}));front.position.z=.5;sc.add(front);
    const high=new SelectionHighlighter();high.select(selected);r.render(sc,cam);const gl=r.getContext(),out=new Uint8Array(64*64*4);gl.readPixels(0,0,64,64,gl.RGBA,gl.UNSIGNED_BYTE,out);
    const at=(x,y)=>Array.from(out.slice((y*64+x)*4,(y*64+x)*4+3)),v={selected:at(15,32),occluder:at(32,32)};
    high.clear();sc.traverse(x=>{x.geometry?.dispose();x.material?.dispose();});r.dispose();r.forceContextLoss();return v;
   })()''')
   check('coplanar selection rendered in uniform selected colour',pixels['selected']==[214,172,92])
   check('true foreground occluder is not painted through',pixels['occluder']==[0,68,170])
   for width,height in [(1366,768),(800,900),(390,844)]:
    c.call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False});time.sleep(.15)
    check('no page horizontal overflow '+str(width),c.js('document.documentElement.scrollWidth<=innerWidth+1'))
  check('no repair backend',c.js('__viewer.state().requests.length')==0)
 except Exception as e:
  checks.append({'name':'exception','passed':False,'detail':str(e)})
  if c:
   try:shot('failure.png')
   except Exception:pass
  raise
 finally:
  (out/'checks.json').write_text(json.dumps({'label':a.label,'checks':checks,'passed':sum(x['passed'] for x in checks),'scope':'real Edge/WebGL2; source unchanged; no LLM or Repair'},ensure_ascii=False,indent=2),encoding='utf8')
  print(json.dumps({'out':str(out),'checks':checks},ensure_ascii=False,indent=2),flush=True)
  if c:
   try:c.call('Browser.close')
   except Exception:pass
  if proc:
   try:proc.wait(timeout=6)
   except subprocess.TimeoutExpired:proc.terminate()
  log.close()
if __name__=='__main__':main()
