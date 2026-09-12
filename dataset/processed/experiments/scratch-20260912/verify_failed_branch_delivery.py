import hashlib
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
base = root / 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910'
prefix = base.relative_to(root).as_posix() + '/'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((base / 'LIVE-ATTEMPT-FILES.json').read_text(encoding='utf-8'))
for row in manifest['files']:
    path = base / row['path']
    assert path.resolve().is_relative_to(base.resolve())
    assert sha(path) == row['sha256'] and path.stat().st_size == row['size_bytes'], row['path']
link_count = 0
for report in [base / 'REPORT.md', base / 'A-revise/REPORT.md', base / 'B-retain/REPORT.md']:
    for destination in re.findall(r'\]\(([^)]+)\)', report.read_text(encoding='utf-8')):
        path = (report.parent / destination.split('#')[0]).resolve()
        assert path.is_relative_to(root.resolve()) and path.exists(), destination
        link_count += 1
paths = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=root, text=True).splitlines()
assert len(paths) == 145
for path in paths:
    assert path.startswith(prefix) or path == 'docs/architecture/semantic-appearance-plan.md'
    raw = (root / path).read_bytes()
    staged = subprocess.check_output(['git', 'show', ':' + path], cwd=root)
    if path.startswith(prefix):
        assert raw == staged, path
    assert not re.search(rb'\bsk-[A-Za-z0-9]{20,}', raw), path
    assert not re.search(rb'Bearer\s+[A-Za-z0-9_-]{20,}', raw), path
print(json.dumps({'frozen_files_verified': len(manifest['files']), 'report_links_checked': link_count,
                  'staged_files_reviewed': len(paths), 'evidence_bytes_identical': True,
                  'credential_pattern_hits': 0, 'scope': 'evidence and reports only; no IFC success claim'}))
