"""Use an isolated headless Windows Edge profile from WSL for actual browser screenshots.
Starts a temporary local static server; closes it on exit. Never uses the personal browser profile.
"""
import json,os,re,subprocess,time,urllib.request
from pathlib import Path

ROOT=Path.cwd();OUT=ROOT/'ui/ifc-viewer/.artifacts/sample-174';OUT.mkdir(parents=True,exist_ok=True)
EDGE='/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
def winpath(p):
    s=str(p.resolve());parts=s.split('/');return parts[2].upper()+':\\'+'\\'.join(parts[3:])

def main():
    env=os.environ.copy();env['IFC_VIEWER_PORT']='4191'
    log=(OUT/'browser-server.log').open('w');server=subprocess.Popen(['node','ui/ifc-viewer/serve.mjs'],stdout=log,stderr=subprocess.STDOUT,env=env)
    results=[]
    try:
        for _ in range(40):
            try:
                with urllib.request.urlopen('http://127.0.0.1:4191/ifc-viewer/',timeout=1) as r:
                    if r.status==200:break
            except Exception:time.sleep(.25)
        for view,w,h in [('front',1276,736),('side',1396,1057)]:
            target=OUT/f'browser-{view}.png'
            # Keep the observed dependency failure when retrying a corrected bootstrap.
            import shutil
            for suffix in ['png','html','log']:
                old=OUT/f'browser-{view}.{suffix}';saved=OUT/f'first-attempt-{view}.{suffix}'
                if old.exists() and not saved.exists():shutil.copyfile(old,saved)
            cmd=[EDGE,'--headless=new','--no-first-run','--disable-extensions','--disable-background-networking','--no-default-browser-check','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-allow-origins=*','--user-data-dir='+winpath(OUT/('edge-profile-'+view)),'--window-size='+f'{w},{h}','--virtual-time-budget=30000','--run-all-compositor-stages-before-draw','--screenshot='+winpath(target),'--dump-dom',f'http://127.0.0.1:4191/ifc-viewer/?sample=174&capture=1&view={view}']
            completed=subprocess.run(cmd,capture_output=True,timeout=110)
            dom=completed.stdout.decode('utf8',errors='replace');(OUT/f'browser-{view}.html').write_text(dom,encoding='utf8');(OUT/f'browser-{view}.log').write_bytes(completed.stderr)
            ready='data-ifc-ready="true"' in dom
            m=re.search(r'data-geometry-products="(\d+)"',dom)
            results.append({'view':view,'exit_code':completed.returncode,'ready':ready,'rendered_products':int(m.group(1)) if m else None,'screenshot_exists':target.exists(),'screenshot_bytes':target.stat().st_size if target.exists() else 0})
            print(json.dumps(results[-1]),flush=True)
    finally:
        server.terminate()
        try:server.wait(timeout=5)
        except subprocess.TimeoutExpired:server.kill();server.wait()
        log.close();(OUT/'browser-capture.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    return 0 if results and all(x['ready'] and x['screenshot_exists'] for x in results) else 2
if __name__=='__main__':raise SystemExit(main())
