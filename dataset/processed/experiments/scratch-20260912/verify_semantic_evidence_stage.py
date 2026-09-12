import hashlib
import io
from pathlib import Path
import subprocess

paths = Path('.tmp/semantic-evidence-pathspec.bin').read_bytes().decode().strip('\0').split('\0')
actual = subprocess.check_output(['git','diff','--cached','--name-only','-z']).decode().strip('\0').split('\0')
assert set(actual) == set(paths)
payload = subprocess.check_output(['git','cat-file','--batch'], input=('\n'.join(':'+p for p in paths)+'\n').encode())
stream = io.BytesIO(payload)
for path in paths:
    header = stream.readline().decode().split()
    assert header[1] == 'blob', (path,header)
    blob = stream.read(int(header[2]))
    assert stream.read(1) == b'\n'
    disk = Path(path).read_bytes()
    if path == 'docs/architecture/semantic-appearance-plan.md':
        assert blob == disk.replace(b'\r\n', b'\n'), path
    else:
        assert hashlib.sha256(blob).digest() == hashlib.sha256(disk).digest(), path
check = subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff','--cached','--check'],capture_output=True)
Path('.tmp/semantic-evidence-whitespace.log').write_bytes(check.stdout+check.stderr)
lines = check.stdout.decode().splitlines()
issues = [line for line in lines if ': trailing whitespace.' in line]
assert check.returncode == 0 or (issues and all(('.xml:' in line or '.log:' in line) for line in issues)), lines[:10]
print('STAGED exact paths and byte hashes:',len(paths),'frozen traceback whitespace:',len(issues))
