"""Resume live generation from an unchanged live Brief after source-ID metadata repair.

This does not replay a Provider or pretend to perform a new Brief call. The origin
response remains in its failed run. Only a single ID-less user transcript can be
rehydrated with the existing controller; no content or Brief value may change.
"""
import argparse
import contextlib
import dataclasses
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import sys
from urllib.parse import urlparse

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent
ROOT = OUT.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
ORIGIN = SOURCE / 'rerun-01/live-run/runs/0b57f15f4af1b7c7/calls/01-design-brief'
PRIOR_BUDGET = SOURCE / 'rerun-03/live-run/runs/58a394a71cf278c4/generation-budget.json'
LIMITS = {'max_calls': 32, 'max_tokens': 2000000, 'max_active_seconds': 3600}

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, obj):
    with p.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def prepare_source(origin, destination, request, *, case_id, expected_evidence='live'):
    from text2ifc_agent.clarification import ClarificationController
    from text2ifc_agent.design_brief import validate_design_brief
    origin, destination = Path(origin), Path(destination)
    conversation = read(origin / 'conversation.json')
    if conversation != [{'role': 'user', 'content': request}]:
        raise ValueError('Recovery only supports an exact single user turn with missing ID')
    brief = read(origin / 'parsed-output.json')
    metadata = read(origin / 'response-metadata.json')
    raw = read(origin / 'response.raw.json')
    assert metadata['evidence_class'] == expected_evidence
    assert raw['id'] == metadata['response_id']
    assert raw['choices'][0]['finish_reason'] == 'stop'
    assert json.loads(raw['choices'][0]['message']['content']) == brief
    assert json.loads((origin / 'model-text.txt').read_text(encoding='utf-8')) == brief
    assert brief['original_request'] == request and brief['status'] == 'ready'
    selection = read(origin / 'context-selection.json')
    old_issues = validate_design_brief(brief, evidence_catalog=selection['evidence'],
        expected_schema_version='text2ifc/design-brief/2.4', conversation=conversation)
    assert old_issues and {i.code for i in old_issues} == {'SEMANTIC_AUTHORITY_SOURCE_INVALID'}
    turns = ClarificationController.start(case_id=case_id, user_request=request).transcript_dicts()
    issues = validate_design_brief(brief, evidence_catalog=selection['evidence'],
        expected_schema_version='text2ifc/design-brief/2.4', conversation=turns)
    if issues:
        raise ValueError('Recovered source is not valid: ' + repr([dataclasses.asdict(i) for i in issues]))
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(origin / 'parsed-output.json', destination / 'design-brief.json')
    shutil.copyfile(origin / 'context-selection.json', destination / 'context-selection.json')
    for name in ('prompt-rendered.md', 'request.redacted.json', 'response.raw.json', 'model-text.txt'):
        # These are the ORIGINAL transport sidecars, not a claimed new call.
        shutil.copyfile(origin / name, destination / name)
    shutil.copyfile(origin / 'conversation.json', destination / 'origin-conversation.json')
    write(destination / 'conversation.json', turns)
    write(destination / 'validation.json', {'valid': True, 'issue_count': 0, 'issues': [],
        'evidence_class': 'offline_revalidation_of_existing_response'})
    record = {'operation': 'rehydrate_missing_single_turn_identity', 'new_provider_calls': 0,
        'origin_directory': str(origin), 'origin_response_id': raw['id'],
        'origin_evidence_class': expected_evidence,
        'origin_files_sha256': {p.name: sha(p) for p in origin.iterdir() if p.is_file()},
        'brief_sha256': sha(destination / 'design-brief.json'),
        'request_sha256': hashlib.sha256(request.encode('utf-8')).hexdigest(),
        'original_issues': [dataclasses.asdict(i) for i in old_issues],
        'revalidation_issues': [], 'brief_values_changed': False,
        'original_run_remains_failed': True, 'new_llm_brief_call': False}
    record['transport_sidecar_role'] = 'Unchanged original invocation; conversation.json is its explicitly revalidated source catalog, not a new transport.'
    write(destination / 'source-revalidation.json', record)
    write(destination / 'metrics.json', {'case_id': case_id, 'stage': 'design-brief',
        'evidence_class': 'offline_revalidation_of_live_origin' if expected_evidence == 'live' else 'offline_fixture',
        'parse_valid': True, 'schema_semantic_valid': True, 'strict_output_contract_valid': True,
        'design_status': 'ready', 'question_count': 0, 'new_provider_calls': 0,
        'response_id': raw['id'], 'model': raw.get('model'), 'usage': {},
        'source_usage_previously_charged': metadata.get('usage', {}),
        'source_revalidation': 'source-revalidation.json'})
    return record


