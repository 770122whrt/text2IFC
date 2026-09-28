"""Fresh Audit of a preserved live candidate, under an additional authorized budget."""
from __future__ import annotations

import argparse
import contextlib
import io
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'src'))
from scripts.ifc2text.rerun_v10 import load, save, digest, now, fingerprint, SOURCE
from scripts.ifc2text.compact_campaign import runtime
from text2ifc_ifc2text.goal_budget import GoalBudget, GoalStopped

PARENT = ROOT / 'dataset/processed/experiments/ifc2text-rerun-20260922/material-list-continuation'
RUN = PARENT / 'reconstruction/runs/feac865882b37e94'
OUT = ROOT / 'dataset/processed/experiments/ifc2text-geometry-debug-20260922/audit-and-roundtrip'
CASE = OUT / 'case'
SCOPE = ['src/text2ifc_agent', 'src/text2ifc_contract', 'src/text2ifc_compiler',
         'src/text2ifc_quality', 'src/text2ifc_extractor', 'src/text2ifc_knowledge',
         'src/text2ifc_text', 'prompts/agent', 'schemas', 'pyproject.toml',
         'src/text2ifc_ifc2text/goal_budget.py', 'scripts/ifc2text/continue_audit_v12.py',
         'scripts/ifc2text/compact_campaign.py', 'scripts/ifc2text/rerun_v10.py']
TARGETS = ['tests/ifc2text/test_audit_continuation_v12.py',
           'tests/ifc2text/test_budget_transport_classification.py', 'tests/ifc2text/test_goal_budget_v03.py',
           'tests/agent/test_phase6_2_openai_compat.py', 'tests/agent/test_audit_failure_terminal.py',
           'tests/agent/test_phase6_3_gate_audit_bundle.py', 'tests/agent/test_audit_context.py',
           'tests/agent/test_material_list_v25_route.py', 'tests/agent/test_storey_identity_aliases.py',
           'tests/agent/test_space_geometry_projection_v12.py', 'tests/compiler/test_project_name_fallback.py',
           'tests/compiler/test_material_list_v25.py', 'tests/agent/test_interactive_cli_generation.py']


class AdditionalBudget(GoalBudget):
    def __init__(self, root, previous, *, inherited_reconstruction):
        if previous['halted'] or any(a['status'] == 'reserved' for a in previous['attempts']):
            raise GoalStopped('PREDECESSOR_HALTED_OR_UNSETTLED')
        self.inherited_reconstruction = inherited_reconstruction
        consumed = previous['historical']['tokens'] + sum(a['charged_tokens'] for a in previous['attempts'])
        writing = previous['historical']['writing'] + sum(a['stage'] == 'writing' for a in previous['attempts'])
        super().__init__(root, writing_calls=writing + 8, reconstruction_calls=inherited_reconstruction + 20,
                         tokens=consumed + 2000000, historical_writing_calls=writing, historical_tokens=consumed)

    def snapshot(self):
        result = super().snapshot()
        result['calls']['reconstruction'] += self.inherited_reconstruction
        return result


def budget():
    authority = load(OUT / 'authorization.json')
    if digest(PARENT / 'budget/goal-budget.json') != authority['predecessor_sha256']:
        raise GoalStopped('PREDECESSOR_CHANGED')
    return AdditionalBudget(OUT / 'budget', authority['predecessor'],
                            inherited_reconstruction=authority['inherited_reconstruction'])


def copy_report_sidecars(source, target):
    """Copy the public report contract, without importing old Audit or source IFC."""
    from text2ifc_agent.run_report import STAGE_SIDECARS
    hashes = {}
    for _, directory, names in STAGE_SIDECARS:
        if directory == 'audit':
            continue
        for name in names:
            relative = directory + '/' + name
            src, dst = Path(source) / relative, Path(target) / relative
            expected = digest(src)
            if dst.exists() and digest(dst) != expected:
                raise GoalStopped('EXISTING_SIDECAR_DIFFERS:' + relative)
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
            hashes[relative] = expected
    return hashes


