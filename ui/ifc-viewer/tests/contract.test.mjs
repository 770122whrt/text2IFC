import test from 'node:test';
import assert from 'node:assert/strict';
import {coverage, validReference, sourceLabel, compatibleFrame} from '../model-contract.mjs';

test('missing representation does not count as visible mesh obligation', () => assert.equal(coverage([{id:1,type:'IfcBuildingStorey',representation:false}],new Set()).expected,0));
test('opening and space are not solid missing objects', () => assert.equal(coverage([{id:1,type:'IfcOpeningElement',representation:true},{id:2,type:'IfcSpace',representation:true}],new Set()).expected,0));
test('physical object without triangles remains missing', () => assert.deepEqual(coverage([{id:3,type:'IfcWindow',representation:true}],new Set()).missing,[3]));
test('all physical classes count, not only repair classes', () => assert.equal(coverage([{id:5,type:'IfcFlowTerminal',representation:true}],new Set([5])).rendered,1));
test('reference resolves in exact model version', () => {
  assert.equal(validReference({id:2,version:'a'},'b',new Map([[2,{}]])),false);
  assert.equal(validReference({id:2,version:'a'},'a',new Map([[2,{}]])),true);
});
test('missing names use explicit type/id labels', () => assert.equal(sourceLabel({id:20,type:'IfcWall',name:null}),'IfcWall #20（未命名）'));
test('frame requires finite ordered bounds with positive extent', () => {
  assert.equal(compatibleFrame({min:[0,0,0],max:[1,2,3]}),true);
  assert.equal(compatibleFrame({min:[0,0,0],max:[NaN,2,3]}),false);
  assert.equal(compatibleFrame({min:[2,0,0],max:[1,2,3]}),false);
});
