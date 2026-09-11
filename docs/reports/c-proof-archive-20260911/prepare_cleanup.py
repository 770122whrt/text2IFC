"""Verify every retained byte and freeze exact source-directory deletion scope."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
from scripts.proof.package import contained, verify_bundle
from text2ifc_agent.artifact_scan import scan_path

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def write(p, d):
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write('\n')

archive = ROOT/'dataset/processed/experiments'
proof = ROOT/'dataset/processed/proof/generation/phase6.6/c-shaped-teaching-20260911'
bundles = [(archive,b) for b in read(archive/'c-token-archive-20260911.json')['bundles']]
bundles += [(proof,b) for b in read(proof/'manifest.json')['legacy_bundles']]
targets = []
for destination, bundle in bundles:
    verified = verify_bundle(destination,bundle)
    source = contained(ROOT,bundle['old_root'])
    assert source.parent == ROOT/'dataset/processed/ifc-presentation-validation'
    records = []
    bound = {}
    for e in bundle['entries']:
        rel = e['legacy_path']
        if source.name == 'c-shaped-current-provider-20260911' and rel == 'generated.ifc': rel='generated-C.ifc'
        bound[rel] = e
    for item in sorted(source.rglob('*')):
        rel = item.relative_to(source).as_posix()
        contained(source,rel)
        if not item.is_file(): continue
        row = dict(relative_path=rel,sha256=sha(item),size_bytes=item.stat().st_size)
        if rel in bound:
            e=bound[rel]
            assert row['sha256']==e['sha256'] and row['size_bytes']==e['size_bytes'],item
            row['retained_at']=(destination/e['path']).relative_to(ROOT).as_posix()
            row['action']='remove_duplicate_after_verified_archive'
        else:
            assert '__pycache__' in item.parts and item.suffix=='.pyc',item
            row['retained_at']=None
            row['action']='remove_rebuildable_python_bytecode'
        records.append(row)
    assert set(bound) <= {r['relative_path'] for r in records}
    targets.append(dict(path=source.relative_to(ROOT).as_posix(),absolute_path=str(source.resolve()),
        retained_root=destination.relative_to(ROOT).as_posix(),files=records,
        file_count=len(records),bytes=sum(r['size_bytes'] for r in records),archive_verified=verified))

scan=scan_path(archive)
assert scan['finding_count']==0,scan
write(HERE/'deletion-proposal.json',dict(status='ready_after_copy_verification',
    user_authorization='整理完后对于run目录进行删除；继续进行 整理完与我汇报',
    scope='Only these 10 C/token source collections; all evidence retained except rebuildable bytecode.',
    targets=targets,source_count=len(targets),file_count=sum(t['file_count'] for t in targets),
    bytes=sum(t['bytes'] for t in targets),secret_scan=scan))
print(json.dumps(dict(targets=len(targets),files=sum(t['file_count'] for t in targets),bytes=sum(t['bytes'] for t in targets),secret_scan_findings=scan['finding_count'])))
