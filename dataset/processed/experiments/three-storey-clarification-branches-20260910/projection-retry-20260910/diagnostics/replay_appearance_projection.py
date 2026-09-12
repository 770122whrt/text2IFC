import hashlib
import json
import multiprocessing
from pathlib import Path
import shutil

from text2ifc_agent.live_pipeline import run_candidate_gate_stage


def main():
    root = Path(__file__).resolve().parents[1]
    source = root / 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/rerun-20260910/A-revise/runtime/runs/026823cac75af845'
    output = root / '.tmp/appearance-projection-original-a-20260910'
    output.mkdir(exist_ok=False)
    names = ['generator/candidate.json', 'generator/validation.json', 'design-brief.json', 'expected-facts.json',
             'semantic-coverage.json', 'semantic-capabilities.json', 'repair/route.json']
    hashes = {}
    for name in names:
        path = source / name
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        target = output / name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(path, target)
    result = run_candidate_gate_stage(case_dir=output, output_dir=output, case_id='appearance-projection-regression')
    assert all(hashlib.sha256((source / name).read_bytes()).hexdigest() == digest for name, digest in hashes.items())
    assert hashlib.sha256((output / 'generator/candidate.json').read_bytes()).hexdigest() == hashes['generator/candidate.json']
    report = {'evidence_class': 'offline unchanged-candidate gate replay; no Provider or live Audit',
              'source_files_preserved': hashes, 'candidate_bytes_unchanged': True,
              'compile_reopen_success': result['compile_reopen_success'], 'valid': result['valid'],
              'geometry_feedback': result['geometry_feedback'], 'ifc_verification': result['ifc_verification'],
              'limits': 'Diagnostic IFC only; original live run remains audit_blocked, not relabeled or registered as Proof.'}
    (output / 'replay-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['candidate_bytes_unchanged', 'compile_reopen_success', 'valid', 'geometry_feedback']}, ensure_ascii=True))


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
