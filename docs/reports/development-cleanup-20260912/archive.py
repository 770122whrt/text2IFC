"""One-time archive of retired presentation/development workspaces; no deletion."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.proof.package import contained

OUT = ROOT/'dataset/processed/experiments'
REPORT = Path(__file__).resolve().parent
PRESENTATION = ROOT/'dataset/processed/ifc-presentation-validation'
NAMES = ['deliverables', 'live-a1-20260904', 'live-semantic-20260908-01',
    'offline-20260904T0431', 'phase12-preflight-20260904', 'pipeline-gate-routing-20260909',
    'pipeline-opening-binding-20260909', 'preflight-20260904T0431', 'repair-mixed-20260905',
    'restoration-20260904', 'semantic-appearance-20260908', 'semantic-appearance-20260908-02',
    'semantic-appearance-20260908-final', 'success-cases',
    'three-storey-clarification-branches-20260910', 'three-storey-human-review-20260909',
    'two-storey-human-review-20260908']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, data):
    with p.open('x', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    proof_paths = [
        'dataset/processed/proof/generation/phase6.6/three-storey-clarification-ab-20260910/manifest.json',
        'dataset/processed/proof/repair/phase12/presentation-cases/manifest.json']
    saved = {}
    for name in proof_paths:
        manifest = ROOT/name
        for b in json.loads(manifest.read_text(encoding='utf8'))['legacy_bundles']:
            for e in b['entries']:
                source = (ROOT/b['old_root']/e['legacy_path']).resolve()
                retained = manifest.parent/e['path']
                saved[source] = (retained, e)
    bundles = []
    for name in NAMES:
        source = PRESENTATION/name
        entries, caches = [], []
        assert source.is_dir(), source
        assert not (OUT/name).exists(), 'Do not overwrite an existing archive.'
        for item in sorted(source.rglob('*')):
            rel = item.relative_to(source).as_posix()
            contained(source, rel)
            if not item.is_file():
                continue
            record = dict(legacy_path=rel, size_bytes=item.stat().st_size, sha256=sha(item))
            if '__pycache__' in item.parts or '.pytest_cache' in item.parts:
                caches.append(record)
                continue
            prior = saved.get(item.resolve())
            if prior and prior[1]['sha256'] == record['sha256'] and sha(prior[0]) == record['sha256']:
                retained = prior[0]
                action = 'reuse_existing_proof'
            else:
                retained = OUT/name/rel
                retained.parent.mkdir(parents=True, exist_ok=True)
                with item.open('rb') as src, retained.open('xb') as dst:
                    shutil.copyfileobj(src, dst)
                assert sha(retained) == record['sha256']
                action = 'archive_development_history'
            entries.append({**record, 'retained_path': retained.relative_to(ROOT).as_posix(), 'action': action})
        bundles.append(dict(old_root=source.relative_to(ROOT).as_posix(), entries=entries, excluded_caches=caches))
        print(name, len(entries), 'preserved', len(caches), 'caches', flush=True)
    write(OUT/'development-retirement-20260912.json', dict(status='archived_not_deleted',
        authorization='User approved deleting listed directories and equivalent completed example/development workspaces on 2026-09-12.',
        frozen_proof_bytes_changed=False, bundles=bundles))
    print(json.dumps({'files':sum(len(b['entries']) for b in bundles),
        'bytes':sum(e['size_bytes'] for b in bundles for e in b['entries']),
        'reused_proof_files':sum(e['action']=='reuse_existing_proof' for b in bundles for e in b['entries'])}))


if __name__ == '__main__':
    main()
