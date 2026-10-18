"""Bounded real-browser UI-language check. Uses an isolated Edge profile, no Repair/LLM.
The user's running viewer service is left running. Evidence directories are never overwritten.
"""
from pathlib import Path
import argparse,base64,json,subprocess,time,urllib.request
from verify_browser import CDP,winpath


def main(label):
 out=Path('ui/ifc-viewer/.artifacts/i18n')/label
 out.mkdir(parents=True,exist_ok=False)
 checks=[];client=None;process=None;log=(out/'edge.log').open('wb')
 def check(name,value):
  checks.append({'name':name,'passed':bool(value)})
  if not value:raise AssertionError(name)
 def shot(name):
  time.sleep(.15);result=client.call('Page.captureScreenshot',{'format':'png','fromSurface':True});(out/name).write_bytes(base64.b64decode(result['data']))
 def click_css(selector):
  rect=client.js('(()=>{const e=document.querySelector('+json.dumps(selector)+');e.scrollIntoView({block:"nearest"});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()')
  client.click(**rect)
 def search(value):
  client.js('(()=>{const e=document.getElementById("treeSearch");e.value='+json.dumps(value)+';e.dispatchEvent(new Event("input",{bubbles:true}));})()')
 def select_id(id):
  record=client.js('__viewer.snapshot().records.find(r=>r.id==='+str(id)+')')
  search(record['guid'] or '#'+str(id));click_css('.tree-leaf[data-id="'+str(id)+'"] .tree-select')
 def observe():
  return client.js('({state:__viewer.state(),camera:__viewer.camera(),report:__viewer.report(),visible:__viewer.snapshot().visible,sourceBytes:__viewer.sourceSize(),search:document.getElementById("treeSearch").value,expanded:Array.from(document.querySelectorAll("#treeContent details")).map(x=>x.open),propertyExpanded:Array.from(document.querySelectorAll("#properties details")).map(x=>x.open),raw:document.querySelector("#rawProperty pre")?.textContent,names:Array.from(document.querySelectorAll(".tree-select")).map(x=>x.textContent),resources:performance.getEntriesByType("resource").filter(x=>/sample.ifc|native-meshes|wasm/.test(x.name)).length})')
 def file_input(path):
  doc=client.call('DOM.getDocument')['root']['nodeId'];node=client.call('DOM.querySelector',{'nodeId':doc,'selector':'#file'})['nodeId']
  client.call('DOM.setFileInputFiles',{'nodeId':node,'files':[winpath(path)]})
 try:
  process=subprocess.Popen(['/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','--headless=new','--no-first-run','--disable-extensions','--disable-background-networking','--remote-debugging-port=9346','--remote-allow-origins=*','--use-angle=swiftshader','--enable-unsafe-swiftshader','--user-data-dir='+winpath(out/'profile'),'about:blank'],stdout=log,stderr=log)
  pages=None
  for _ in range(70):
   try:pages=json.load(urllib.request.urlopen('http://127.0.0.1:9346/json',timeout=1));break
   except Exception:time.sleep(.2)
  if not pages:raise RuntimeError('Isolated Edge unavailable')
  client=CDP(next(x['webSocketDebuggerUrl'] for x in pages if x['type']=='page'))
  client.call('Page.enable');client.call('Runtime.enable')
  client.call('Emulation.setDeviceMetricsOverride',{'width':1600,'height':1000,'deviceScaleFactor':1,'mobile':False})
  url='http://127.0.0.1:4178/ifc-viewer/?sample=174&engine=native&view=side'
  client.navigate(url)
  check('default Chinese and actual native IFC',client.js('document.documentElement.lang==="zh-CN" && __viewer.report().geometry.renderedProducts===250'))
  client.button('selectMode');select_id(1895)
  door=client.js('__viewer.snapshot().records.find(r=>r.type==="IfcDoor" && r.parsedBoundsMetres).id')
  client.button('addAux');select_id(door)
  client.button('request');client.call('Input.insertText',{'text':'保持原文：在这面墙上加窗。Keep this exact request.'});client.button('submit')
  client.button('request');client.call('Input.insertText',{'text':'下一条草稿 中文 / English draft'})
  client.button('viewMode')
  beam=client.js('__viewer.snapshot().records.find(r=>r.type==="IfcBeam" && r.parsedBoundsMetres).id')
  select_id(beam);click_css('.tree-leaf[data-id="'+str(beam)+'"] .tree-visibility')
  select_id(1895);client.button('propertiesBtn');time.sleep(.2)
  # Preserve deliberately expanded details as well as raw IFC text across language changes.
  click_css('#properties details.property-section:first-of-type > summary')
  before=observe();shot('chinese-properties.png')
  client.button('langEn');after=observe()
  check('English controls and html language',client.js('document.documentElement.lang==="en" && document.getElementById("viewMode").textContent==="View" && document.getElementById("treeToggle").textContent==="Model tree"'))
  for key in ['state','camera','report','visible','sourceBytes','search','expanded','propertyExpanded','raw','names','resources']:
   check('language preserves '+key,before[key]==after[key])
  check('property headings and logical values translated',client.js('document.getElementById("properties").textContent.includes("Instance properties") && document.getElementById("properties").textContent.includes("LoadBearing") && Array.from(document.querySelectorAll(".property-table td")).some(e=>e.textContent==="No")'))
  check('dynamic status and hidden count translated',client.js('document.getElementById("stats").textContent.startsWith("Model displayed") && document.getElementById("hiddenCount").textContent==="Hidden: 1"'))
  check('request note translated but request untouched',client.js('document.querySelector(".message").firstChild.textContent==="保持原文：在这面墙上加窗。Keep this exact request." && document.querySelector(".message small").textContent.startsWith("Saved on this page")'))
  shot('english-properties.png')
  client.button('langZh');back=observe()
  check('switch back preserves complete task state',back['state']==before['state'] and back['camera']==before['camera'] and back['raw']==before['raw'])
  client.button('langEn');client.button('closeProperty');search('');client.button('clearInspection');client.button('showAll');shot('english-workbench.png')
  for w,h in [(1366,768),(1024,900),(390,844)]:
   client.call('Emulation.setDeviceMetricsOverride',{'width':w,'height':h,'deviceScaleFactor':1,'mobile':False});time.sleep(.2)
   check('English layout has no horizontal overflow '+str(w),client.js('document.documentElement.scrollWidth<=innerWidth+1'))
   if w==1366:shot('english-laptop.png')
  client.call('Emulation.setDeviceMetricsOverride',{'width':1600,'height':1000,'deviceScaleFactor':1,'mobile':False})
  client.navigate(url)
  check('English preference survives reload',client.js('document.documentElement.lang==="en" && document.getElementById("langEn").getAttribute("aria-pressed")==="true"'))
  # Invalid local input: no loss of the existing model, and notices switch languages too.
  source_before=client.js('__viewer.sourceSize()');invalid=out/'invalid.ifc';invalid.write_text('not an IFC',encoding='utf8');file_input(invalid);time.sleep(.6)
  check('failed input shows English explanation and keeps IFC',client.js('document.getElementById("loadNotice").textContent.startsWith("Could not open")') and client.js('__viewer.sourceSize()')==source_before)
  client.button('langZh');check('existing error switches to Chinese',client.js('document.getElementById("loadNotice").textContent.startsWith("未打开")'))
  client.button('langEn')
  source=Path('dataset/external/bimnet/hxp.ifc');file_input(source)
  for _ in range(100):
   time.sleep(.1)
   if client.js('document.getElementById("modelName").textContent==="hxp.ifc" && !__viewer.displayState().loading'):break
  check('English ordinary file opening works',client.js('__viewer.report().source.name==="hxp.ifc" && __viewer.report().source.schema==="IFC2X3" && __viewer.report().geometry.renderedProducts>0'))
  check('source model name not overwritten by localization',client.js('document.getElementById("modelName").textContent==="hxp.ifc"'))
  downloads=out/'downloads';downloads.mkdir();client.call('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':winpath(downloads)});client.button('saveSource')
  for _ in range(50):
   if (downloads/'hxp.ifc').exists():break
   time.sleep(.1)
  check('English download returns original IFC bytes',(downloads/'hxp.ifc').exists() and (downloads/'hxp.ifc').read_bytes()==source.read_bytes())
  check('no Repair request was executed',client.js('__viewer.state().requests.length===0'))
  result={'browser':'Windows Edge headless + SwiftShader WebGL2','checks':checks,'passed':sum(x['passed'] for x in checks),'repair_called':False,'notes':'State invariants tested by actual buttons; source and user text retained; isolated preference storage.'}
  (out/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))
 except Exception as error:
  checks.append({'name':'exception','passed':False,'detail':str(error)})
  if client:
   try:shot('failure.png')
   except Exception:pass
  (out/'checks.json').write_text(json.dumps({'checks':checks,'error':str(error)},ensure_ascii=False,indent=2),encoding='utf8');raise
 finally:
  if client:
   try:client.call('Browser.close')
   except Exception:pass
  if process:
   try:process.wait(timeout=6)
   except subprocess.TimeoutExpired:process.terminate()
  log.close()

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);main(parser.parse_args().label)
