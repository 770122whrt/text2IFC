import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from '../vendor/three.module.js';
import {exactBounds,sourceMatches,displayMaterial} from '../display-geometry.mjs';

test('rotated asymmetric mesh is measured at vertices, not the expanded local box',()=>{
 const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute([0,0,0,2,0,0,0,1,0],3));
 const m=new T.Mesh(g);m.rotation.z=Math.PI/4;m.updateMatrixWorld(true);
 const precise=exactBounds(m);const coarse=new T.Box3().setFromObject(m);
 assert.ok(coarse.max.y-precise.max[1]>.7);
 assert.ok(Math.abs(precise.max[1]-Math.SQRT2)<1e-6);
});
test('same file length or GUID is insufficient to reuse native mesh cache',()=>{
 const a=new Uint8Array([65,66,67]);
 assert.ok(sourceMatches(a,{source_base64:'QUJD'}));
 assert.equal(sourceMatches(a,{source_base64:'QUJE'}),false);
});
test('display retains source alpha and colour bytes with an explicit sRGB convention',()=>{
 const rgba=[.823529411764706,.623529411764706,.372549019607843,.1];const m=displayMaterial(rgba);
 assert.equal(m.opacity,.1);assert.ok(m.transparent);assert.deepEqual(m.userData.sourceRGBA,rgba);
 assert.equal(m.color.getHex(),0xd29f5f);assert.equal(m.side,T.FrontSide);
});
