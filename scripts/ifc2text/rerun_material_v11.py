"""Authorized material-list continuation; reuse reviewed text, never rewrite a response."""
from __future__ import annotations
import argparse
import contextlib
import io
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'src'))
from scripts.ifc2text import rerun_v10 as prior_run
from scripts.ifc2text.rerun_v10 import load, save, digest, now, SCOPE as PRIOR_SCOPE, SOURCE
from scripts.ifc2text.compact_campaign import runtime, verify_text
from text2ifc_ifc2text.goal_budget import GoalBudget, GoalStopped

PARENT = prior_run.OUT
OUT = PARENT / 'material-list-continuation'
SCOPE = [*PRIOR_SCOPE, 'tests/contract_v2']
TARGETS = [*prior_run.TARGETS, 'tests/agent/test_material_list_v25_route.py',
           'tests/compiler/test_material_list_v25.py', 'tests/contract_v2/test_material_list_v25.py']

def fingerprint():
    return prior_run.fingerprint(scope=SCOPE)

class ContinuationBudget(GoalBudget):
    def __init__(self, root, previous, *, inherited_reconstruction):
        if previous['halted'] or any(a['status'] == 'reserved' for a in previous['attempts']):
            raise GoalStopped('PREDECESSOR_HALTED_OR_UNSETTLED')
        self.inherited_reconstruction = inherited_reconstruction
        tokens = previous['historical']['tokens'] + sum(a['charged_tokens'] for a in previous['attempts'])
        writing = previous['historical']['writing'] + sum(a['stage'] == 'writing' for a in previous['attempts'])
        super().__init__(root, writing_calls=writing, reconstruction_calls=inherited_reconstruction + 3,
                         tokens=previous['limits']['tokens'], historical_writing_calls=writing, historical_tokens=tokens)

    def snapshot(self):
        result = super().snapshot()
        result['calls']['reconstruction'] += self.inherited_reconstruction
        return result

def budget():
    authority = load(OUT / 'authorization.json')
    if digest(PARENT / 'budget/goal-budget.json') != authority['predecessor_sha256']:
        raise GoalStopped('PREDECESSOR_CHANGED')
    return ContinuationBudget(OUT / 'budget', authority['predecessor'], inherited_reconstruction=authority['inherited_reconstruction'])

def prepare():
    if (OUT / 'authorization.json').exists(): raise GoalStopped('ALREADY_PREPARED')
    text = verify_text(PARENT / 'hxp')
    previous = load(PARENT / 'budget/goal-budget.json')
    inherited = load(PARENT / 'authorization.json')['inherited_reconstruction'] + sum(a['stage'] == 'reconstruction' for a in previous['attempts'])
    save(OUT / 'authorization.json', {'request': '2026-09-22: 先补材料清单支持（推荐）并继续验证',
        'scope': 'reuse reviewed text; fresh Brief 2.8 and Generation 2.5 with at most three reconstruction calls, no writing or outer retries',
        'predecessor': previous, 'predecessor_sha256': digest(PARENT / 'budget/goal-budget.json'),
        'inherited_reconstruction': inherited, 'description_sha256': digest(PARENT / 'hxp/design-description.md')})
    (OUT / 'design-description.md').write_bytes((PARENT / 'hxp/design-description.md').read_bytes())
    cfg = load(PARENT / 'config.json')
    cfg.update(output=str(OUT.relative_to(ROOT)), budget_root=str((OUT / 'budget').relative_to(ROOT)),
               design_brief_schema='text2ifc/design-brief/2.8', bim_json_schema_version='bim-json/2.5',
               position_tolerance_mm=1.0, dimension_tolerance_mm=1.0, comparison_version='1.1',
               max_reconstruction_calls=3, max_writing_calls=0)
    save(OUT / 'config.json', cfg)
    save(OUT / 'original-source.json', {'path': str(SOURCE), 'sha256': digest(SOURCE)})
    print({'prepared': True, 'characters': len(text), 'budget': budget().snapshot()['calls']})

