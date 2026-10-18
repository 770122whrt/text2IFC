"""Real Edge/WebGL verification via CDP, isolated profile. Leaves the user's viewer service running."""
from pathlib import Path
import sys,subprocess,time,json,base64,urllib.request
sys.path.insert(0,str(Path(__file__).parent/'.python'))
import websocket
ROOT=Path.cwd();OUT=ROOT/'ui/ifc-viewer/.artifacts/sample-174';OUT.mkdir(parents=True,exist_ok=True)
def winpath(p):
 s=str(p.resolve()).split('/');return s[2].upper()+':\\'+'\\'.join(s[3:])
class CDP:
 def __init__(self,url):self.ws=websocket.create_connection(url,timeout=20,suppress_origin=True);self.i=0
 def call(self,method,params=None):
  self.i+=1;i=self.i;self.ws.send(json.dumps({'id':i,'method':method,'params':params or {}}))
  while True:
   r=json.loads(self.ws.recv())
   if r.get('id')==i:
    if 'error' in r:raise RuntimeError(str(r['error']))
    return r.get('result',{})
 def js(self,code):
  r=self.call('Runtime.evaluate',{'expression':code,'returnByValue':True,'awaitPromise':True})
  if 'exceptionDetails' in r:raise RuntimeError(str(r['exceptionDetails']))
  return r.get('result',{}).get('value')
 def click(self,x,y,button='left'):
  self.call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':x,'y':y})
  self.call('Input.dispatchMouseEvent',{'type':'mousePressed','x':x,'y':y,'button':button,'clickCount':1})
  self.call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':x,'y':y,'button':button,'clickCount':1});time.sleep(.12)
 def button(self,id):
  b=self.js("(()=>{const r=document.getElementById("+json.dumps(id)+").getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()")
  self.click(**b)
 def navigate(self,url):
  self.call('Page.navigate',{'url':url})
  for _ in range(150):
   time.sleep(.2)
   try:
    if self.js('!!globalThis.__IFC_READY__'):return
    e=self.js('globalThis.__IFC_ERROR__||null')
    if e:raise RuntimeError(e)
   except websocket.WebSocketTimeoutException:raise
  raise RuntimeError('IFC ready timeout')
 def shot(self,name):
  time.sleep(.25);r=self.call('Page.captureScreenshot',{'format':'png','fromSurface':True});(OUT/name).write_bytes(base64.b64decode(r['data']))