def prepare():
    OUT.mkdir(parents=True, exist_ok=False)
    previous = load(PARENT / 'budget/goal-budget.json')
    inherited = load(PARENT / 'authorization.json')['inherited_reconstruction'] + sum(a['stage'] == 'reconstruction' for a in previous['attempts'])
    save(OUT / 'authorization.json', {'request': '新增 200 万 token 用于 Audit 和两条链路调试',
         'predecessor': previous, 'predecessor_sha256': digest(PARENT / 'budget/goal-budget.json'),
         'inherited_reconstruction': inherited, 'additional_tokens': 2000000,
         'meaning': 'new allowance added to actual prior consumption; no automatic retries'})
    cfg = load(PARENT / 'config.json'); cfg['audit_output_tokens'] = 32768
    save(OUT / 'config.json', cfg)
    names = ['design-brief/input.txt', 'design-brief/conversation.json', 'design-brief/design-brief.json',
             'design-brief/metrics.json', 'design-brief.json', 'expected-facts.json', 'generation-contract.json',
             'generator/candidate.json', 'generator/validation.json', 'generator/metrics.json',
             'generator/response.raw.json', 'generator/model-text.txt', 'candidate-origin.json',
             'repair/route.json', 'repair/metrics.json', 'repair/repair-attempts.json', 'semantic-coverage.json']
    hashes = {}
    for name in names:
        source = RUN / name
        if not source.exists():
            if name in {'generator/response.raw.json', 'generator/model-text.txt', 'repair/repair-attempts.json'}:
                continue
            raise GoalStopped('MISSING_PUBLIC_INPUT:' + name)
        target = CASE / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target); hashes[name] = digest(source)
    hashes.update(copy_report_sidecars(RUN, CASE))
    save(OUT / 'lineage.json', {'source_run': str(RUN), 'input_hashes': hashes,
        'source_ifc_sha256': digest(SOURCE), 'role': 'frozen live candidate; fresh compile and Audit; no new Generator call'})
    print({'prepared': True, 'tokens': budget().snapshot()['tokens_used_or_reserved'], 'ceiling': budget().snapshot()['limits']['tokens']})


def validate(*, finalization=False):
    import pytest
    from scripts.ifc2text.validate_goal import OfflineRecorder
    from text2ifc_agent.live_pipeline import run_candidate_gate_stage
    directory = OUT / ('validation-finalization' if finalization else 'validation'); directory.mkdir(exist_ok=False)
    if finalization and load(OUT / 'validation/admission.json')['status'] != 'admitted':
        raise GoalStopped('BASE_STAGE_ADMISSION_REQUIRED')
    before = fingerprint(scope=SCOPE); save(directory / 'source-snapshot.json', before)
    observer = OfflineRecorder(); stream = io.StringIO()
    targets = ['tests/agent/test_phase6_1_live.py', 'tests/agent/test_audit_failure_terminal.py',
               'tests/agent/test_phase6_3_gate_audit_bundle.py', 'tests/ifc2text/test_audit_continuation_v12.py'] if finalization else TARGETS
    args = [*targets, '-q', '-p', 'no:cacheprovider', '--basetemp=' + str(directory / 'tmp'), '--junitxml=' + str(directory / 'tests.xml')]
    with observer.network_guard(), contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        code = int(pytest.main(args, plugins=[observer]))
        gates = run_candidate_gate_stage(case_dir=CASE, output_dir=CASE, case_id='frozen-live-candidate-audit-v12')
    (directory / 'pytest.log').write_text(stream.getvalue(), encoding='utf-8')
    valid = code == 0 and not observer.counts['failed'] and not observer.counts['skipped'] and not observer.setup_errors and not observer.network_attempts and before == fingerprint(scope=SCOPE) and gates['deterministic_gates_passed']
    record = {'status': 'admitted' if valid else 'blocked', 'at': now(), 'tests': observer.counts,
        'exit_code': code, 'command': args, 'network_attempts': observer.network_attempts,
        'deterministic_gates_passed': gates['deterministic_gates_passed'],
        'snapshot_sha256': digest(directory / 'source-snapshot.json'), 'config_sha256': digest(OUT / 'config.json'),
        'scope': 'scoped revalidation of existing material-list stage for fresh Audit continuation',
        'parent_admission': str(OUT / 'validation/admission.json' if finalization else PARENT / 'validation/admission.json'), 'full_preflight': False}
    save(directory / 'admission.json', record)
    print({k: record[k] for k in ('status', 'tests', 'deterministic_gates_passed')}); print(stream.getvalue()[-1200:])
    return 0 if valid else 1


def admitted():
    directory = OUT / 'validation-finalization'
    record = load(directory / 'admission.json')
    if record['status'] != 'admitted': raise GoalStopped('ADMISSION_REQUIRED')
    if digest(directory / 'source-snapshot.json') != record['snapshot_sha256'] or load(directory / 'source-snapshot.json') != fingerprint(scope=SCOPE):
        raise GoalStopped('CODE_CHANGED_SINCE_ADMISSION')
    if digest(OUT / 'config.json') != record['config_sha256']: raise GoalStopped('CONFIG_CHANGED')
    lineage = load(OUT / 'lineage.json')
    if digest(SOURCE) != lineage['source_ifc_sha256']: raise GoalStopped('SOURCE_CHANGED')
    for name, expected in lineage['input_hashes'].items():
        if digest(RUN / name) != expected or digest(CASE / name) != expected:
            raise GoalStopped('PUBLIC_INPUT_CHANGED:' + name)


