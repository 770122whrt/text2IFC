"""One-time, offline, byte-preserving courtyard archive. Never deletes sources."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.proof.package import contained, verify_bundle

OUT = ROOT / 'dataset/processed/proof/generation/phase6.6/courtyard-library-20260912'
REPORT = Path(__file__).resolve().parent
SOURCES = {
    'v1': 'courtyard-library-20260912',
    'v2': 'courtyard-library-open-court-20260912',
    'concept': 'courtyard-library-concept-20260909',
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    assert not OUT.exists(), 'Archive already exists: inspect it instead of overwriting.'
    bundles, retirement = [], []
    for key, name in SOURCES.items():
        source = ROOT / 'dataset/processed/ifc-presentation-validation' / name
        entries, excluded = [], []
        for item in sorted(source.rglob('*')):
            relative = item.relative_to(source).as_posix()
            contained(source, relative)
            if not item.is_file():
                continue
            record = {'legacy_path': relative, 'sha256': sha(item), 'size_bytes': item.stat().st_size}
            if '__pycache__' in item.parts or '.pytest_cache' in item.parts:
                excluded.append({**record, 'reason': 'rebuildable Python/pytest cache; not run evidence'})
                continue
            destination = f'evidence/{key}/{relative}'
            target = contained(OUT, destination)
            target.parent.mkdir(parents=True, exist_ok=True)
            with item.open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst)
            entries.append({**record, 'path': destination})
        bundle = {'id': key, 'old_root': source.as_posix(), 'entries': entries}
        verify_bundle(OUT, bundle)
        bundles.append(bundle)
        retirement.append({'path': source.as_posix(), 'action': 'retire_after_backup_and_approval',
            'bundle': key, 'archived_files': len(entries), 'archived_bytes': sum(e['size_bytes'] for e in entries),
            'excluded_cache_files': excluded})

    cases = []
    specs = [
        ('open-court-v2', 'v2', 'accepted', 'accepted',
         'rerun-03/live-run/runs/ce8116ce095acdcf/acceptance-metrics.json', {
            'request.txt': 'rerun-03/request.txt', 'conversation.json': 'rerun-03/conversation.json',
            'generated.ifc': 'rerun-03/generated-open-court.ifc',
            'model.json': 'rerun-03/live-run/runs/ce8116ce095acdcf/generator/candidate.json',
            'independent-ifc-check.json': 'rerun-03/independent-final-v3.json',
            'usage-summary.json': 'rerun-03/review-status.json'}, 'rerun-03/views-final'),
        ('reference-v1', 'v1', 'historical_reference', 'not_accepted',
         'continuation-01/live-run/final-acceptance/acceptance-metrics.json', {
            'request.txt': 'request.txt',
            'generated.ifc': 'continuation-01/live-run/final-acceptance/output.ifc',
            'model.json': 'continuation-01/live-run/candidate.json',
            'independent-ifc-check.json': 'continuation-01/final-review/check_ifc.json',
            'part-colours-check.json': 'continuation-01/final-review/check_part_colours.json'},
         'continuation-01/final-review/views'),
    ]
    for case_id, key, status, human, authority, paths, view_root in specs:
        bundle = next(b for b in bundles if b['id'] == key)
        entries = {e['legacy_path']: e for e in bundle['entries']}
        paths.update({'views/' + p[len(view_root)+1:]: p for p in entries if p.startswith(view_root + '/')})
        artifacts = {}
        for name, old in paths.items():
            e = entries[old]
            dest = contained(OUT, case_id + '/' + name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(contained(OUT, e['path']), dest)
            artifacts[name] = {k: e[k] for k in ('sha256', 'size_bytes')}
            artifacts[name]['source'] = e['path']
        case = dict(case_id=case_id, path=case_id, status=status, outcome='generated',
            human_review_status=human, machine_status='compiled_and_audit_accepted',
            evidence_mode='live_fresh_generation' if key == 'v2' else 'live_generation_with_deterministic_recovery_and_audit_continuation',
            full_fresh_provider_loop=key == 'v2',
            authority=f'evidence/{key}/{authority}', original_role=None, ifccompare='N/A: Generation', artifacts=artifacts)
        if key == 'v2':
            case.update(run_id='ce8116ce095acdcf', provider_calls=3, human_review_date='2026-09-12')
        cases.append(case)
        write(OUT / case_id / 'FILES.json', {'schema_version': 'text2ifc/package-artifacts/0.1', 'artifacts': artifacts})

    write(OUT / 'manifest.json', dict(schema_version='text2ifc/workflow-proof-package/0.1',
        collection_id=OUT.name, workflow='generation', status='accepted_with_historical_reference',
        human_review_status='accepted_v2_only', human_review_date='2026-09-12',
        accepted_case_count=1, historical_reference_count=1,
        scope='V2 human-accepted modeling Proof. V1 historical design reference; no engineering certification.',
        cases=cases, legacy_bundles=bundles))
    write(OUT / 'human-acceptance.json', dict(date='2026-09-12', timezone='Asia/Shanghai',
        source='User message in the current task', case_id='open-court-v2',
        user_statement='人工检验完毕是可行的合理的proof。',
        ifc_sha256=cases[0]['artifacts']['generated.ifc']['sha256'],
        human_review_status='accepted', scope='Latest open courtyard V2; V1 retained as historical reference.',
        previous_snapshot='evidence/v2/rerun-03/review-status.json',
        frozen_evidence_rewritten=False))
    write(REPORT / 'retirement.json', dict(status='prepared_not_deleted',
        archive=OUT.relative_to(ROOT).as_posix(), directories=retirement))
    print(json.dumps({'archive': str(OUT), 'files': sum(len(b['entries']) for b in bundles),
        'bytes': sum(e['size_bytes'] for b in bundles for e in b['entries']),
        'archived_test_scripts': sum(e['legacy_path'].split('/')[-1].startswith('test_') and e['legacy_path'].endswith('.py') for b in bundles for e in b['entries'])}))


if __name__ == '__main__':
    main()
