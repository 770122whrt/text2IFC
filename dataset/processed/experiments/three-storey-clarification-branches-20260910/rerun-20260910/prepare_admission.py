"""Stage-scoped offline admission for fresh A/B; never opens a Provider."""
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


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


GROUPS = {
    'seams': [
        'agent/test_generation_semantic_correction.py', 'agent/test_semantic_scope_and_type_policy.py',
        'agent/test_phase6_5_changeset_apply.py', 'agent/test_phase6_5_change_scope.py',
        'agent/test_phase6_5_changeset_stage.py', 'agent/test_changeset_context_selection.py',
        'agent/test_changeset_failure_evidence.py', 'agent/test_generation_task_budget.py',
        'agent/test_cross_storey_identity_contract.py', 'agent/test_cross_storey_name_boundary.py',
        'agent/test_generation_semantic_closure.py', 'agent/test_semantic_identity_binding.py',
        'agent/test_design_review_audit.py', 'agent/test_phase6_2_openai_compat.py',
        'agent/test_design_brief_attempt_preservation.py', 'agent/test_prompt_registry.py',
    ],
    'public-chain': [
        'agent/test_design_review_fresh_rerun.py', 'agent/test_semantic_public_paths.py',
        'agent/test_interactive_cli_generation.py', 'agent/test_interactive_cli_flow.py',
        'agent/test_interactive_cli_session.py', 'agent/test_phase6_2_fix_repl_cli.py',
        'agent/test_phase6_5_staged_generation.py', 'agent/test_phase6_5_scoped_loop.py',
        'agent/test_phase6_4_geometry_loop.py', 'agent/test_phase6_3_gate_audit_bundle.py',
        'agent/test_clarification_resume_preservation.py', 'agent/test_early_field_recovery.py',
        'agent/test_gate_dispute_recovery.py', 'agent/test_generation_authoring_contract.py',
    ],
    'reopened-ifc': [
        'compiler/test_v21_semantics.py', 'compiler/test_basic_filling.py',
        'compiler/test_coordinated_appearance.py', 'compiler/test_ifc_verification.py',
        'compiler/test_phase6_4_stair_geometry.py', 'ifc_quality/test_floor_opening_identity.py',
        'ifc_quality/test_phase6_4_geometry_truth_gate.py', 'contract/test_semantic_validation.py',
    ],
}


