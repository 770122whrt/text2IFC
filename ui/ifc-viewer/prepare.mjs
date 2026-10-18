/** Prepare public, version-checked browser assets locally. No IFC upload, npm install or credentials. */
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {inflateRawSync} from 'node:zlib';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const here=path.dirname(fileURLToPath(import.meta.url));
const assets=[
  ['https://thatopen.github.io/engine_web-ifc/build.zip','0e863ef22a708478613884cdee6e40a5f97be7b7906e288a016919759ec1f9bf'],
  ['https://thatopen.github.io/engine_web-ifc/demo/web-ifc-viewer.js','934b38af1d956af8ba3a2d2dba475d3bc445b4f0eafca85e43440b2a57417226'],
];
const digest=b=>createHash('sha256').update(b).digest('hex');
async function get(url,expected){
  const response=await fetch(url,{signal:AbortSignal.timeout(90000)});
  if(!response.ok)throw Error(`Resource unavailable: HTTP ${response.status}`);
  const bytes=Buffer.from(await response.arrayBuffer());
  if(bytes.length>40*1048576||digest(bytes)!==expected)throw Error('Upstream artifact changed; refusing a silent version change. Use the supplied offline resource package or review a new locked build.');
  return bytes;
}
function unzipFile(zip,wanted){
  let e=-1;for(let i=zip.length-22;i>=Math.max(0,zip.length-65557);i--)if(zip.readUInt32LE(i)===0x06054b50){e=i;break;}
  if(e<0)throw Error('ZIP end record missing');let cursor=zip.readUInt32LE(e+16),entries=zip.readUInt16LE(e+10);
  for(let i=0;i<entries;i++){
    if(zip.readUInt32LE(cursor)!==0x02014b50)throw Error('Bad ZIP directory');
    const compression=zip.readUInt16LE(cursor+10),size=zip.readUInt32LE(cursor+20),unpacked=zip.readUInt32LE(cursor+24),n=zip.readUInt16LE(cursor+28),x=zip.readUInt16LE(cursor+30),c=zip.readUInt16LE(cursor+32),off=zip.readUInt32LE(cursor+42),name=zip.subarray(cursor+46,cursor+46+n).toString('utf8');
    if(name===wanted||name==='dist/'+wanted){
      if(unpacked>12*1048576||zip.readUInt32LE(off)!==0x04034b50)throw Error('Invalid asset size/header');
      const start=off+30+zip.readUInt16LE(off+26)+zip.readUInt16LE(off+28),packed=zip.subarray(start,start+size);
      const data=compression===0?packed:compression===8?inflateRawSync(packed,{maxOutputLength:12*1048576}):null;
      if(!data||data.length!==unpacked)throw Error('Invalid asset data');return data;
    }
    cursor+=46+n+x+c;
  }
  throw Error(`Asset not in ZIP: ${wanted}`);
}
function between(s,a,b){const start=s.indexOf(a),end=s.indexOf(b,start+1);if(start<0||end<start)throw Error('Official bundle structure changed');return s.slice(start,end);}
const [zip,bundleBytes]=await Promise.all(assets.map(([u,h])=>get(u,h)));
const bundle=bundleBytes.toString('utf8');
// Extract unchanged upstream library sections, not the demo application or its TypeScript evaluator.
const helper=bundle.slice(0,bundle.indexOf('  // ../../dist/web-ifc-api.js'));
if(!helper.startsWith('"use strict";')||helper.length>10000)throw Error('Unexpected bundle prologue');
const library=between(bundle,'  // ../../node_modules/three/build/three.core.js','  // ../../node_modules/three/examples/jsm/utils/BufferGeometryUtils.js');
const orbit=between(bundle,'  // ../../node_modules/three/examples/jsm/controls/OrbitControls.js','  // web-ifc-scene.ts');
const bridge='\ninit_three_module(); init_OrbitControls();\nglobalThis.THREE={REVISION,MOUSE,Scene,Group,Mesh,MeshPhongMaterial,MeshBasicMaterial,BufferGeometry,BufferAttribute,Vector2,Vector3,Matrix4,Box3,Ray,Color,AmbientLight,DirectionalLight,OrthographicCamera,PerspectiveCamera,WebGLRenderer,OrbitControls,DoubleSide,SRGBColorSpace,LinearSRGBColorSpace,NoToneMapping,ColorManagement};\n})();\n';
const notice='/*! Three.js r186, Copyright Three.js authors, MIT. Repackaged from ThatOpen official demo a7b53a8; original library code unchanged. */\n';
const files={
  'web-ifc-api-iife.js':unzipFile(zip,'web-ifc-api-iife.js'),
  'web-ifc.wasm':unzipFile(zip,'web-ifc.wasm'),
  'WEB-IFC-LICENSE.md':unzipFile(zip,'LICENSE.md'),
  'three-runtime.js':Buffer.from(notice+helper+library+orbit+bridge),
};
const directory=path.join(here,'vendor');await fs.mkdir(directory,{recursive:true});
for(const [name,data] of Object.entries(files)){
  const file=path.join(directory,name);let exists;try{exists=await fs.readFile(file);}catch(e){if(e.code!=='ENOENT')throw e;}
  if(exists&&!exists.equals(data))throw Error(`Existing different asset: ${name}; not overwritten`);
  if(!exists)await fs.writeFile(file,data,{flag:'wx'});
}
console.log(JSON.stringify({prepared:Object.keys(files),source:'ThatOpen official workflow 37911573838',commit:'a7b53a8b41376993fb2f70cfe85e7a293d43348c',model_uploaded:false,global_install:false}));
