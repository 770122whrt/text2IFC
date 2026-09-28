"""One source-to-text-to-IFC diagnostic run of actual opening profiles."""
from __future__ import annotations
import argparse
import contextlib
import io
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'src'))
from scripts.ifc2text.rerun_v10 import load, save, digest, now, fingerprint, SOURCE, SCOPE
from scripts.ifc2text.continue_audit_v12 import budget, OUT as AUDIT_OUT
from scripts.ifc2text.compact_campaign import runtime, verify_text
from text2ifc_ifc2text.goal_budget import GoalStopped

OUT = ROOT / 'dataset/processed/experiments/ifc2text-geometry-debug-20260922/opening-live-v13'
TARGETS = ['tests/ifc2text', 'tests/agent/test_material_list_v25_route.py',
           'tests/agent/test_generation_v24_route.py', 'tests/agent/test_space_geometry_projection_v12.py',
           'tests/agent/test_storey_identity_aliases.py', 'tests/compiler/test_polygon_wall_hosts_v24.py',
           'tests/agent/test_audit_failure_terminal.py']


class StageProvider:
    def __init__(self, generator, audit):
        self.generator, self.audit = generator, audit

    def provider_evidence_delegate(self):
        return self.generator

    def generate_live(self, **kwargs):
        selected = self.audit if kwargs.get('state', {}).get('stage') == 'audit' else self.generator
        return selected.generate_live(**kwargs)


def prepare():
    from text2ifc_ifc2text.compact_pipeline import prepare_compact
    OUT.mkdir(parents=True, exist_ok=False)
    cfg = load(AUDIT_OUT / 'config.json')
    cfg.update(description_version='0.9', output=str(OUT.relative_to(ROOT)),
               budget_root=str((AUDIT_OUT / 'budget').relative_to(ROOT)),
               max_total_tokens=budget().snapshot()['limits']['tokens'], max_writing_calls=1, max_reconstruction_calls=3)
    save(OUT / 'config.json', cfg)
    before = digest(SOURCE)
    report = prepare_compact(SOURCE, OUT / 'hxp', description_version='0.9')
    assert before == digest(SOURCE)
    save(OUT / 'original-source.json', {'path': str(SOURCE), 'sha256': before})
    save(OUT / 'scope.json', {'role': 'revealed development case; one new narration and public text-only reconstruction',
        'shared_authorization': str(AUDIT_OUT / 'authorization.json'), 'budget_before': budget().snapshot(),
        'limits': 'one write, one Brief, Generator then Audit; no outer retry',
        'source_comparison': 'Compare 1.1 only after generation; 1 mm tolerance fixed'})
    print({'prepared': True, 'characters': report['characters']})


def validate():
    import pytest
    from scripts.ifc2text.validate_goal import OfflineRecorder
    directory = OUT / 'validation'; directory.mkdir(exist_ok=False)
    before = fingerprint(scope=SCOPE); save(directory / 'source-snapshot.json', before)
    stream = io.StringIO(); observer = OfflineRecorder()
    args = [*TARGETS, '-q', '-p', 'no:cacheprovider', '--basetemp=' + str(directory / 'tmp'), '--junitxml=' + str(directory / 'tests.xml')]
    with observer.network_guard(), contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        code = int(pytest.main(args, plugins=[observer]))
    (directory / 'pytest.log').write_text(stream.getvalue(), encoding='utf-8')
    valid = code == 0 and not observer.counts['failed'] and not observer.counts['skipped'] and not observer.setup_errors and not observer.network_attempts and before == fingerprint(scope=SCOPE)
    record = {'status': 'admitted' if valid else 'blocked', 'at': now(), 'tests': observer.counts,
        'exit_code': code, 'command': args, 'network_attempts': observer.network_attempts,
        'snapshot_sha256': digest(directory / 'source-snapshot.json'), 'config_sha256': digest(OUT / 'config.json'),
        'scope': 'opening extraction 0.9 and affected text-only public generation route', 'full_preflight': False,
        'previous_stage': str(AUDIT_OUT / 'validation-finalization/admission.json')}
    save(directory / 'admission.json', record)
    print({k: record[k] for k in ('status', 'tests')}); print(stream.getvalue()[-1500:])
    return 0 if valid else 1