def execute(*, output, provider_factory, evidence_class, strategy='legacy_full', origin_evidence='live'):
    from text2ifc_agent.generation_budget import GenerationBudget, BudgetLimits
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    request = (SOURCE / 'request.txt').read_text(encoding='utf-8')
    record = {'status': 'running', 'evidence_class': evidence_class,
        'started_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'request_sha256': sha(SOURCE / 'request.txt'), 'limits': LIMITS,
        'prior_budget_sha256': sha(PRIOR_BUDGET), 'generation_strategy': strategy,
        'reused_design_brief': True, 'new_llm_brief_call': False, 'reference_ifc_supplied': False}
    with (output / 'run.log').open('x', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        store = SessionStore.open(output / 'sessions.sqlite', artifact_root=output)
        try:
            session = store.create_session(original_input=request)
            shutil.copyfile(PRIOR_BUDGET, session.run_dir / 'generation-budget.json')
            budget = GenerationBudget(session.run_dir, BudgetLimits(**LIMITS))
            record.update(run_id=session.session_hash, run_dir=str(session.run_dir), budget_before=budget.snapshot())
            source = prepare_source(ORIGIN, session.run_dir / 'calls/00-design-brief', request,
                case_id=session.session_hash, expected_evidence=origin_evidence)
            record['source_revalidation'] = source
            store.append_event(session.session_id, event_type='live_brief_source_revalidated', payload=source)
            store.mark_session_status(session.session_id, 'ready')
            write(output / 'running.json', record)
            result = run_ready_session_to_ifc(store=store, session=session.session_hash,
                provider_factory=provider_factory, generation_strategy=strategy, budget_limits=BudgetLimits(**LIMITS))
            record.update(status=result.status, result=dataclasses.asdict(result))
        except Exception as error:
            record.update(status='exception', exception_type=type(error).__name__)
            raise
        finally:
            if 'budget' in locals(): record['budget_after'] = budget.snapshot()
            if 'session' in locals(): store.export_session(session.session_id)
            record['prior_budget_unchanged'] = sha(PRIOR_BUDGET) == record['prior_budget_sha256']
            record['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
            store.close(); write(output / 'execution.json', record)
    return record


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--live', action='store_true'); args = parser.parse_args()
    admission = read(OUT / 'admission.json'); assert admission['status'] == 'admitted'
    for p, h in admission['files_sha256'].items(): assert sha(ROOT / p) == h, p
    for p, v in admission['dependencies'].items(): assert importlib.metadata.version(p) == v
    if not args.live:
        print('Recovery admission verified; no credentials or network.'); return
    approval = read(OUT / 'authorization.json')
    assert approval['status'] == 'approved' and approval['limits'] == LIMITS
    assert approval['request_sha256'] == sha(SOURCE / 'request.txt')
    assert approval['payload_preview_sha256'] == sha(OUT / 'payload-preview.json')
    assert not (OUT / 'live-run').exists()
    from scripts.agent.run_phase6_2_cli import load_env_file
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config, OpenAICompatibleLiveProvider
    load_env_file(ROOT / '.env'); config = load_openai_compatible_runtime_config(dict(os.environ))
    assert urlparse(config.base_url).hostname == 'api.deepseek.com' and config.model == 'deepseek-v4-flash'
    config = dataclasses.replace(config, max_completion_tokens=98304, max_input_tokens=131072)
    result = execute(output=OUT / 'live-run', provider_factory=lambda: OpenAICompatibleLiveProvider(config=config, connection_max_attempts=1),
        evidence_class='live_generator_audit_with_revalidated_live_brief')
    print(json.dumps({k: result[k] for k in ('status', 'run_id', 'evidence_class')}, ensure_ascii=False))


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support(); main()
