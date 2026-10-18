import test from 'node:test';
import assert from 'node:assert/strict';
import * as core from '../core.mjs';

// The visible card must describe the binding, not just the toolbar mode.
test('switching to select cannot label another inspected object as the reference', () => {
  const s=core.createState();
  core.setMode(s,'select'); core.inspect(s,'wall');
  core.setMode(s,'view'); core.inspect(s,'column');
  core.setMode(s,'select');
  assert.equal(s.reference.id,'wall');
  assert.equal(core.selectionRole(s),'inspection');
});
test('removing a reference leaves inspection without an attached-reference label', () => {
  const s=core.createState(); core.setMode(s,'select'); core.inspect(s,'wall');
  core.clearReference(s);
  assert.equal(s.inspected,'wall');
  assert.equal(core.selectionRole(s),'inspection');
});
test('an explicitly selected object is a reference, including in view mode', () => {
  const s=core.createState(); core.setMode(s,'select'); core.inspect(s,'wall');
  assert.equal(core.selectionRole(s),'reference');
  core.setMode(s,'view');
  assert.equal(core.selectionRole(s),'reference');
});
test('same id in another model version is not the attached reference', () => {
  const s=core.createState(); core.setMode(s,'select'); core.inspect(s,'wall');
  core.setViewVersion(s,'after',true);
  assert.equal(core.selectionRole(s),'inspection');
});
test('no inspected object has no selection role', () => {
  assert.equal(core.selectionRole(core.createState()),'none');
});
