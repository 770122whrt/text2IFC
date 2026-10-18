/** Explicit local start/status/stop. No login task or system service. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawn,spawnSync} from 'node:child_process';
import {randomUUID} from 'node:crypto';
import {setTimeout as delay} from 'node:timers/promises';
import {hasLocalSample, viewerEntry, pythonCandidates} from './startup.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
const port=Number(process.env.IFC_VIEWER_PORT||4178);
if(!Number.isInteger(port)||port<1024||port>65535)throw Error('Invalid port');
const dir=path.join(here,'.artifacts');fs.mkdirSync(dir,{recursive:true});
const record=path.join(dir,`service-${port}.json`),url=`http://127.0.0.1:${port}`;
const entry=viewerEntry(hasLocalSample(here));
async function health(){try{const r=await fetch(url+'/health',{signal:AbortSignal.timeout(1500)});return r.ok?await r.json():null;}catch{return null;}}
const action=process.argv[2]||'start',current=await health();
if(!['start','stop','status'].includes(action))throw Error('Use start, status, or stop');
if(action==='status'){console.log(JSON.stringify(current||{running:false,port}));}
else if(action==='stop'){
 if(!current){console.log('No responding viewer on '+port);}
 else{
  const saved=fs.existsSync(record)?JSON.parse(fs.readFileSync(record,'utf8')):null;
  if(!saved||current.service!=='text2IFC-local-viewer'||current.instance!==saved.instance||current.pid!==saved.pid||(current.platform&&current.platform!==process.platform))throw Error('This launcher does not own the listener; refusing to stop another process.');
  process.kill(saved.pid,'SIGTERM');await delay(500);fs.rmSync(record,{force:true});console.log('Stopped this viewer.');
 }
}else if(current){
 if(current.service!=='text2IFC-local-viewer')throw Error('Port is occupied by another service.');
 console.log('Already running: '+url+entry);
}else{
 const instance=randomUUID(),log=fs.openSync(path.join(dir,`service-${port}.log`),'a');
 const child=spawn(process.execPath,[path.join(here,'serve.mjs')],{cwd:here,env:{...process.env,IFC_VIEWER_PORT:String(port),IFC_VIEWER_INSTANCE:instance},detached:true,stdio:['ignore',log,log],windowsHide:true});
 child.on('error',e=>console.error(e.message));child.unref();fs.closeSync(log);
 let ready=null;
 for(let i=0;i<30;i++){await delay(150);ready=await health();if(ready?.instance===instance)break;}
 if(ready?.instance!==instance)throw Error('Viewer failed to become ready; inspect .artifacts/service-'+port+'.log');
 fs.writeFileSync(record,JSON.stringify({pid:ready.pid,instance,port,startedAt:new Date().toISOString()},null,2));
 console.log(JSON.stringify({running:true,pid:ready.pid,url:url+entry,persistence:'until stopped or Windows/WSL shutdown',repairEnabled:false}));
}
if(action!=='status'){
 const interpreters=pythonCandidates(path.resolve(here,'../..'),process.platform,process.env.TEXT2IFC_PYTHON);
 let ready=false,lastError='Python 3.12+ not found';
 for(const executable of interpreters){
  const result=spawnSync(executable,['api_launcher.py',action],{cwd:here,env:{...process.env,PYTHONIOENCODING:'utf-8'},encoding:'utf8',timeout:25000,windowsHide:true});
  if(result.status===0){console.log(result.stdout.trim());ready=true;break;}
  lastError=result.stderr?.trim()||result.error?.message||lastError;
 }
 if(!ready)console.warn('Viewer is available; Repair API '+action+' failed. Set TEXT2IFC_PYTHON. '+lastError);
}
