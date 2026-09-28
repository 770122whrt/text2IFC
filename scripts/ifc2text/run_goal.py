"""Synchronous, budgeted IFC2Text experiment using existing configuration helpers.

Only this task's config is public. Credential loading and SDK construction remain
in the existing Generation entrypoint and Provider adapter, unchanged here.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'src'))

from text2ifc_ifc2text.goal_budget import GoalBudget, BudgetClient, GoalStopped
from text2ifc_ifc2text.hierarchy import make_hierarchy_plan, assemble_hierarchy
from text2ifc_ifc2text.hierarchical_pipeline import run_hierarchical_writing
from text2ifc_ifc2text.observation import extract_description_facts
from text2ifc_ifc2text.roundtrip_compare import compare_roundtrip
from text2ifc_ifc2text.llm_pipeline import _write_json

SCOPE = ['src/text2ifc_ifc2text', 'tests/ifc2text', 'scripts/ifc2text',
         'prompts/agent', 'schemas/ifc2text', 'src/text2ifc_agent',
         'src/text2ifc_compiler', 'src/text2ifc_extractor']


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def git(*args):
    result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True,
                            text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        raise GoalStopped('VERSION_CHECK_FAILED')
    return result.stdout.strip()


def verify_admission(cfg):
    root = ROOT/cfg['output']
    record = load(root/'validation'/'admission.json')
    if record['status'] != 'admitted':
        raise GoalStopped('CURRENT_ADMISSION_REQUIRED')
    if git('status', '--porcelain', '--untracked-files=all', '--', *SCOPE):
        raise GoalStopped('UNCOMMITTED_EXECUTION_SCOPE')
    if git('diff', record['code_commit'], '--', *SCOPE):
        raise GoalStopped('ADMISSION_CODE_CHANGED')
    if cfg != load(root/'config.json'):
        raise GoalStopped('CONFIGURATION_CHANGED')
    return record


def budget_for(cfg):
    history = [load(ROOT/path) for path in cfg['historical_ledgers']]
    calls = sum(len(h['attempts']) for h in history)
    consumed = sum(a['tokens_charged'] for h in history for a in h['attempts'])
    return GoalBudget(ROOT/cfg['budget_root'], writing_calls=cfg['max_writing_calls'],
        reconstruction_calls=cfg['max_reconstruction_calls'], tokens=cfg['max_total_tokens'],
        historical_writing_calls=calls, historical_tokens=consumed)


def runtime_for(cfg, budget, stage):
    from scripts.agent.run_phase6_2_cli import load_env_file, DEFAULT_ENV_FILE
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config, _create_openai_client
    load_env_file(DEFAULT_ENV_FILE)
    runtime = load_openai_compatible_runtime_config(dict(os.environ))
    runtime = replace(runtime, max_input_tokens=cfg['provider_input_tokens'],
        max_completion_tokens=cfg['writing_output_tokens'] if stage == 'writing' else cfg['reconstruction_output_tokens'],
        timeout_seconds=cfg['provider_timeout_seconds'])
    return runtime, BudgetClient(_create_openai_client(config=runtime, client_factory=None), budget, stage)


def run_writing(cfg):
    record = verify_admission(cfg)
    root = ROOT/cfg['output']
    facts = load(root/'source-facts.json')
    source = ROOT/cfg['source']
    original = source.read_bytes()
    if facts != extract_description_facts(source):
        raise GoalStopped('SOURCE_OBSERVATIONS_CHANGED')
    plan = make_hierarchy_plan(facts)
    if plan != load(root/'writing-plan.json'):
        raise GoalStopped('PREPARED_PLAN_CHANGED')
    budget = budget_for(cfg)
    runtime, client = runtime_for(cfg, budget, 'writing')
    from text2ifc_agent.openai_compat import OpenAICompatibleLiveProvider
    provider = OpenAICompatibleLiveProvider(config=runtime,
        client_factory=lambda **_: client, connection_max_attempts=1)
    _write_json(root/'runtime.json', {'provider':runtime.provider_label, 'requested_model':runtime.model,
        'code_commit':record['code_commit'], 'sdk_retries':0, 'adapter_retries':0,
        'writing_output_limit':runtime.max_completion_tokens})
    result = run_hierarchical_writing(plan=plan, output_dir=root/'writing', provider=provider,
        run_id=cfg['run_id'], max_batch_chars=cfg['max_batch_chars'], budget=budget)
    if source.read_bytes() != original:
        budget.halt('SOURCE_CHANGED')
        raise GoalStopped('SOURCE_CHANGED')
    return {**result, 'budget':budget.snapshot()}


def run_reconstruction(cfg):
    verify_admission(cfg)
    root = ROOT/cfg['output']
    budget = budget_for(cfg)
    budget.check_capacity('reconstruction')
    result = load(root/'writing'/'run.json')
    if result['status'] != 'completed':
        raise GoalStopped('COMPLETE_DESCRIPTION_REQUIRED')
    description = (root/'writing'/'design-description.md').read_text(encoding='utf-8')
    expected = assemble_hierarchy(load(root/'writing-plan.json'), load(root/'writing'/'layout-results.json'))
    if description != expected:
        budget.halt('DESCRIPTION_CHANGED')
        raise GoalStopped('DESCRIPTION_CHANGED')
    review = load(root/'content-review.json')
    if review.get('decision') != 'allow_diagnostic_reconstruction':
        raise GoalStopped('CONTENT_REVIEW_REQUIRED')
    output = root/'reconstruction'
    output.mkdir(parents=True, exist_ok=True)
    marker = output/'started.json'
    if marker.exists():
        raise GoalStopped('RECONSTRUCTION_ATTEMPT_ALREADY_EXISTS')
    source = ROOT/cfg['source']
    original = source.read_bytes()
    _write_json(marker, {'description_path':'../writing/design-description.md', 'run_id':cfg['run_id']})
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_agent.generation_budget import GenerationBudget, BudgetLimits
    from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker
    from text2ifc_agent.openai_compat import OpenAICompatibleLiveProvider
    from text2ifc_ifc2text.text2ifc_public import reconstruct_description_with_public_text2ifc
    runtime, client = runtime_for(cfg, budget, 'reconstruction')
    provider = OpenAICompatibleLiveProvider(config=runtime,
        client_factory=lambda **_: client, connection_max_attempts=1)
    limits = BudgetLimits(max_calls=cfg['max_reconstruction_calls'], max_tokens=cfg['max_total_tokens'])
    with SessionStore.open(output/'sessions.sqlite', artifact_root=output) as store:
        def invoke(transcript, call_index):
            session = store.list_sessions()[-1]
            GenerationBudget(session.run_dir, limits=limits)
            invoker = make_openai_design_brief_invoker(config=runtime, run_dir=session.run_dir,
                client_factory=lambda **_: client, design_review_enabled=cfg['design_review_enabled'],
                design_brief_schema_version=cfg['design_brief_schema'])
            return invoker(transcript, call_index)
        try:
            result = reconstruct_description_with_public_text2ifc(description, store=store,
                invoke_design_brief=invoke, provider_factory=lambda:provider,
                generation_strategy=cfg['generation_strategy'], budget_limits=limits)
            session = store.get_session(result['session_id'])
            result['session_run_dir'] = str(session.run_dir)
            if session.original_input != description or source.read_bytes() != original:
                raise GoalStopped('INPUT_OR_SOURCE_CHANGED')
        except Exception as error:
            budget.halt('RECONSTRUCTION_FAILED')
            _write_json(output/'terminal.json', {'status':'failed', 'error_type':type(error).__name__})
            raise
    _write_json(output/'result.json', result)
    if result.get('ifc_path') and Path(result['ifc_path']).is_file():
        comparison = compare_roundtrip(source, result['ifc_path'],
            position_mm=cfg['comparison_position_tolerance_mm'], dimension_mm=cfg['comparison_dimension_tolerance_mm'])
    else:
        comparison = {'status':'not_run', 'reason':'No reconstructed IFC', 'reconstruction_status':result['status']}
    _write_json(root/'compare.json', comparison)
    return {**result, 'budget':budget.snapshot()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['write', 'reconstruct', 'status'])
    parser.add_argument('--config', default='scripts/ifc2text/hxp-goal-v0.3.json')
    args = parser.parse_args()
    cfg = load(ROOT/args.config)
    try:
        action = {'write':run_writing, 'reconstruct':run_reconstruction, 'status':lambda c:budget_for(c).snapshot()}
        result = action[args.command](cfg)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print(json.dumps({'status':'blocked_or_failed', 'error_type':type(error).__name__}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
