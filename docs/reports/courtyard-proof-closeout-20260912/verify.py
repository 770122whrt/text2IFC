"""Offline archive verification; never executes archived runner main functions."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
OUT = ROOT/'dataset/processed/proof/generation/phase6.6/courtyard-library-20260912'


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def write(name, value):
    with (OUT/'validation'/name).open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    from scripts.proof.package import validate_package
    manifest = read(OUT/'manifest.json')
    package = validate_package(OUT, manifest)
    write('package.json', package)
    assert package['status'] == 'passed', package
    checker = load('v2_frozen_checker', OUT/'evidence/v2/rerun-03/check_ifc.py')
    strict = checker.run(OUT/'open-court-v2/generated.ifc')
    write('independent-v2-strict.json', strict)
    color = load('v2_frozen_hex8', OUT/'evidence/v2/rerun-03/color_readback_v2.py')
    current = color.run(OUT/'open-court-v2/generated.ifc', OUT/'validation/independent-v2-strict.json')
    write('independent-v2-hex8.json', current)
    assert current['passed'] and len(current['checks']) == 545
    v1 = load('v1_frozen_checker', OUT/'evidence/v1/check_ifc.py').check_ifc(OUT/'reference-v1/generated.ifc')
    write('independent-v1.json', v1)
    assert v1['status'] == 'passed', v1['failed']
    reviews = []
    for case in manifest['cases']:
        p = OUT/case['path']
        digest = hashlib.sha256((p/'generated.ifc').read_bytes()).hexdigest()
        views = read(p/'views/views.json')
        assert views['ifc_sha256'] == digest and views['mesh_failures'] == []
        model = read(p/'model.json')
        assert model['entities'] and model['relationships']
        metrics = read(OUT/case['authority'])
        assert metrics['valid'] and metrics['compile_reopen_success'] and metrics['deterministic_gates_passed']
        assert metrics['live_acceptance_eligible']
        reviews.append(dict(case_id=case['case_id'], ifc_sha256=digest,
            image_source_matches=True, mesh_failures=0, candidate_json_valid=True,
            frozen_machine_acceptance_valid=True, human_status=case['human_review_status']))
    acceptance = read(OUT/'human-acceptance.json')
    assert acceptance['ifc_sha256'] == reviews[0]['ifc_sha256']
    assert read(OUT/'evidence/v2/rerun-03/review-status.json')['human_status'] == 'not_reviewed'
    write('review-checks.json', dict(status='passed', cases=reviews, original_pending_snapshot_preserved=True))
    print(json.dumps({'package': package['status'], 'v2': len(current['checks']), 'v1': v1['total'], 'review_checks': 'passed'}))


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
