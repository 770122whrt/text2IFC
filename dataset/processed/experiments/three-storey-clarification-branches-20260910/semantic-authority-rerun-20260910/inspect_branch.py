"""Independent frozen IFC checks and native mesh views; never calls a Provider."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
ROOT = BASE.parents[3]
REFERENCE = BASE.parent/'three-storey-human-review-20260909'
REFERENCE_SHA = '756cf1ad4b8175ecb2571ce09483bd6ab83edfd562ae2f66c33a650b9e610d63'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('branch', choices=['A-revise', 'B-retain'])
    parser.add_argument('--render-python', type=Path, required=True)
    args = parser.parse_args()
    folder = OUT/args.branch
    execution = read(folder/'execution.json')
    runtime = Path(execution['run_dir'])
    report = {'branch': args.branch, 'run_id': runtime.name, 'runtime_status': execution['status'],
        'human_acceptance': 'pending', 'proof_registration': False,
        'reference_ifc_unchanged': sha(REFERENCE/'generated.ifc') == REFERENCE_SHA,
        'budget_before': execution['budget_before'], 'budget_after': execution['budget_after']}
    assert report['reference_ifc_unchanged']
    source = runtime/'output.ifc'
    if execution['status'] != 'compiled' or not source.is_file():
        report.update(status='blocked', reason='No compiled terminal IFC for independent review')
    else:
        target = folder/'generated.ifc'
        assert not target.exists()
        shutil.copyfile(source, target)
        for name in ['request.txt', 'clarification.txt', 'conversation.json']:
            assert not (folder/name).exists()
            shutil.copyfile(OUT/'inputs'/args.branch/name, folder/name)
        subprocess.run([sys.executable, str(OUT/'inputs'/args.branch/'check_ifc.py'), str(target),
                        str(folder/'independent-ifc-checks.json')], cwd=ROOT, check=True, timeout=180)
        checks = read(folder/'independent-ifc-checks.json')
        subprocess.run([sys.executable, str(BASE/'measure_clearance.py'), str(target),
                        str(folder/'clearance-checks.json')], cwd=ROOT, check=True, timeout=180)
        clearance = read(folder/'clearance-checks.json')
        subprocess.run([sys.executable, str(REFERENCE/'export_mesh.py'), str(target), str(folder/'views')],
                       cwd=ROOT, check=True, timeout=180)
        digest = sha(target)
        for view in ['overall', 'cutaway', 'window-double', 'door']:
            mesh = folder/'views'/(view+'-mesh.json')
            assert read(mesh)['source_sha256'] == digest
            subprocess.run([str(args.render_python), str(REFERENCE/'render_png.py'), str(mesh),
                            str(folder/'views'/(view+'.png'))], cwd=ROOT, check=True, timeout=180)
        report.update(ifc_sha256=digest, check_count=len(checks['checks']),
            failed_checks=checks['failed'], independent_status=checks['status'],
            clearance={k:clearance[k] for k in ['sample_count', 'minimum_sampled_gap_m', 'zero_gap_count']},
            status='awaiting_visual_review' if checks['status']=='passed' else 'blocked',
            limitations='Native IFC readback against frozen request, not building-code or engineering certification. B intentionally retains the acknowledged clearance problem.')
    write(folder/'review-checks.json', report)
    if report['status'] == 'blocked':
        write(OUT/'RUN-HOLD.json', {'status': 'independent_review_blocked', 'branch': args.branch,
            'reason': report, 'action': 'Preserve this attempt; return to offline diagnosis before more Provider transport.'})
    print(json.dumps({k:report[k] for k in ['branch', 'run_id', 'status']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
