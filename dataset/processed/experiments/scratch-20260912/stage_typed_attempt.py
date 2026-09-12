import hashlib
import json
from pathlib import Path
import subprocess
import sys
import re

root=Path.cwd()
out=Path('dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/typed-appearance-rerun-20260910')
manifest=json.loads((out/'FILES.json').read_text(encoding='utf-8'))
expected=[]
for row in manifest['files']:
    p=out/row['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
    expected.append(p.as_posix())
expected.append((out/'FILES.json').as_posix())
if '--verify' not in sys.argv:
    assert not subprocess.check_output(['git','diff','--cached','--name-only']).strip()
    Path('.tmp/typed-attempt-pathspec.bin').write_bytes(b'\0'.join(p.encode('utf-8') for p in expected)+b'\0')
    print('Prepared explicit paths:',len(expected))
else:
    staged=subprocess.check_output(['git','diff','--cached','--name-only','-z']).decode().strip('\0').split('\0')
    assert set(staged)==set(expected), (set(staged)-set(expected),set(expected)-set(staged))
    if '--whitespace-only' not in sys.argv:
        for p in staged:
            assert subprocess.check_output(['git','show',':'+p])==(root/p).read_bytes(),p
    result=subprocess.run(['git','diff','--cached','--check'],capture_output=True)
    Path('.tmp/typed-attempt-staged-diff-check.log').write_bytes(result.stdout+result.stderr)
    findings=[]
    for line in result.stdout.decode('utf-8').splitlines():
        if ': trailing whitespace.' in line or ': new blank line at EOF.' in line:
            match=re.match(r'(.+):(\d+): ',line)
            assert match,line
            path,number=match.group(1),int(match.group(2))
            raw_line=(root/path).read_bytes().split(b'\n')[number-1]
            assert path.endswith(('.xml','.log')) or raw_line.endswith(b'\r'),line
            findings.append(line)
    assert result.returncode in (0,2)
    print(json.dumps({'staged_paths':len(staged),'all_staged_bytes_exact':True,
        'raw_trace_whitespace_preserved':len(findings),'total_bytes':sum((root/p).stat().st_size for p in staged)}))
