/** Local static preview only; never serves the repository, credentials or Repair API. */
import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.dirname(fileURLToPath(import.meta.url));
const port=Number(process.env.UI_PREVIEW_PORT||4177);
if(!Number.isInteger(port)||port<1024||port>65535)throw Error('Invalid UI_PREVIEW_PORT');
const allowed=new Set(['index.html','styles.css','app.mjs','core.mjs','scene.mjs','vendor/plotly.min.js']);
const server=http.createServer(async(req,res)=>{
 if(req.method!=='GET'&&req.method!=='HEAD'){res.writeHead(405);res.end();return;}
 let rel;try{rel=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname).replace(/^\//,'')||'index.html';}catch{res.writeHead(400);res.end();return;}
 if(!allowed.has(rel)){res.writeHead(404);res.end('Not found');return;}
 try{const data=await readFile(path.join(root,rel));const type=rel.endsWith('.html')?'text/html; charset=utf-8':rel.endsWith('.css')?'text/css; charset=utf-8':'text/javascript; charset=utf-8';res.writeHead(200,{'Content-Type':type,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(req.method==='HEAD'?undefined:data);}
 catch{if(rel==='vendor/plotly.min.js'){res.writeHead(200,{'Content-Type':'text/javascript'});res.end('/* Optional Plotly asset absent; design-only compatibility viewer is available. */');}else{res.writeHead(404);res.end('Not found');}}
});
server.on('error',e=>{console.error('Preview server:',e.message);process.exitCode=1;});
server.listen(port,'127.0.0.1',()=>console.log(`Repair UI preview: http://127.0.0.1:${port}/\nNo IFC/Provider execution. Ctrl+C to stop.`));
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>server.close(()=>process.exit(0)));
