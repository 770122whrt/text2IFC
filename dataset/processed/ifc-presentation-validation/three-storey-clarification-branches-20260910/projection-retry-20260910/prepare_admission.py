"""Scoped revalidation of the existing Generation stage; no network calls."""
import datetime as dt
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
ROOT = BASE.parents[3]
PARENT = BASE / 'rerun-20260910'
PRIOR_A = PARENT / 'A-revise/runtime/runs/026823cac75af845'
TESTS = ['test_appearance_request_projection.py', 'test_semantic_public_paths.py',
         'test_design_review_budget_retry.py', 'test_generation_task_budget.py',
         'test_changeset_failure_evidence.py', 'test_design_review_audit.py',
         'test_interactive_cli_flow.py', 'test_phase6_2_fix_repl_cli.py',
         'test_clarification_resume_preservation.py']


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    validation = OUT / 'validation'
    validation.mkdir(exist_ok=False)
    (OUT / '.gitattributes').write_text('* -text\n', encoding='utf-8')
    parent = read(PARENT / 'admission.json')
    changed = {name for name, digest in parent['files_sha256'].items() if sha(ROOT / name) != digest}
    assert changed == {'src/text2ifc_agent/semantic_requirements.py', 'src/text2ifc_agent/semantic_report.py',
                       'src/text2ifc_agent/live_pipeline.py', 'tests/agent/test_semantic_public_paths.py'}, changed
    for package, version in parent['dependencies'].items():
        assert metadata.version(package) == version
    manifests = [(BASE / 'LIVE-ATTEMPT-FILES.json', BASE),
                 (BASE / 'continuation-20260910/FILES.json', BASE / 'continuation-20260910'),
                 (PARENT / 'FILES.json', PARENT)]
    frozen_checks = []
    for path, folder in manifests:
        rows = read(path)['files']
        for row in rows:
            assert sha(folder / row['path']) == row['sha256'], row['path']
        frozen_checks.append({'manifest': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'files': len(rows)})
    for branch in ['A-revise', 'B-retain']:
        shutil.copytree(PARENT / 'inputs' / branch, OUT / 'inputs' / branch,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    history = read(PRIOR_A / 'generation-budget.json')
    assert len(history['attempts']) == 3 and all(a['status'] == 'completed' for a in history['attempts'])
    assert history['limits'] == {'max_calls': 32, 'max_tokens': 2000000, 'max_active_seconds': 3600}
    confirmation = PARENT / 'explicit-egress-confirmation.json'
    authorization = {
        'source_confirmation': confirmation.relative_to(ROOT).as_posix(), 'confirmation_sha256': sha(confirmation),
        'approved_payload_preview': (PARENT / 'payload-preview.json').relative_to(ROOT).as_posix(),
        'approved_payload_sha256': sha(PARENT / 'payload-preview.json'),
        'destination': 'https://api.deepseek.com', 'model': 'deepseek-v4-flash',
        'scope': 'Continue the same authorized A/B task after offline defect repair, with unchanged frozen request/conversation. New Brief and candidate; preserve prior A spend in the same total budget.',
        'A_prior_calls_charged': 3, 'B_prior_calls_charged': 0, 'per_branch_limits': history['limits'],
        'excluded_from_provider_payload': ['original IFC bytes', 'private Gold', 'other task data', 'credential text'],
        'github_push_authorized': False,
    }
    write(OUT / 'authorization.json', authorization)
    diagnostics = OUT / 'diagnostics'
    diagnostics.mkdir()
    for name in ['appearance-projection-red-20260910.xml', 'appearance-projection-unit-final-20260910.xml',
                 'appearance-projection-public-green-20260910.xml', 'appearance-provenance-red-20260910.xml',
                 'appearance-retry-harness-red-20260910.xml', 'appearance-retry-harness-green-20260910.xml']:
        shutil.copyfile(ROOT / '.tmp' / name, validation / name)
    shutil.copytree(ROOT / '.tmp/appearance-projection-original-a-20260910', diagnostics / 'original-a-offline-replay')
    shutil.copyfile(ROOT / '.tmp/replay_appearance_projection.py', diagnostics / 'replay_appearance_projection.py')
    (diagnostics / 'README.md').write_text('离线诊断：原A候选字节未改，使用修复后的公共Gate编译并重读。这里的IFC不是新的真实完整运行，原A仍为audit_blocked；不得用它替代下方新运行的交付IFC。脚本原工作位置为仓库 .tmp/。\n', encoding='utf-8')
    paths = {ROOT / name for name in parent['files_sha256']}
    paths.update([PARENT / 'admission.json', PARENT / 'RUN-HOLD.json', confirmation,
                  PRIOR_A / 'generation-budget.json', OUT / 'run_branches.py', OUT / 'prepare_admission.py',
                  OUT / 'authorization.json', OUT / '.gitattributes'])
    paths.update(ROOT / 'tests/agent' / name for name in TESTS)
    paths.update(p for p in (OUT / 'inputs').rglob('*') if p.is_file())
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}
    command = [sys.executable, '-m', 'pytest', *['tests/agent/' + name for name in TESTS], '-q',
               '-p', 'no:cacheprovider', '--basetemp', '.tmp/pytest-projection-retry-admission-20260910',
               '--junitxml', str(validation / 'scoped-final.xml')]
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    print('Starting changed-scope public-path revalidation; no Provider.', flush=True)
    with (validation / 'scoped-final.log').open('xb') as log:
        result = subprocess.run(command, cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                                stdout=log, stderr=subprocess.STDOUT, timeout=900)
    suites = list(ET.parse(validation / 'scoped-final.xml').getroot().iter('testsuite'))
    counts = {key: sum(int(s.get(key, 0)) for s in suites) for key in ['tests', 'failures', 'errors', 'skipped']}
    checks = [{'command': command, 'started_at': started, 'finished_at': dt.datetime.now(dt.timezone.utc).isoformat(),
               'timeout_seconds': 900, 'exit_code': result.returncode, 'log_sha256': sha(validation / 'scoped-final.log'), **counts}]
    write(validation / 'checks.json', checks)
    print(counts, flush=True)
    assert result.returncode == 0 and counts['tests'] and not any(counts[key] for key in ['failures', 'errors', 'skipped'])
    for label, command in [('compileall', [sys.executable, '-m', 'compileall', '-q',
            'src/text2ifc_agent/semantic_requirements.py', 'src/text2ifc_agent/semantic_report.py',
            'src/text2ifc_agent/live_pipeline.py', *['tests/agent/' + name for name in TESTS],
            str(OUT / 'run_branches.py'), str(OUT / 'prepare_admission.py')]),
            ('diff-check', ['git', '-c', 'core.whitespace=cr-at-eol', 'diff', '--check', '--', 'src', 'tests', 'docs', str(OUT.relative_to(ROOT))])]:
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=180)
        log = validation / (label + '.log')
        log.write_bytes(result.stdout + result.stderr)
        checks.append({'command': command, 'started_at': started, 'finished_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                       'timeout_seconds': 180, 'exit_code': result.returncode, 'log_sha256': sha(log)})
        assert result.returncode == 0
    write(validation / 'checks.json', checks)
    assert all(sha(ROOT / name) == digest for name, digest in before.items())
    for p in validation.iterdir():
        before[p.relative_to(ROOT).as_posix()] = sha(p)
    admission = {
        'status': 'admitted', 'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'scope': 'Scoped revalidation within the admitted Generation stage after appearance projection bug fix; public complete/clarification/recovery and budget-carry runner, no schema/prompt/operation-permission changes.',
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'worktree': subprocess.check_output(['git', 'status', '--short', '--', 'src', 'tests', 'docs', str(OUT.relative_to(ROOT))], cwd=ROOT, text=True),
        'python': sys.version, 'platform': platform.platform(), 'dependencies': parent['dependencies'],
        'parent_admission': {'path': (PARENT / 'admission.json').relative_to(ROOT).as_posix(), 'sha256': sha(PARENT / 'admission.json')},
        'changed_bound_files': sorted(changed), 'reused_unchanged_bindings': len(parent['files_sha256']) - len(changed),
        'reuse_basis': 'Parent stage 487 checks: unchanged IFC compiler/geometry/Type transaction/transport contracts retain evidence. Fresh checks cover changed request projection, final Brief source, all four basic fillings through both strategies, ready-session acceptance, A/B branch runner, budget exhaustion/unsettled/hold, clarification and REPL, Audit and response preservation. Additional 108 public/Type/identity checks were green before final provenance-path-only correction.',
        'supersedes_holds': [{'path': (PARENT / 'RUN-HOLD.json').relative_to(ROOT).as_posix(), 'sha256': sha(PARENT / 'RUN-HOLD.json')}],
        'supersession_basis': 'af45478e fixes projection without changing candidate; frozen original A offline gate and 290 independent IFC checks pass. This does not relabel the genuine failed attempt.',
        'budget_history': {'A-revise': (PRIOR_A / 'generation-budget.json').relative_to(ROOT).as_posix()},
        'checks': checks, 'files_sha256': before, 'frozen_authority_checks': frozen_checks,
        'network_transport_attempted': False, 'full_preflight': False,
        'limits': 'Offline fake/replay admission; real calls only viability for revealed A/B task. Human review still required; B retains known usability issue. No Proof installation or push.',
        'invalidation': 'Any bound file/dependency drift, failed applicable check, new unresolved deterministic defect or collection RUN-HOLD blocks further transport.',
    }
    write(OUT / 'admission.json', admission)
    print(json.dumps({'status': 'admitted', 'tests': counts['tests'], 'bound_files': len(before), 'reused_parent_bindings': admission['reused_unchanged_bindings']}), flush=True)


if __name__ == '__main__':
    main()
