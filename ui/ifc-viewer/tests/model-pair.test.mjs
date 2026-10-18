import test from 'node:test';
import assert from 'node:assert/strict';
import {pairOffset,findByGuid,validateResultRole} from '../model-pair.mjs';
test('both models use the original offset, not separate automatic centering',()=>{assert.deepEqual(pairOffset([10,2,-5],[99,20,50]),[10,2,-5]);});
test('object correspondence uses unique GlobalId, never a repeated name or STEP id',()=>{
 const records=new Map([[11,{id:11,guid:'A',name:'same'}],[12,{id:12,guid:'B',name:'same'}]]);assert.equal(findByGuid(records,'A'),11);assert.equal(findByGuid(records,'missing'),null);records.set(13,{id:13,guid:'A'});assert.equal(findByGuid(records,'A'),null);
});
test('unpublished or unrelated files cannot enter the successful after view',()=>{
 assert.throws(()=>validateResultRole({role:'successful_ifc'},{successful_artifact_publishable:false}));
 assert.equal(validateResultRole({role:'diagnostic_candidate'},{successful_artifact_publishable:false}),'diagnostic');
 assert.equal(validateResultRole({role:'successful_ifc'},{successful_artifact_publishable:true}),'success');
 assert.throws(()=>validateResultRole({role:'provider_record'},{}));
});
