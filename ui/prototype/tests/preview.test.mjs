import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawn,spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import net from 'node:net';
const root=new URL('../',import.meta.url);
const html=readFileSync(new URL('index.html',root),'utf8');
test('DOM ids remain unique after separating layout and behavior',()=>{const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert.equal(ids.length,new Set(ids).size);});
test('all application DOM references exist',()=>{const ids=new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]));const js=readFileSync(new URL('app.mjs',root),'utf8');for(const m of js.matchAll(/\$\('([^']+)'\)/g))assert.ok(ids.has(m[1]),m[1]);});
test('prototype scripts parse without installing dependencies',()=>{for(const name of ['core.mjs','app.mjs','scene.mjs','serve.mjs','prepare.mjs']){const result=spawnSync(process.execPath,['--check',fileURLToPath(new URL(name,root))],{encoding:'utf8'});assert.equal(result.status,0,name+': '+result.stderr);}});
test('source links and styles are present',()=>{for(const name of ['styles.css','core.mjs','scene.mjs','app.mjs'])assert.ok(readFileSync(new URL(name,root)).length>0);assert.match(html,/id="modeView"/);assert.match(html,/id="modeSelect"/);assert.doesNotMatch(html,/id="caseWindow"|id="caseColumn"/);});
test('local server serves new JS/CSS and rejects repository access',{timeout:20000},async()=>{
 const probe=net.createServer();await new Promise((resolve,reject)=>{probe.once('error',reject);probe.listen(0,'127.0.0.1',resolve);});const port=probe.address().port;await new Promise(resolve=>probe.close(resolve));
 const child=spawn(process.execPath,[fileURLToPath(new URL('serve.mjs',root))],{env:{...process.env,UI_PREVIEW_PORT:String(port)},stdio:['ignore','pipe','pipe']});
 try{
  await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Server startup timeout')),5000);child.once('error',e=>{clearTimeout(timer);reject(e);});child.stdout.once('data',()=>{clearTimeout(timer);resolve();});child.once('exit',code=>{if(code){clearTimeout(timer);reject(Error('Server exit '+code));}});});
  const base=`http://127.0.0.1:${port}/`;
  for(const name of ['','styles.css','app.mjs','core.mjs','scene.mjs']){const response=await fetch(base+name);assert.equal(response.status,200,name);if(name.endsWith('.css'))assert.match(response.headers.get('content-type'),/^text\/css/);assert.ok((await response.text()).length>0);}
  assert.equal((await fetch(base+'AGENTS.md')).status,404);assert.equal((await fetch(base+'..%2f..%2fAGENTS.md')).status,404);assert.equal((await fetch(base,{method:'POST'})).status,405);
 }finally{
  if(child.exitCode===null){const exited=new Promise(resolve=>child.once('exit',resolve));child.kill('SIGTERM');await Promise.race([exited,new Promise(resolve=>setTimeout(resolve,3000))]);if(child.exitCode===null)child.kill('SIGKILL');}
 }
});
