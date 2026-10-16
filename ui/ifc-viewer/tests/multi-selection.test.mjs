import test from 'node:test';
import assert from 'node:assert/strict';
import {createState,setMode} from '../../prototype/core.mjs';
import {targetRefs,setMulti,pickTarget,removeTarget,clearTargets} from '../multi-selection.mjs';
import {requestSignature,preparePayload} from '../repair-client.mjs';

test('view clicks inspect but do not change the multiple targets',()=>{const s=createState();s.version=s.baseVersion='v';setMode(s,'select');setMulti(s,true);pickTarget(s,1);pickTarget(s,2);setMode(s,'view');pickTarget(s,3);assert.deepEqual(targetRefs(s).map(r=>r.id),[1,2]);assert.equal(s.inspected,3);});
test('multi targets toggle with clicks and do not overlap auxiliary role',()=>{const s=createState();s.version=s.baseVersion='v';setMode(s,'select');setMulti(s,true);pickTarget(s,1);pickTarget(s,2);pickTarget(s,1);assert.deepEqual(targetRefs(s).map(r=>r.id),[2]);s.pickRole='auxiliary';assert.throws(()=>pickTarget(s,2));s.pickRole='auxiliary';pickTarget(s,4);assert.equal(s.auxReference.id,4);assert.throws(()=>pickTarget(s,4));});
test('turning off multi never silently discards several targets',()=>{const s=createState();s.version=s.baseVersion='v';setMode(s,'select');setMulti(s,true);pickTarget(s,1);pickTarget(s,2);assert.throws(()=>setMulti(s,false));removeTarget(s,2);setMulti(s,false);assert.equal(s.reference.id,1);});
test('old-version viewing and explicit clearing stay separate',()=>{const s=createState();s.version=s.baseVersion='v';setMode(s,'select');setMulti(s,true);pickTarget(s,1);s.version='result';pickTarget(s,2);assert.equal(targetRefs(s).length,1);s.version='v';clearTargets(s);assert.equal(targetRefs(s).length,0);});
test('new array contract preserves all identities and invalidates after any member changes',()=>{const s={version:'v',text:'each wall',targets:[{id:1,guid:'A',version:'v'},{id:2,guid:'B',version:'v'}],primary:null,auxiliary:null};const p=preparePayload(s,'input','en');assert.equal(p.targets.length,2);assert.equal(p.primary,null);assert.notEqual(requestSignature(s),requestSignature({...s,targets:[s.targets[0]]}));assert.equal(p.user_text,s.text);});
