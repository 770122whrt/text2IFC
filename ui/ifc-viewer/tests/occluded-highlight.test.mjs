import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from '../vendor/three.module.js';
import {SelectionHighlighter} from '../selection-highlight.mjs';

function fixture(){const group=new T.Group();for(let i=0;i<2;i++){const mesh=new T.Mesh(new T.BoxGeometry(1,2,1),new T.MeshBasicMaterial({color:0x777777}));mesh.position.x=i*2;mesh.userData.expressID=42;group.add(mesh);}return group;}
test('through highlight covers every submesh without editing the source geometry',()=>{
 const group=fixture(),meshes=[...group.children],source=meshes.map(m=>m.geometry.attributes.position.array.slice()),materials=meshes.map(m=>m.material);
 const h=new SelectionHighlighter({through:true});h.select(group);
 assert.equal(h.saved.length,2);assert.equal(h.overlays.filter(x=>x.isMesh).length,2);
 for(const overlay of h.overlays){assert.equal(overlay.material.depthFunc,T.GreaterDepth);assert.equal(overlay.material.depthWrite,false);assert.equal(overlay.userData.selectionOverlay,true);const hits=[];overlay.raycast({},hits);assert.deepEqual(hits,[]);}
 meshes.forEach((m,i)=>assert.deepEqual(m.geometry.attributes.position.array,source[i]));
 h.clear();assert.equal(h.overlays.length,0);meshes.forEach((m,i)=>assert.equal(m.material,materials[i]));
});
test('ordinary depth highlight and explicit visibility remain separate from through mode',()=>{
 const group=fixture(),h=new SelectionHighlighter();h.select(group);
 assert.equal(h.saved[0].mesh.material.depthTest,true);assert.ok(h.overlays.every(x=>!x.visible));
 h.setThrough(true);assert.ok(h.overlays.every(x=>x.visible));group.visible=false;
 assert.equal(group.visible,false);h.setThrough(false);assert.ok(h.overlays.every(x=>!x.visible));assert.equal(group.visible,false);
 h.clear();assert.equal(group.visible,false);
});
test('selection changes remove old overlays and never dispose shared source geometry',()=>{
 const a=fixture(),b=fixture(),h=new SelectionHighlighter({through:true});let disposed=0;a.children[0].geometry.addEventListener('dispose',()=>disposed++);
 h.select(a);h.select(b);assert.equal(disposed,0);assert.equal(a.children[0].children.length,0);assert.equal(h.group,b);h.clear();
});
