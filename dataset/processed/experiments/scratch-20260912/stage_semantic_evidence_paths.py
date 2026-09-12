import json
from pathlib import Path

root = Path.cwd()
base = root/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/semantic-authority-rerun-20260910'
manifest = json.loads((base/'FILES.json').read_text(encoding='utf-8'))
paths = [(base/r['path']).relative_to(root).as_posix() for r in manifest['files']]
assert all((root/p).resolve().is_relative_to(base.resolve()) for p in paths)
paths += [(base/'FILES.json').relative_to(root).as_posix(), 'docs/architecture/semantic-appearance-plan.md']
(root/'.tmp/semantic-evidence-pathspec.bin').write_bytes(('\0'.join(paths)+'\0').encode())
print(len(paths))
