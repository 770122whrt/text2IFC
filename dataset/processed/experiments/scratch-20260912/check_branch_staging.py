import hashlib
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
prefix = 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/'
paths = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=root, text=True).splitlines()
assert len(paths) == 31 and all(p.startswith(prefix) for p in paths)
total = 0
for path in paths:
    raw = (root / path).read_bytes()
    staged = subprocess.check_output(['git', 'show', ':' + path], cwd=root)
    assert raw == staged, path
    text = raw.decode('utf-8')
    assert not re.search(r'\bsk-[A-Za-z0-9]{20,}', text), path
    assert not re.search(r'Bearer\s+[A-Za-z0-9_-]{20,}', text), path
    if path.endswith('.json'):
        json.loads(text)
    total += len(raw)
print(json.dumps({'files': len(paths), 'bytes': total, 'staged_bytes_match': True, 'credential_pattern_hits': 0}))