def main():
    validation = OUT / 'validation'
    validation.mkdir(exist_ok=False)
    frozen_checks = []
    for manifest, base in [(BASE / 'LIVE-ATTEMPT-FILES.json', BASE),
                           (BASE / 'continuation-20260910/FILES.json', BASE / 'continuation-20260910')]:
        rows = read(manifest)['files']
        for row in rows:
            assert sha(base / row['path']) == row['sha256'], row['path']
        frozen_checks.append({'manifest': str(manifest.relative_to(ROOT)), 'sha256': sha(manifest),
                              'verified_files': len(rows)})
    for branch in ['A-revise', 'B-retain']:
        target = OUT / 'inputs' / branch
        target.mkdir(parents=True, exist_ok=False)
        for name in ['request.txt', 'conversation.json', 'clarification.txt', 'reference-review.json',
                     'frozen-expectations.json', 'check_ifc.py']:
            shutil.copyfile(BASE / branch / name, target / name)
    authorization = {
        'user_request': '下一步进行provider的调用 并进行A/B两个分支的重新运行。然后给我进行审查 如果遇到问题随时停下 如果没有遇到问题就开启goal模式完成',
        'destination': 'https://api.deepseek.com', 'model': 'deepseek-v4-flash',
        'scope': 'Fresh full Generation A/B from frozen request and approved scripted branch conversation. No prior Brief/candidate/budget reused.',
        'per_branch_whole_run_limits': {'max_calls': 32, 'max_tokens': 2000000, 'max_active_seconds': 3600},
        'payload': ['original request', 'approved branch conversation', 'public reference concern',
                    'new Design Brief', 'candidate JSON', 'automatic feedback', 'run metadata'],
        'excluded': ['IFC file bytes', 'private Gold', 'Repair source', 'other task data', 'credential text'],
        'human_review': 'pending; no accepted Proof installation', 'github_push_authorized': False,
    }
    write(OUT / 'authorization.json', authorization)
    write(OUT / 'payload-preview.json', {**authorization, 'branches': {
        branch: {'conversation': read(OUT / 'inputs' / branch / 'conversation.json'),
                 'reference_review': read(OUT / 'inputs' / branch / 'reference-review.json')}
        for branch in ['A-revise', 'B-retain']}})
    parent_path = BASE / 'continuation-20260910/admission.json'
    parent = read(parent_path)
    for package, version in parent['dependencies'].items():
        assert metadata.version(package) == version, package
    paths = {ROOT / p for p in parent['files_sha256']}
    for folder in ['src/text2ifc_agent', 'src/text2ifc_compiler', 'src/text2ifc_contract', 'src/text2ifc_quality']:
        paths.update((ROOT / folder).glob('*.py'))
    paths.update((ROOT / 'prompts/agent').rglob('*.md'))
    paths.update(OUT.rglob('*.py'))
    paths.update((OUT / 'inputs').rglob('*'))
    paths.update(OUT / p for p in ['authorization.json', 'payload-preview.json'])
    paths.update(ROOT / 'tests' / p for group in GROUPS.values() for p in group)
    paths = {p for p in paths if p.is_file()}
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    checks = []
    for group, files in GROUPS.items():
        command = [sys.executable, '-m', 'pytest', *['tests/' + p for p in files], '-q',
                   '-p', 'no:cacheprovider', '--basetemp', '.tmp/pytest-ab-rerun-stage-' + group + '-20260910',
                   '--junitxml', str(validation / (group + '.xml'))]
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        print('Starting offline stage group:', group, flush=True)
        with (validation / (group + '.log')).open('xb') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        suites = list(ET.parse(validation / (group + '.xml')).getroot().iter('testsuite'))
        counts = {k: sum(int(s.get(k, 0)) for s in suites) for k in ['tests', 'failures', 'errors', 'skipped']}
        check = {'group': group, 'command': command, 'started_at': started,
                 'finished_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'timeout_seconds': 900,
                 'exit_code': result.returncode, **counts, 'log_sha256': sha(validation / (group + '.log')),
                 'xml_sha256': sha(validation / (group + '.xml'))}
        checks.append(check)
        write(validation / 'checks.json', checks)
        print(group, counts, flush=True)
        assert result.returncode == 0 and counts['tests'] > 0 and not any(counts[k] for k in ['failures', 'errors', 'skipped']), check
    for label, command in [
        ('compileall', [sys.executable, '-m', 'compileall', '-q',
          *[str(p) for p in paths if p.suffix == '.py']]),
        ('diff-check', ['git', 'diff', '--check', '--', 'src', 'tests', 'prompts', 'docs', str(OUT.relative_to(ROOT))]),
    ]:
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
        log = validation / (label + '.log')
        log.write_bytes(result.stdout + result.stderr)
        checks.append({'group': label, 'command': command, 'started_at': started,
                       'finished_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                       'timeout_seconds': 180, 'exit_code': result.returncode, 'log_sha256': sha(log)})
        write(validation / 'checks.json', checks)
        assert result.returncode == 0, label
    assert all(sha(ROOT / p) == digest for p, digest in before.items()), 'Files changed during validation'
    for p in validation.iterdir():
        before[p.relative_to(ROOT).as_posix()] = sha(p)
    admission = {
        'status': 'admitted', 'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'stage': 'Generation public API/CLI with bounded atomic semantic correction and design-review branches',
        'scope': 'Stage-scoped fresh offline seams and public full chain; live legacy_full; staged compatibility offline',
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'worktree': subprocess.check_output(['git', 'status', '--short', '--', 'src', 'tests', 'prompts', 'docs', str(OUT.relative_to(ROOT))], cwd=ROOT, text=True),
        'python': sys.version, 'platform': platform.platform(), 'dependencies': parent['dependencies'],
        'checks': checks, 'files_sha256': before, 'frozen_authority_checks': frozen_checks,
        'parent_reference': {'path': parent_path.relative_to(ROOT).as_posix(), 'sha256': sha(parent_path)},
        'supersedes_holds': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)}
            for p in [BASE / 'RUN-HOLD.json', BASE / 'continuation-20260910/RUN-HOLD.json']],
        'supersession_basis': '60191979 atomic Type graph correction, 06230aa9 identity/error evidence, current fresh stage checks. Historical run failures and holds unchanged.',
        'matrix': {
            'complete/publication/reopen': 'public-chain: fresh A/B runner; semantic public paths; interactive CLI generation',
            'clarification/resume/unsupported/persistence': 'public-chain: interactive flow/session, clarification preservation, REPL',
            'malformed/truncated/transport evidence/budget': 'seams: OpenAI compatibility, changeset failure evidence, task budget',
            'binding/atomic rollback/request preservation': 'seams: semantic correction, identity, scope, changeset apply',
            'L0/L1/L2/geometry/material/appearance': 'reopened-ifc plus public-chain gate/audit bundle',
            'immutable truth/private Gold': 'Frozen input/old attempt hashes; Generation payload contains only request/approved conversation/public concern, no original IFC/private Gold. Repair is outside this stage.',
        },
        'full_preflight': False, 'network_transport_attempted': False,
        'limits': 'Deterministic offline checks, no capability success-rate claim. Same revealed development A/B retries, not blind evaluation. B retains user-confirmed zero-clearance defect. No construction/code approval or human acceptance.',
        'invalidation': 'Any bound file/dependency drift, applicable failed check or new unresolved deterministic defect blocks transport.',
    }
    write(OUT / 'admission.json', admission)
    print(json.dumps({'status': 'admitted', 'tests': sum(c.get('tests', 0) for c in checks), 'bound_files': len(before)}), flush=True)


if __name__ == '__main__':
    main()
