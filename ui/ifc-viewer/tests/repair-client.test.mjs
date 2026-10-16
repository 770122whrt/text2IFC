import test from 'node:test';
import assert from 'node:assert/strict';
import {RepairClient,requestSignature,preparePayload} from '../repair-client.mjs';

test('selection payload retains the exact user text and source-bound identities',()=>{
 const s={version:'source-3',text:' 在此加窗\nKeep original ',primary:{id:12,guid:'wall-guid',version:'source-3'},auxiliary:{id:17,guid:'window-guid',version:'source-3'}};
 const p=preparePayload(s,'input-id','zh');assert.equal(p.user_text,s.text);assert.equal(p.primary.step_id,12);assert.equal(p.auxiliary.global_id,'window-guid');assert.equal(p.view_version,'source-3');
 assert.throws(()=>preparePayload({...s,primary:{...s.primary,version:'old'}},'input-id','en'),/SELECTION_VERSION/);
});
test('request identity ignores view language/camera but changes with text, model or references',()=>{
 const s={version:'s1',text:'x',primary:null,auxiliary:null};const key=requestSignature(s);
 assert.equal(requestSignature({...s,language:'en',camera:[1,2,3]}),key);
 for(const patch of [{text:'y'},{version:'s2'},{primary:{id:2,guid:'g',version:'s1'}}])assert.notEqual(requestSignature({...s,...patch}),key);
});
test('client calls public HTTP endpoints without invoking a CLI or model SDK',async()=>{
 const calls=[];const c=new RepairClient({fetchImpl:async(url,opts)=>{calls.push([url,opts]);return new Response(JSON.stringify({task_id:'t'}),{status:202,headers:{'Content-Type':'application/json'}});}});
 await c.start('request-id','click-once');assert.equal(calls[0][0],'/api/repair-tasks');assert.equal(calls[0][1].method,'POST');assert.deepEqual(JSON.parse(calls[0][1].body),{prepared_request_id:'request-id',client_request_id:'click-once'});
});
test('HTTP failure is explicit, never replaced by a demo success or retried silently',async()=>{
 let calls=0;const c=new RepairClient({fetchImpl:async()=>{calls++;return new Response(JSON.stringify({error:{code:'REPAIR_EXECUTION_NOT_ENABLED'}}),{status:503});}});
 await assert.rejects(c.start('r','id'),e=>e.code==='REPAIR_EXECUTION_NOT_ENABLED'&&e.status===503);assert.equal(calls,1);
});
