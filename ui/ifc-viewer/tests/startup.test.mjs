import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import {viewerEntry, pythonCandidates} from '../startup.mjs';

test('a checkout without local sample data opens the file-selection workbench', () => {
  assert.equal(viewerEntry(false), '/ifc-viewer/');
  assert.equal(viewerEntry(true), '/ifc-viewer/?sample=174&engine=native&view=side');
});

test('the workspace virtual environment takes precedence over system Python', () => {
  const workspace = path.resolve('checkout');
  const local = path.join(workspace, '.venv', 'Scripts', 'python.exe');
  assert.equal(pythonCandidates(workspace, 'win32', null, file => file === local)[0], local);
  assert.deepEqual(pythonCandidates(workspace, 'win32', null, () => false), ['python', 'python3.12']);
  assert.equal(pythonCandidates(workspace, 'linux', null, () => true)[0], path.join(workspace, '.venv', 'bin', 'python'));
  assert.deepEqual(pythonCandidates(workspace, 'win32', 'chosen-python', () => true), ['chosen-python']);
});
