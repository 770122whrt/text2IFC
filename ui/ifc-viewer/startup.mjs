/** Local launch defaults; private sample caches are optional. */
import fs from 'node:fs';
import path from 'node:path';

export function hasLocalSample(directory) {
  const sample = path.join(directory, '.artifacts', 'sample-174');
  return ['source.ifc', 'native-meshes.json.gz'].every(name => fs.existsSync(path.join(sample, name)));
}

export function viewerEntry(sampleAvailable) {
  return sampleAvailable ? '/ifc-viewer/?sample=174&engine=native&view=side' : '/ifc-viewer/';
}

export function pythonCandidates(workspace, platform, override, exists = fs.existsSync) {
  if (override) return [override];
  const local = platform === 'win32'
    ? path.join(workspace, '.venv', 'Scripts', 'python.exe')
    : path.join(workspace, '.venv', 'bin', 'python');
  const system = platform === 'win32' ? ['python', 'python3.12'] : ['python3.12', 'python.exe'];
  return exists(local) ? [local, ...system] : system;
}
