import hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'dataset/processed/proof/generation/phase6.6/two-storey-community-20260909'
verification=json.loads((root/'docs/reports/run-cleanup-review-20260910/two-storey-preservation.json').read_text(encoding='utf-8'))
expected=set((root/'.tmp/two-storey-preserve-pathspec.nul').read_bytes().decode().split('\0'))-{''}
expected.update(['dataset/processed/proof/README.md','dataset/processed/proof/generation/README.md','docs/reports/run-cleanup-review-20260910/two-storey-preservation.json'])
actual=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=root).decode().split('\0'))-{''}
assert actual==expected,actual^expected
entries={}
for row in subprocess.check_output(['git','ls-files','--stage','-z','--',p.relative_to(root).as_posix()],cwd=root).split(b'\0'):
    if row:
        meta,name=row.split(b'\t',1);entries[name.decode()]=meta.decode().split()[1]
lfs=0
for row in verification['files']:
    file=p/row['path'];raw=file.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    assert digest==row['sha256']
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    actual_blob=entries[file.relative_to(root).as_posix()]
    if actual_blob!=blob:
        pointer=subprocess.check_output(['git','cat-file','blob',actual_blob],cwd=root)
        assert pointer==f'version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize {len(raw)}\n'.encode(),file
        assert hashlib.sha256((root/'.git/lfs/objects'/digest[:2]/digest[2:4]/digest).read_bytes()).hexdigest()==digest
        lfs+=1
check=subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff','--cached','--check','--','dataset/processed/proof/README.md','dataset/processed/proof/generation/README.md'],cwd=root,capture_output=True)
assert check.returncode==0
print(json.dumps({'staged_paths':len(actual),'frozen_files':len(verification['files']),'lfs_objects':lfs,'status':'passed'}))
