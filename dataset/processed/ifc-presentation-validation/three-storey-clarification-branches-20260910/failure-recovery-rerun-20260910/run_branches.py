"""Fresh Brief/candidate retry with preserved task spend; old runs are immutable."""
import contextlib
import dataclasses
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil

COLLECTION = Path(__file__).resolve().parent
BASE = COLLECTION.parent
ROOT = BASE.parents[3]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prepare_budget_history(prior_budget, *, branch, approval=None):
    """Return a new-session ledger; never edit or refund the original history."""
    history = read(prior_budget)
    if any(a['status'] == 'reserved' for a in history['attempts']):
        raise ValueError('Unsettled prior budget requires inspection before transport')
    if approval is None:
        return history
    previous, amended = approval.get('previous_limits'), approval.get('new_limits', {})
    if (approval.get('status') != 'approved' or approval.get('branch') != branch
        or approval.get('prior_budget_sha256') != sha(prior_budget)
        or previous != history['limits'] or set(amended) != set(previous)
        or amended.get('max_calls') != previous['max_calls']
        or amended.get('max_active_seconds') != previous['max_active_seconds']
        or not isinstance(amended.get('max_tokens'), int)
        or amended['max_tokens'] <= previous['max_tokens']):
        raise ValueError('Budget extension lacks matching explicit authorization')
    return {**history, 'limits': dict(amended)}


def execute(*, case, output, provider_factory, prior_budget=None, budget_approval=None):
    from text2ifc_agent.generation_budget import BudgetLimits, GenerationBudget, BudgetedProvider
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore

    case, output = Path(case), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    turns = read(case / 'conversation.json')
    limits = BudgetLimits()
    record = {'branch': case.name, 'status': 'running', 'limits': dataclasses.asdict(limits),
        'started_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'conversation_origin': 'user-authorized scripted branch; not spontaneous live clarification',
        'reused_design_brief': False}
    def save():
        write(output / 'execution.json', record)
    save()
    with (output / 'run.log').open('x', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        runtime = output / 'runtime'
        runtime.mkdir()
        store = SessionStore.open(runtime / 'sessions.sqlite', artifact_root=runtime)
        try:
            session = store.create_session(original_input=turns[0]['content'])
            record.update(session_hash=session.session_hash, run_dir=str(session.run_dir))
            for turn in turns[1:]:
                store.append_turn(session.session_id, role=turn['role'], text=turn['content'])
            call_dir = session.run_dir / 'calls/01-design-brief'
            if prior_budget is not None:
                prior_budget = Path(prior_budget)
                history = prepare_budget_history(prior_budget, branch=case.name, approval=budget_approval)
                limits = BudgetLimits(**history['limits'])
                write(session.run_dir / 'generation-budget.json', history)
                record['budget_lineage'] = {'source': str(prior_budget), 'sha256': sha(prior_budget),
                    'reused_payloads': False, 'reason': 'Preserve prior task spend, start new Brief and candidate'}
                if budget_approval is not None:
                    record['budget_extension'] = budget_approval
                record['limits'] = dataclasses.asdict(limits)
            elif budget_approval is not None:
                raise ValueError('A budget extension requires its exact prior ledger')
            budget = GenerationBudget(session.run_dir, limits)
            record['budget_before'] = budget.snapshot()
            save()
            brief_result = run_design_brief_stage(provider=BudgetedProvider(provider_factory(), budget),
                output_dir=call_dir, design_review_enabled=True, design_brief_schema_version='text2ifc/design-brief/2.3',
                case={'case_id': session.session_hash, 'user_request': turns[0]['content'],
                      'conversation': turns, 'call_index': 1})
            store.record_agent_call(session.session_id, {'role': 'design_brief', 'call_index': 1, **brief_result})
            record['brief_result'] = brief_result
            if brief_result['valid'] and brief_result['status'] == 'ready':
                shutil.copyfile(call_dir / 'design-brief.json', session.run_dir / 'design-brief.json')
                shutil.copyfile(case / 'reference-review.json', session.run_dir / 'reference-review.json')
                write(session.run_dir / 'design-review-context.json', {
                    'schema_version': 'text2ifc/design-review-context/1.0',
                    'conversation_sha256': sha(call_dir / 'conversation.json'),
                    'concerns': [{
                        'id': 'reference-stair-walking-clearance',
                        'description': '参考 IFC 中反向梯段共用同一平面，首段接近二层北端平台时局部净空为零。此为参考模型发现，仍需独立检查本次 IFC。',
                        'location': '一层通往二层楼梯的北端',
                        'decision': 'revise' if case.name == 'A-revise' else 'retain',
                        'decision_turn_id': turns[-1]['turn_id'], 'decision_quote': turns[-1]['content'],
                        'evidence_path': 'reference-review.json', 'evidence_sha256': sha(session.run_dir / 'reference-review.json')}],
                })
                store.mark_session_status(session.session_id, 'ready')
                result = run_ready_session_to_ifc(store=store, session=session.session_hash,
                    provider_factory=provider_factory, generation_strategy='legacy_full', budget_limits=limits)
                record.update(status=result.status, result=dataclasses.asdict(result))
            else:
                record['status'] = brief_result['status']
                store.mark_session_status(session.session_id, record['status'])
            store.export_session(session.session_id)
        except Exception as error:
            record.update(status='exception', exception_type=type(error).__name__)
            raise
        finally:
            if 'budget' in locals():
                record['budget_after'] = budget.snapshot()
            store.close()
            record['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
            save()
    return record


def main():
    import argparse
    import importlib.metadata as metadata
    import os
    import sys
    from urllib.parse import urlparse
    sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
    parser = argparse.ArgumentParser()
    parser.add_argument('branch', choices=['A-revise', 'B-retain'])
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if (COLLECTION / 'RUN-HOLD.json').exists():
        raise SystemExit('Active run hold: inspect RUN-HOLD.json before any further transport.')
    admission = read(COLLECTION / 'admission.json')
    assert admission['status'] == 'admitted'
    for hold in admission['supersedes_holds']:
        assert hold['sha256'] == sha(ROOT / hold['path'])
    for path, digest in admission['files_sha256'].items():
        assert sha(ROOT / path) == digest, path
    for package, version in admission['dependencies'].items():
        assert metadata.version(package) == version, package
    from scripts.agent.run_phase6_2_cli import load_env_file
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config, OpenAICompatibleLiveProvider
    load_env_file(ROOT / '.env')
    config = load_openai_compatible_runtime_config(dict(os.environ))
    assert urlparse(config.base_url).hostname == 'api.deepseek.com'
    assert config.model == 'deepseek-v4-flash'
    budget_approval = None
    approval_path = COLLECTION / 'A-budget-extension-approval.json'
    if args.branch == 'A-revise' and approval_path.is_file():
        budget_approval = read(approval_path)
        assert budget_approval['preview_sha256'] == sha(COLLECTION / 'A-budget-extension-preview.json')
        prepare_budget_history(ROOT / admission['budget_history'][args.branch],
            branch=args.branch, approval=budget_approval)
    if not args.live:
        print('Fresh-run stage admission, frozen inputs and api.deepseek.com/deepseek-v4-flash verified; no transport.')
        return
    record = execute(case=COLLECTION / 'inputs' / args.branch, output=COLLECTION / args.branch,
        provider_factory=lambda: OpenAICompatibleLiveProvider(config=config),
        prior_budget=ROOT / admission['budget_history'][args.branch] if args.branch in admission['budget_history'] else None,
        budget_approval=budget_approval)
    print(json.dumps({k: record[k] for k in ['branch', 'status', 'session_hash']}, ensure_ascii=True))


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
