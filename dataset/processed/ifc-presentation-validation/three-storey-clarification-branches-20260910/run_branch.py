"""Bounded real Generation using public stages and an authorized branch script.

No transport unless --live is explicit and the current admission is valid.
"""

def main():
    import argparse
    import contextlib
    import dataclasses
    import datetime as dt
    import hashlib
    import json
    import os
    from pathlib import Path
    import sys

    base = Path(__file__).resolve().parent
    root = base.parents[3]
    sys.path[:0] = [str(root), str(root / 'src')]
    parser = argparse.ArgumentParser()
    parser.add_argument('branch', choices=['A-revise', 'B-retain'])
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    case = base / args.branch
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    admission = json.loads((base / 'admission.json').read_text(encoding='utf-8'))
    assert admission['status'] == 'admitted'
    for path, digest in admission['files_sha256'].items():
        assert sha(root / path) == digest, path
    import importlib.metadata as metadata
    for package, version in admission['dependencies'].items():
        assert metadata.version(package) == version, package
    from scripts.agent.run_phase6_2_cli import load_env_file
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config, OpenAICompatibleLiveProvider
    load_env_file(root / '.env')
    config = load_openai_compatible_runtime_config(dict(os.environ))
    from urllib.parse import urlparse
    assert urlparse(config.base_url).hostname == 'api.deepseek.com'
    assert config.model == 'deepseek-v4-flash'
    if not args.live:
        print('Current admission, branch input and destination verified; no transport.')
        return

    from text2ifc_agent.generation_budget import BudgetLimits, GenerationBudget, BudgetedProvider
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore

    runtime = case / 'runtime'
    runtime.mkdir(exist_ok=False)
    turns = json.loads((case / 'conversation.json').read_text(encoding='utf-8'))
    limits = BudgetLimits(max_calls=6, max_tokens=800000, max_active_seconds=1800)
    record = {'branch': args.branch, 'status': 'running', 'started_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'conversation_origin': 'user-authorized scripted branch; not spontaneous live clarification',
              'network_transport_attempted': False, 'limits': dataclasses.asdict(limits)}
    def save():
        (case / 'execution.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    save()
    with (case / 'run.log').open('x', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        store = SessionStore.open(runtime / 'sessions.sqlite', artifact_root=runtime)
        try:
            session = store.create_session(original_input=turns[0]['content'])
            record.update(session_hash=session.session_hash, run_dir=session.run_dir.relative_to(root).as_posix())
            for turn in turns[1:]:
                store.append_turn(session.session_id, role=turn['role'], text=turn['content'])
            store.append_event(session.session_id, event_type='authorized_scripted_design_branch', payload={'branch': args.branch, 'conversation_sha256': sha(case / 'conversation.json')})
            budget = GenerationBudget(session.run_dir, limits)
            factory = lambda: OpenAICompatibleLiveProvider(config=config)
            call_dir = session.run_dir / 'calls/01-design-brief'
            record['network_transport_attempted'] = True
            save()
            brief_result = run_design_brief_stage(
                provider=BudgetedProvider(factory(), budget), output_dir=call_dir,
                case={'case_id': session.session_hash, 'user_request': turns[0]['content'], 'conversation': turns, 'call_index': 1},
                design_review_enabled=True,
            )
            record['brief_result'] = brief_result
            store.record_agent_call(session.session_id, {'role': 'design_brief', 'call_index': 1, **brief_result})
            if brief_result['valid'] and brief_result['status'] == 'ready':
                (session.run_dir / 'design-brief.json').write_bytes((call_dir / 'design-brief.json').read_bytes())
                (session.run_dir / 'reference-review.json').write_bytes((case / 'reference-review.json').read_bytes())
                context = {
                    'schema_version': 'text2ifc/design-review-context/1.0',
                    'conversation_sha256': sha(call_dir / 'conversation.json'),
                    'concerns': [{
                        'id': 'reference-stair-walking-clearance',
                        'description': '参考 IFC 中反向梯段共用同一平面，首段接近二层北端平台时局部净空为零。此为参考模型发现，仍需独立检查本次 IFC。',
                        'location': '一层通往二层楼梯的北端',
                        'decision': 'revise' if args.branch == 'A-revise' else 'retain',
                        'decision_turn_id': turns[-1]['turn_id'], 'decision_quote': turns[-1]['content'],
                        'evidence_path': 'reference-review.json', 'evidence_sha256': sha(session.run_dir / 'reference-review.json'),
                    }],
                }
                (session.run_dir / 'design-review-context.json').write_text(json.dumps(context, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                store.mark_session_status(session.session_id, 'ready')
                result = run_ready_session_to_ifc(store=store, session=session.session_hash, provider_factory=factory,
                                                 generation_strategy='legacy_full', budget_limits=limits)
                record.update(status=result.status, result=dataclasses.asdict(result))
            else:
                record['status'] = brief_result['status']
                store.mark_session_status(session.session_id, record['status'])
            store.export_session(session.session_id)
        except Exception as error:
            record.update(status='exception', exception_type=type(error).__name__)
            # Preserve raw stage evidence; do not print credentials from exception strings.
        finally:
            store.close()
            record['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
            save()
    print(json.dumps({'branch': args.branch, 'status': record['status'], 'session_hash': record.get('session_hash')}, ensure_ascii=False))


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
