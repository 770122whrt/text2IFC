import test from 'node:test';
import assert from 'node:assert/strict';
import {mergeByKey,restorableTaskId,candidateAnswerKind} from '../repair-panel.mjs';
test('incremental events are deduplicated and ordered by their own sequence',()=>{
 assert.deepEqual(mergeByKey([{event_seq:1},{event_seq:2}],[{event_seq:2},{event_seq:3}],'event_seq').map(x=>x.event_seq),[1,2,3]);
});
test('only an actual task id can restore a task',()=>{
 assert.equal(restorableTaskId('task-'+'a'.repeat(32)),'task-'+'a'.repeat(32));assert.equal(restorableTaskId('../secret'),null);assert.equal(restorableTaskId('https://remote/task-x'),null);
});
test('candidate actions follow the backend modes, not arbitrary UI guesses',()=>{
 assert.equal(candidateAnswerKind(['add_detail']),null);assert.equal(candidateAnswerKind(['select_candidate']),'select_candidate');assert.equal(candidateAnswerKind(['authorize_prototype','cancel']),'authorize_prototype');
});
