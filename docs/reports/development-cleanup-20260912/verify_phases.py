"""Verify new compressed phase bindings; no IFC regeneration or curator run."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[3]
REPORT = Path(__file__).resolve().parent
OUT = ROOT/'dataset/processed/experiments/phase-history-20260912'


def main():
    document = json.loads((OUT/'manifest.json').read_text('utf8'))
    plan = json.loads((REPORT/'phase-inventory-combined.json').read_text('utf8'))
    assert document['status'] == 'archived_not_deleted' and not document['findings']
    assert len(document['bundles']) == len(plan['bundles'])
    unique = {}
    sources = {b['old_root']: b for b in plan['bundles']}
    for b in document['bundles']:
        actual = b['entries']+b['excluded_caches']
        assert {e['legacy_path']:e['size_bytes'] for e in actual} == {e['legacy_path']:e['size_bytes'] for e in sources[b['old_root']]['files']}
        for e in b['entries']:
            key = (e['retained_path'], e.get('archive_member'))
            if key in unique:
                assert unique[key]['sha256'] == e['sha256']
            unique[key] = e
    containers = {}
    try:
        for c in document['archives']:
            p = ROOT/c['path']
            with p.open('rb') as f:
                assert hashlib.file_digest(f, 'sha256').hexdigest() == c['sha256']
            assert p.stat().st_size == c['size_bytes']
            containers[c['path']] = zipfile.ZipFile(p)
        tracked = set(subprocess.check_output(['git','ls-files','-z'], cwd=ROOT).decode().split('\0'))
        proof_files = 0
        for (name, member), e in unique.items():
            if member:
                z = containers[name]
                assert z.getinfo(member).file_size == e['size_bytes']
                with z.open(member) as f:
                    assert hashlib.file_digest(f, 'sha256').hexdigest() == e['sha256']
            else:
                p = ROOT/name
                assert name in tracked, f'Reused Proof must already be committed: {name}'
                assert p.stat().st_size == e['size_bytes']
                with p.open('rb') as f:
                    assert hashlib.file_digest(f, 'sha256').hexdigest() == e['sha256']
                proof_files += 1
        for name, z in containers.items():
            assert set(z.namelist()) == {member for path,member in unique if path == name}
        result = dict(status='passed', roots=len(document['bundles']), source_files=sum(len(b['files']) for b in plan['bundles']),
            source_bytes=sum(e['size_bytes'] for b in plan['bundles'] for e in b['files']),
            unique_retained_files=len(unique), reused_proof_files=proof_files,
            zip_files=len(containers), zip_bytes=sum(e['size_bytes'] for e in document['archives']),
            links=sum(len(b['links']) for b in document['bundles']), findings=document['findings'], provider_calls=0)
        (REPORT/'phase-archive-verification.json').write_text(json.dumps(result, indent=2)+'\n', 'utf8')
        print(json.dumps(result))
    finally:
        for z in containers.values():
            z.close()


if __name__ == '__main__':
    main()
