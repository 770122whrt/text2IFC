import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/c-shaped-brief-debug-20260910'
expected=set((ROOT/'.tmp/brief-debug-pathspec.nul').read_bytes().decode().split('\0'))-{''}

actual=set(subprocess.check_output(['git','diff','--cached','--no-renames','--name-only','-z'],cwd=ROOT).decode().split('\0'))-{''}
assert actual==expected,dict(extra=sorted(actual-expected),missing=sorted(expected-actual))
entries={}
for row in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).split(b'\0'):
    if row:
        meta,path=row.split(b'\t',1)
        entries[path.decode()]=meta.decode().split()[1]
frozen=json.loads((OUT/'FILES.json').read_text(encoding='utf-8'))['files']
lfs_count=0
for row in [*frozen,{'path':'FILES.json'}]:
    p=OUT/row['path'];raw=p.read_bytes()
    if 'sha256' in row:assert hashlib.sha256(raw).hexdigest()==row['sha256'],p
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    staged_blob=entries[p.relative_to(ROOT).as_posix()]
    if staged_blob!=blob:
        pointer=subprocess.check_output(['git','cat-file','blob',staged_blob],cwd=ROOT)
        digest=hashlib.sha256(raw).hexdigest()
        assert pointer==f'version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize {len(raw)}\n'.encode(),p
        local=ROOT/'.git/lfs/objects'/digest[:2]/digest[2:4]/digest
        assert hashlib.sha256(local.read_bytes()).hexdigest()==digest,p
        lfs_count+=1
authored=[p for p in actual if Path(p).suffix in ('.md','.py')]
check=subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff','--cached','--check','--',*sorted(authored)],cwd=ROOT,capture_output=True)
assert check.returncode==0,check.stdout.decode(errors='replace')[:2000]
result=dict(status='passed',exact_staged_paths=len(actual),frozen_blobs_or_lfs_objects_exact=len(frozen)+1,lfs_objects_verified=lfs_count,
    authored_whitespace_checked=len(authored),raw_evidence='Byte-verified; original logs/XML/prompts not rewritten for formatting.')
(ROOT/'.tmp/brief-debug-staged-review.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))