def audit():
    from text2ifc_agent.live_pipeline import run_audit_report_stage, run_final_acceptance_stage
    admitted(); b = budget(); cfg = load(OUT / 'config.json')
    if (OUT / 'audit-started.json').exists(): raise GoalStopped('SINGLE_ATTEMPT_ALREADY_STARTED')
    b.check_capacity('reconstruction')
    conf, client, provider = runtime(cfg, b, 'reconstruction', cfg['audit_output_tokens'])
    save(OUT / 'audit-started.json', {'at': now(), 'requested_model': conf.model, 'output_cap': cfg['audit_output_tokens'], 'retries': 0})
    try:
        result = run_audit_report_stage(provider=provider, case_dir=CASE, case_id='frozen-live-candidate-audit-v12')
        save(OUT / 'audit-result.json', result)
        report = load(CASE / 'audit/audit-report.json')
        if result.get('valid') is True and report.get('recommendation') == 'accept' and report.get('blocking') is False:
            save(OUT / 'acceptance-result.json', run_final_acceptance_stage(case_dir=CASE, output_dir=OUT / 'accepted', case_id='frozen-live-candidate-audit-v12'))
        admitted()
        print({'audit': report.get('recommendation'), 'blocking': report.get('blocking'), 'tokens': b.snapshot()['tokens_used_or_reserved']})
    except Exception as error:
        save(OUT / 'audit-terminal.json', {'status': 'failed', 'error_type': type(error).__name__, 'at': now()})
        raise


def recover_report():
    """Finish a saved valid live Audit locally; never sends a new Provider request."""
    from text2ifc_agent.run_report import build_live_run_report
    from text2ifc_agent.live_pipeline import run_final_acceptance_stage
    snapshot = load(OUT / 'validation-finalization/source-snapshot.json')
    current = fingerprint(scope=SCOPE)
    allowed = 'scripts/ifc2text/continue_audit_v12.py'
    if {k: v for k, v in snapshot.items() if k != allowed} != {k: v for k, v in current.items() if k != allowed}:
        raise GoalStopped('PRODUCTION_CHANGED_SINCE_AUDIT')
    lineage = load(OUT / 'lineage.json')
    if digest(SOURCE) != lineage['source_ifc_sha256']: raise GoalStopped('SOURCE_CHANGED')
    for name, expected in lineage['input_hashes'].items():
        if digest(RUN / name) != expected or digest(CASE / name) != expected:
            raise GoalStopped('PUBLIC_INPUT_CHANGED:' + name)
    metrics = load(CASE / 'audit/metrics.json')
    if metrics.get('valid') is not True or metrics.get('evidence_class') != 'live':
        raise GoalStopped('VALID_SAVED_LIVE_AUDIT_REQUIRED')
    if (OUT / 'report-recovery.json').exists(): raise GoalStopped('ALREADY_RECOVERED')
    audit_hashes = {p.name: digest(p) for p in (CASE / 'audit').iterdir() if p.is_file()}
    hashes = copy_report_sidecars(RUN, CASE)
    report = build_live_run_report(case_dir=CASE)
    result = run_final_acceptance_stage(case_dir=CASE, output_dir=OUT / 'accepted', case_id='frozen-live-candidate-audit-v12')
    assert audit_hashes == {p.name: digest(p) for p in (CASE / 'audit').iterdir() if p.is_file()}
    save(OUT / 'acceptance-result.json', result)
    save(OUT / 'report-recovery.json', {'at': now(), 'reason': 'continuation harness omitted report sidecars',
        'copied_hashes': hashes, 'audit_hashes_unchanged': audit_hashes, 'provider_calls': 0,
        'report': str(report), 'result': result, 'recovery_script_sha256': digest(Path(__file__))})
    print({'valid': result['valid'], 'provider_calls': 0, 'budget_tokens': budget().snapshot()['tokens_used_or_reserved']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('command', choices=['prepare', 'validate', 'validate-finalization', 'audit', 'recover-report', 'status'])
    args = parser.parse_args()
    if args.command == 'validate': raise SystemExit(validate())
    elif args.command == 'validate-finalization': raise SystemExit(validate(finalization=True))
    elif args.command == 'status': print(budget().snapshot())
    elif args.command == 'recover-report': recover_report()
    else: globals()[args.command]()
