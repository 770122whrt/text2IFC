/** Optional: obtain one pinned, MIT-licensed browser asset. No npm/pip install or global changes. */
import {mkdir,writeFile,readFile} from 'node:fs/promises';
const url='https://cdn.plot.ly/plotly-3.3.1.min.js';
const dest=new URL('./vendor/plotly.min.js',import.meta.url);
try{const existing=await readFile(dest,'utf8');if(existing.includes('plotly.js v3.3.1')){console.log('Pinned Plotly asset already present.');process.exit(0);}}
catch(e){if(e.code!=='ENOENT')throw e;}
const response=await fetch(url,{signal:AbortSignal.timeout(60000)});
if(!response.ok)throw Error(`Asset download failed: ${response.status}`);
const code=await response.text();
if(code.length<500000||!code.slice(0,400).includes('plotly.js v3.3.1'))throw Error('Unexpected asset/version; refusing to write.');
await mkdir(new URL('./vendor/',import.meta.url),{recursive:true});
await writeFile(dest,code,{encoding:'utf8',flag:'wx'});
console.log('Prepared ui/prototype/vendor/plotly.min.js. Source: '+url);