def validate():
    import pytest, ifcopenshell, shapely
    from scripts.ifc2text.validate_goal import OfflineRecorder
    directory = OUT / 'validation'; directory.mkdir(exist_ok=False)
    before = fingerprint(); save(directory / 'source-snapshot.json', before)
    start = now(); observer = OfflineRecorder(); stream = io.StringIO()
    args = [*TARGETS, '-q', '-p', 'no:cacheprovider', '--basetemp=' + str(directory / 'pytest-temp'), '--junitxml=' + str(directory / 'tests.xml')]
    with observer.network_guard(), contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        code = int(pytest.main(args, plugins=[observer]))
    log = stream.getvalue(); (directory / 'pytest.log').write_text(log, encoding='utf-8')
    valid = code == 0 and not observer.counts['failed'] and not observer.counts['skipped'] and not observer.setup_errors and not observer.network_attempts and before == fingerprint()
    record = {'status': 'admitted' if valid else 'blocked', 'stage': 'reviewed IFC2Text 0.8 -> Brief 2.8 -> Generation 2.5 -> Compare 1.1',
        'authority': 'exact file SHA-256 snapshot including dirty/new files', 'snapshot_sha256': digest(directory / 'source-snapshot.json'),
        'config_sha256': digest(OUT / 'config.json'), 'started_at': start, 'finished_at': now(),
        'python': platform.python_version(), 'ifcopenshell': ifcopenshell.version, 'shapely': shapely.__version__,
        'command': args, 'exit_code': code, 'tests': observer.counts, 'setup_errors': observer.setup_errors,
        'network_transport_attempted': bool(observer.network_attempts), 'full_preflight': False, 'source_scope': SCOPE,
        'claim': 'offline stage admission; revealed development case, no system capability claim',
        'matrix': 'same public-chain, rollback, malformed, resume, persistence, source-isolation and geometry suite as v10, plus material-list positive/negative/reopen and 1 mm boundary tests'}
    save(directory / 'admission.json', record)
    print({k: record[k] for k in ('status', 'tests', 'network_transport_attempted')}); print(log[-3000:])
    return 0 if valid else 1

def admitted():
    record = load(OUT / 'validation/admission.json')
    if record['status'] != 'admitted': raise GoalStopped('ADMISSION_REQUIRED')
    if digest(OUT / 'validation/source-snapshot.json') != record['snapshot_sha256'] or load(OUT / 'validation/source-snapshot.json') != fingerprint():
        raise GoalStopped('CODE_CHANGED_SINCE_ADMISSION')
    if digest(OUT / 'config.json') != record['config_sha256']: raise GoalStopped('CONFIG_CHANGED')
    if digest(SOURCE) != load(OUT / 'original-source.json')['sha256']: raise GoalStopped('SOURCE_CHANGED')
    expected = load(OUT / 'authorization.json')['description_sha256']
    if digest(OUT / 'design-description.md') != expected or digest(PARENT / 'hxp/design-description.md') != expected:
        raise GoalStopped('DESCRIPTION_CHANGED')