def main():
 log=(OUT/'edge-review.log').open('wb');checks=[];client=None
 args=['/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','--headless=new','--no-first-run','--no-default-browser-check','--disable-extensions','--disable-background-networking','--remote-debugging-port=9336','--remote-allow-origins=*','--use-angle=swiftshader','--enable-unsafe-swiftshader','--user-data-dir='+winpath(OUT/'edge-review-profile'),'about:blank']
 proc=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT)
 def check(name,value):
  checks.append({'name':name,'passed':bool(value)})
  if not value:raise AssertionError(name)
 try:
  pages=None
  for _ in range(60):
   try:pages=json.load(urllib.request.urlopen('http://127.0.0.1:9336/json',timeout=1));break
   except Exception:time.sleep(.2)
  if not pages:raise RuntimeError('Cannot connect to isolated Edge CDP')
  client=CDP(next(p['webSocketDebuggerUrl'] for p in pages if p['type']=='page'))
  client.call('Page.enable');client.call('Runtime.enable')
  for engine in ['webifc','native']:
   for view,w,h in [('front',1276,736),('side',1396,1057)]:
    client.call('Emulation.setDeviceMetricsOverride',{'width':w,'height':h,'deviceScaleFactor':1,'mobile':False})
    client.navigate(f'http://127.0.0.1:4178/ifc-viewer/?sample=174&engine={engine}&capture=1&view={view}')
    r=client.js('__viewer.report()');(OUT/f'{engine}-precise-report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
    check(engine+' '+view+' actual 250 geometry products',r['geometry']['renderedProducts']==250)
    client.shot('fidelity-'+engine+'-'+view+'.png')
  check('native source bytes verified',r['native']['exactSourceBytesMatched'])
  check('native triangle count retained',r['geometry']['triangles']==149378)
  client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':960,'deviceScaleFactor':1,'mobile':False})
  client.navigate('http://127.0.0.1:4178/ifc-viewer/?sample=174&engine=native&view=side')
  client.shot('fidelity-workbench.png')
  before=client.js('__viewer.camera()')
  client.call('Input.dispatchMouseEvent',{'type':'mousePressed','x':650,'y':450,'button':'left','clickCount':1})
  for i in range(1,9):client.call('Input.dispatchMouseEvent',{'type':'mouseMoved','x':650+i*7,'y':450-i*3,'button':'left','buttons':1})
  client.call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':706,'y':426,'button':'left','clickCount':1})
  check('mouse drag rotates real IFC',before['position']!=client.js('__viewer.camera()')['position'])
  z=client.js('__viewer.camera().zoom');client.call('Input.dispatchMouseEvent',{'type':'mouseWheel','x':650,'y':450,'deltaX':0,'deltaY':-120})
  check('wheel zooms real IFC',z!=client.js('__viewer.camera().zoom'))
  client.button('fit');time.sleep(.2)
  candidates=client.js("__viewer.snapshot().records.filter(x=>x.parsedBoundsMetres).map(x=>({id:x.id,p:__viewer.project(x.id)}))")
  choices=[]
  for x in candidates:
   p=x['p']
   if p and 340<p['x']<990 and 260<p['y']<770:
    client.click(p['x'],p['y']);s=client.js('__viewer.state()');actual=s['inspected']
    if actual is not None and all(actual!=a['id'] for a in choices):choices.append({'id':actual,'x':p['x'],'y':p['y']})
    if len(choices)>=2:break
  check('actual geometry picking returns distinct IFC identities',len(choices)==2)
  check('view picking does not attach references',s['reference'] is None)
  client.button('selectMode');client.click(choices[0]['x'],choices[0]['y']);client.button('addAux');client.click(choices[1]['x'],choices[1]['y'])
  s=client.js('__viewer.state()');check('primary and auxiliary references remain distinct',s['reference']['id']!=s['auxReference']['id'])
  client.button('viewMode');client.click(choices[0]['x'],choices[0]['y'],button='right')
  check('right click opens hide menu',not client.js('document.getElementById("context").hidden'))
  camera=client.js('__viewer.camera()');count=len(client.js('__viewer.snapshot().visible'))
  client.button('hide');hidden=client.js('__viewer.state()')
  check('only one IFC product hidden',len(client.js('__viewer.snapshot().visible'))==count-1)
  check('hide preserves both references',hidden['reference']==s['reference'] and hidden['auxReference']==s['auxReference'])
  check('hide preserves camera',camera==client.js('__viewer.camera()'))
  client.shot('fidelity-hidden.png');client.button('undoHide');check('undo restores product',len(client.js('__viewer.snapshot().visible'))==count)
  client.click(choices[0]['x'],choices[0]['y'],button='right');client.button('hide');client.button('showAll');check('show all restores hidden model',len(client.js('__viewer.snapshot().visible'))==250)
  check('no repair execution',all(x['status']=='pending_backend' for x in client.js('__viewer.state().requests')))
  client.shot('fidelity-interaction.png')
  result={'passed':sum(x['passed'] for x in checks),'checks':checks,'browser':'Windows Edge headless + SwiftShader WebGL2','source':'same sample bytes bound to native mesh','repair_called':False,'server_kept_running':True}
  (OUT/'fidelity-browser-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))
 finally:
  if client:
   try:client.call('Browser.close')
   except Exception:pass
  try:proc.wait(timeout=5)
  except subprocess.TimeoutExpired:proc.terminate()
  log.close()
if __name__=='__main__':main()
