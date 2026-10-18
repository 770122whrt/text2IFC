import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from '../vendor/three.module.js';
import {fitVisible,checkIfcBytes,loadMessage} from '../display-geometry.mjs';

test('fit retains the current viewing direction instead of jumping to a preset',()=>{
 const camera=new T.OrthographicCamera(-2,2,2,-2,.01,1000);
 camera.position.set(20,30,40);camera.up.set(0,1,0);
 const controls={target:new T.Vector3(2,1,-1),update(){}};
 camera.lookAt(controls.target);const direction=camera.position.clone().sub(controls.target).normalize();
 const group=new T.Group();group.add(new T.Mesh(new T.BoxGeometry(10,20,6)));group.position.set(3,-2,1);
 assert.equal(fitVisible(T,camera,controls,[group],16/9),true);
 assert.ok(camera.position.clone().sub(controls.target).normalize().distanceTo(direction)<1e-12);
 assert.equal(camera.zoom,1);assert.ok(camera.far>camera.near);
});
test('fit excludes hidden objects and does nothing if everything is hidden',()=>{
 const camera=new T.OrthographicCamera(-2,2,2,-2,.01,1000);camera.position.set(0,0,100);
 const controls={target:new T.Vector3(),update(){}};const group=new T.Group();group.visible=false;
 const before=camera.position.toArray();assert.equal(fitVisible(T,camera,controls,[group],1),false);
 assert.deepEqual(camera.position.toArray(),before);
});
test('reject LFS pointer or non-IFC bytes without opening a model',()=>{
 assert.throws(()=>checkIfcBytes(new TextEncoder().encode('version https://git-lfs.github.com/spec/v1')),/LFS/);
 assert.throws(()=>checkIfcBytes(new TextEncoder().encode('not an IFC')),/IFC/);
 assert.equal(checkIfcBytes(new TextEncoder().encode("ISO-10303-21; HEADER; FILE_SCHEMA(('IFC2X3')); ENDSEC; DATA;")),'IFC2X3');
});
test('missing geometry and parser diagnostics never read as an unqualified success',()=>{
 assert.equal(loadMessage({rendered:10,expected:11,missing:[7]},0).level,'partial');
 assert.equal(loadMessage({rendered:11,expected:11,missing:[]},2).level,'warning');
 assert.equal(loadMessage({rendered:11,expected:11,missing:[]},0).level,'ready');
});