def live(stage):
    admitted(); cfg = load(OUT / 'config.json'); b = budget(); attempt = OUT / 'reconstruction'
    marker = OUT / (stage + '-started.json')
    if marker.exists(): raise GoalStopped('SINGLE_ATTEMPT_ALREADY_STARTED')
    if stage == 'generate' and load(OUT / 'brief-result.json')['status'] != 'ready': raise GoalStopped('READY_BRIEF_REQUIRED')
    b.check_capacity('reconstruction')
    save(marker, {'stage': stage, 'at': now(), 'meaning': 'pretransport start marker; transport counts are in budget ledger'})
    conf, client, provider = runtime(cfg, b, 'reconstruction', 131072)
    save(OUT / (stage + '-runtime.json'), {'model': conf.model, 'provider': conf.provider_label, 'max_output_tokens': 131072, 'sdk_retries': 0, 'provider_retries': 0})
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker, run_design_brief_clarification_loop, run_ready_session_to_ifc
    from text2ifc_agent.generation_budget import GenerationBudget, BudgetLimits
    limits = BudgetLimits(max_calls=3, max_tokens=2000000)
    try:
        with SessionStore.open(attempt / 'sessions.sqlite', artifact_root=attempt) as store:
            if stage == 'brief':
                text = (OUT / 'design-description.md').read_text(encoding='utf-8')
                session = store.create_session(original_input=text); GenerationBudget(session.run_dir, limits=limits)
                save(attempt / 'session.json', {'id': session.session_id, 'run_dir': str(session.run_dir)})
                invoker = make_openai_design_brief_invoker(config=conf, run_dir=session.run_dir, client_factory=lambda **_: client,
                    design_review_enabled=False, design_brief_schema_version=cfg['design_brief_schema'])
                value = run_design_brief_clarification_loop(store=store, session=session.session_id, invoke_design_brief=invoker, user_answers=())
                result = {'status': value.status, 'session_id': value.session_id, 'session_hash': value.session_hash}
                if store.get_session(session.session_id).original_input != text: raise GoalStopped('SESSION_TEXT_CHANGED')
            else:
                value = run_ready_session_to_ifc(store=store, session=load(attempt / 'session.json')['id'], provider_factory=lambda: provider,
                    generation_strategy='legacy_full', trace_level='debug', budget_limits=limits, bim_json_schema_version=cfg['bim_json_schema_version'])
                result = {'status': value.status, 'session_hash': value.session_hash, 'ifc_path': str(value.ifc_path) if value.ifc_path else None,
                    'generator_status': value.generator_status, 'audit_status': value.audit_status}
        save(OUT / (stage + '-result.json'), result); admitted()
        print(result); print({'calls': b.snapshot()['calls'], 'tokens': b.snapshot()['tokens_used_or_reserved']})
    except Exception as error:
        b.halt(stage + '_FAILED')
        save(OUT / (stage + '-terminal.json'), {'status': 'failed', 'error_type': type(error).__name__, 'budget': b.snapshot()})
        raise

def compare():
    import json
    from text2ifc_ifc2text.precision_compare_v11 import compare_roundtrip
    run = Path(load(OUT / 'reconstruction/session.json')['run_dir'])
    if not (run / 'output.ifc').exists(): raise GoalStopped('NO_GENERATED_IFC')
    before = digest(SOURCE)
    report = compare_roundtrip(SOURCE, run / 'output.ifc')
    if digest(SOURCE) != before: raise GoalStopped('SOURCE_CHANGED')
    report['generation_result'] = load(OUT / 'generate-result.json')
    report['comparison_role'] = 'diagnostic; file existence does not imply public generation acceptance'
    save(OUT / 'compare-v1.1.json', report)
    lines = ['# 本次整栋重建比较', '', '线性误差不超过 1 mm 视为一致。', '',
             '生成终态：' + report['generation_result']['status'], '',
             json.dumps(report['summary'], ensure_ascii=False), '']
    for category, details in report['categories'].items():
        lines += ['## ' + category, '']
        for row in details['matched']:
            if row['geometry_outside_tolerance'] or row['material_content_difference']:
                lines.append('- ' + json.dumps(row, ensure_ascii=False))
        lines += ['', '缺失：' + json.dumps(details['missing'], ensure_ascii=False),
                  '多余：' + json.dumps(details['extra'], ensure_ascii=False), '']
    lines += ['## 未评估与限制', '', json.dumps(report.get('unassessed', []), ensure_ascii=False),
              json.dumps(report.get('limitations', []), ensure_ascii=False)]
    (OUT / 'COMPARE-v1.1.md').write_text('\n'.join(lines), encoding='utf-8')
    print(report['summary'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('command', choices=['prepare', 'validate', 'brief', 'generate', 'compare', 'status'])
    args = parser.parse_args()
    if args.command == 'validate': raise SystemExit(validate())
    elif args.command in {'brief', 'generate'}: live(args.command)
    elif args.command == 'status': print(budget().snapshot())
    else: globals()[args.command]()
