/** Local static viewer; does not expose the repository, upload IFC, or start Repair. */
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {hasLocalSample, viewerEntry} from './startup.mjs';
const ui=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const port=Number(process.env.IFC_VIEWER_PORT||4178);
if(!Number.isInteger(port)||port<1024||port>65535)throw Error('Invalid IFC_VIEWER_PORT');
const files=['index.html','styles.css','repair-api.css','repair-client.mjs','repair-panel.mjs','multi-selection.mjs','result-list.mjs','local-examples.mjs','diagnostics-display.mjs','model-pair.mjs','viewer.mjs','i18n.mjs','native-mesh-adapter.mjs','model-contract.mjs','selection-highlight.mjs','inspection-data.mjs','inspection-panel.mjs','display-geometry.mjs','vendor/three.module.js','vendor/three.core.js','vendor/OrbitControls.js','vendor/web-ifc-api-iife.js','vendor/web-ifc.wasm'];
const allowed=new Set(files.map(f=>'ifc-viewer/'+f));allowed.add('prototype/core.mjs');
// Exact, already verified user-supplied sample and its derived outputs only.
// No directory browsing, arbitrary filesystem paths, task answers, or Repair execution.
const sampleRoot=path.join(ui,'ifc-viewer/.artifacts/sample-174');
const inspectionRoot=path.join(ui,'ifc-viewer/.artifacts/inspection/candidate-2');
const sampleRoutes=new Map([
 ['ifc-viewer/review/highlight.png',path.join(inspectionRoot,'wall-selected.png')],
 ['ifc-viewer/review/properties.png',path.join(inspectionRoot,'properties.png')],
 ['ifc-viewer/review/tree.png',path.join(inspectionRoot,'workbench.png')],
 ['ifc-viewer/review/checks.json',path.join(inspectionRoot,'checks.json')],
 ['ifc-viewer/sample.ifc',path.join(sampleRoot,'source.ifc')],
 ...['front-edges.png','side-edges.png','browser-front.png','browser-side.png','browser-native-front.png','browser-native-side.png','native-report.json','diagnostic-summary.json','parser-comparison.json','native-meshes.json.gz','model.glb','fidelity-native-front.png','fidelity-native-side.png','fidelity-workbench.png','fidelity-hidden.png','fidelity-browser-checks.json','extent-recheck.json'].map(f=>['ifc-viewer/native/'+f,path.join(sampleRoot,f)])
]);
const mime={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.wasm':'application/wasm','.ifc':'application/x-step','.png':'image/png','.json':'application/json','.glb':'model/gltf-binary'};
const apiPort=Number(process.env.TEXT2IFC_API_PORT||4180);
if(!Number.isInteger(apiPort)||apiPort<1024||apiPort>65535)throw Error('Invalid API port');
const server=http.createServer(async(req,res)=>{
  if(req.url?.startsWith('/api/')){
    // Development convenience only: one fixed loopback upstream, never a user URL.
    const host=(req.headers.host||'').split(':')[0];
    if(!['127.0.0.1','localhost'].includes(host)){res.writeHead(403);res.end();return;}
    const upstream=http.request({hostname:'127.0.0.1',port:apiPort,path:req.url,method:req.method,headers:{...req.headers,host:'127.0.0.1:'+apiPort}},response=>{res.writeHead(response.statusCode,response.headers);response.pipe(res);});
    upstream.setTimeout(120000,()=>upstream.destroy(Error('API_TIMEOUT')));
    upstream.on('error',()=>{if(!res.headersSent)res.writeHead(503,{'Content-Type':'application/json'});res.end(JSON.stringify({error:{code:'REPAIR_API_UNAVAILABLE'}}));});
    req.on('aborted',()=>upstream.destroy());req.pipe(upstream);return;
  }
  if(req.method!=='GET'&&req.method!=='HEAD'){res.writeHead(405);res.end();return;}
  let rel;try{rel=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname).replace(/^\//,'');}catch{res.writeHead(400);res.end();return;}
  if(rel==='health'){
    res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});
    res.end(JSON.stringify({service:'text2IFC-local-viewer',platform:process.platform,pid:process.pid,instance:process.env.IFC_VIEWER_INSTANCE||'foreground',port,repairEnabled:false}));return;
  }
  if(!rel||rel==='ifc-viewer'){
    const query=new URL(req.url,'http://127.0.0.1').search;
    res.writeHead(302,{Location:query?'/ifc-viewer/'+query:viewerEntry(hasLocalSample(path.join(ui,'ifc-viewer')))});res.end();return;
  }
  if(rel==='ifc-viewer/')rel+='index.html';
  if(!allowed.has(rel)&&!sampleRoutes.has(rel)){res.writeHead(404);res.end('Not found');return;}
  try{const data=await fs.readFile(sampleRoutes.get(rel)||path.join(ui,rel));res.writeHead(200,{'Content-Type':rel.endsWith('.json.gz')?'application/json':mime[path.extname(rel)],...(rel.endsWith('.json.gz')?{'Content-Encoding':'gzip'}:{}),'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(req.method==='HEAD'?undefined:data);}catch{res.writeHead(404);res.end('Missing resource: run node ui/ifc-viewer/prepare.mjs');}
});
server.on('error',e=>{console.error(e.message);process.exitCode=1;});
server.listen(port,'127.0.0.1',()=>console.log(`Real IFC viewer: http://127.0.0.1:${port}/ifc-viewer/\nChoose the source IFC locally. No Repair or model calls. Ctrl+C to stop.`));
process.on('SIGINT',()=>server.close(()=>process.exit(0)));