def admitted():
    record = load(OUT / 'validation/admission.json')
    if record['status'] != 'admitted': raise GoalStopped('ADMISSION_REQUIRED')
    if digest(OUT / 'validation/source-snapshot.json') != record['snapshot_sha256'] or load(OUT / 'validation/source-snapshot.json') != fingerprint(scope=SCOPE):
        raise GoalStopped('CODE_CHANGED_SINCE_ADMISSION')
    if digest(OUT / 'config.json') != record['config_sha256']: raise GoalStopped('CONFIG_CHANGED')
    if digest(SOURCE) != load(OUT / 'original-source.json')['sha256']: raise GoalStopped('SOURCE_CHANGED')


def live(stage):
    admitted(); cfg = load(OUT / 'config.json'); b = budget()
    marker = OUT / (stage + '-started.json')
    if marker.exists(): raise GoalStopped('SINGLE_ATTEMPT_ALREADY_STARTED')
    if stage == 'generate' and load(OUT / 'brief-result.json')['status'] != 'ready': raise GoalStopped('READY_BRIEF_REQUIRED')
    text = verify_text(OUT / 'hxp') if stage != 'write' else None
    budget_stage = 'writing' if stage == 'write' else 'reconstruction'
    b.check_capacity(budget_stage)
    cap = cfg['writing_output_tokens'] if stage == 'write' else 131072
    conf, client, provider = runtime(cfg, b, budget_stage, cap)
    save(marker, {'at': now(), 'stage': stage, 'requested_model': conf.model, 'max_output_tokens': cap, 'retries': 0})
    try:
        if stage == 'write':
            from text2ifc_ifc2text.compact_pipeline import write_compact
            result = write_compact(output=OUT / 'hxp', provider=provider, budget=b, template_id=cfg['writing_template'])
        else:
            from text2ifc_agent.session_store import SessionStore
            from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker, run_design_brief_clarification_loop, run_ready_session_to_ifc
            from text2ifc_agent.generation_budget import GenerationBudget, BudgetLimits
            limits = BudgetLimits(max_calls=3, max_tokens=2000000)
            attempt = OUT / 'reconstruction'
            with SessionStore.open(attempt / 'sessions.sqlite', artifact_root=attempt) as store:
                if stage == 'brief':
                    session = store.create_session(original_input=text); GenerationBudget(session.run_dir, limits=limits)
                    save(attempt / 'session.json', {'id': session.session_id, 'run_dir': str(session.run_dir)})
                    invoker = make_openai_design_brief_invoker(config=conf, run_dir=session.run_dir, client_factory=lambda **_: client,
                        design_review_enabled=False, design_brief_schema_version=cfg['design_brief_schema'])
                    value = run_design_brief_clarification_loop(store=store, session=session.session_id, invoke_design_brief=invoker, user_answers=())
                    result = {'status': value.status, 'session_id': value.session_id, 'session_hash': value.session_hash}
                else:
                    # Same adapter, with a smaller output cap for the Audit stage.
                    _, _, audit_provider = runtime(cfg, b, 'reconstruction', cfg['audit_output_tokens'])
                    value = run_ready_session_to_ifc(store=store, session=load(attempt / 'session.json')['id'],
                        provider_factory=lambda: StageProvider(provider, audit_provider), generation_strategy='legacy_full', trace_level='debug',
                        budget_limits=limits, bim_json_schema_version=cfg['bim_json_schema_version'])
                    result = {'status': value.status, 'session_hash': value.session_hash, 'ifc_path': str(value.ifc_path) if value.ifc_path else None,
                        'generator_status': value.generator_status, 'audit_status': value.audit_status}
        save(OUT / (stage + '-result.json'), result); admitted()
        print(result); print({'tokens': b.snapshot()['tokens_used_or_reserved'], 'calls': b.snapshot()['calls']})
    except Exception as error:
        save(OUT / (stage + '-terminal.json'), {'status': 'failed', 'error_type': type(error).__name__, 'at': now()})
        raise


def compare():
    from text2ifc_ifc2text.precision_compare_v11 import compare_roundtrip
    run = Path(load(OUT / 'reconstruction/session.json')['run_dir'])
    before = digest(SOURCE)
    report = compare_roundtrip(SOURCE, run / 'output.ifc')
    assert before == digest(SOURCE)
    report['generation_result'] = load(OUT / 'generate-result.json')
    save(OUT / 'compare-v1.1.json', report)
    print(report['summary'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('command', choices=['prepare', 'validate', 'write', 'brief', 'generate', 'compare'])
    args = parser.parse_args()
    if args.command == 'validate': raise SystemExit(validate())
    elif args.command in {'write', 'brief', 'generate'}: live(args.command)
    else: globals()[args.command]()
