import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';
import {mkdir, mkdtemp, copyFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

test('viewer URL aliases, health identity and local-only allowlist',async()=>{
 const port=4203;
 const get=(url)=>fetch(url,{signal:AbortSignal.timeout(3000)});
 const child=spawn(process.execPath,['ui/ifc-viewer/serve.mjs'],{env:{...process.env,IFC_VIEWER_PORT:String(port)},stdio:'ignore'});
 try{
  let ready=false;
  for(let i=0;i<40;i++){try{const r=await get(`http://127.0.0.1:${port}/ifc-viewer/`);if(r.ok){ready=true;break;}}catch{}await delay(100);}
  assert.ok(ready,'temporary server starts');
  const health=await get(`http://127.0.0.1:${port}/health`).then(r=>r.json());
  assert.equal(health.service,'text2IFC-local-viewer');
  for(const suffix of ['','/ifc-viewer','/ifc-viewer/']){
   const r=await get(`http://127.0.0.1:${port}${suffix}`);assert.equal(r.status,200);assert.match(await r.text(),/真实 IFC/);
  }
  for(const suffix of ['/AGENTS.md','/dataset/','/ifc-viewer/../.env'])assert.equal((await get(`http://127.0.0.1:${port}${suffix}`)).status,404);
 }finally{if(child.exitCode===null){const exit=new Promise(resolve=>child.once('exit',resolve));child.kill();await Promise.race([exit,delay(1500)]);}}
});

test('a fresh checkout serves the workbench without requesting a private sample', async () => {
 const temporary = fileURLToPath(new URL('../../../.tmp/', import.meta.url));
 await mkdir(temporary, {recursive:true});
 const checkout = await mkdtemp(path.join(temporary, 'ui-empty-checkout-'));
 const viewer = path.join(checkout, 'ui', 'ifc-viewer');
 await mkdir(viewer, {recursive:true});
 for (const name of ['serve.mjs', 'startup.mjs', 'index.html']) {
  await copyFile(new URL('../'+name, import.meta.url), path.join(viewer, name));
 }
 const port=4204;
 const child=spawn(process.execPath,[path.join(viewer,'serve.mjs')],{env:{...process.env,IFC_VIEWER_PORT:String(port)},stdio:'ignore'});
 try {
  let response;
  for(let i=0;i<40;i++) {
   try { response=await fetch(`http://127.0.0.1:${port}/`,{redirect:'manual',signal:AbortSignal.timeout(1000)});if(response.ok||response.status===302)break; } catch {}
   await delay(100);
  }
  assert.equal(response?.status,302);
  assert.equal(response.headers.get('location'),'/ifc-viewer/');
  const page=await fetch(`http://127.0.0.1:${port}/ifc-viewer/`);
  assert.equal(page.status,200);
  assert.match(await page.text(),/真实 IFC/);
 } finally {
  if(child.exitCode===null){const exit=new Promise(resolve=>child.once('exit',resolve));child.kill();await Promise.race([exit,delay(1500)]);}
 }
});
