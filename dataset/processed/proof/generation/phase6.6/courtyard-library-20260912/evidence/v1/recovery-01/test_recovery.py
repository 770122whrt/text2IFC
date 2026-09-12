"""Source metadata recovery has no model edits and pays for no replay calls."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest
from text2ifc_agent.context_selection import select_design_brief_context
from text2ifc_agent.generation_budget import GenerationBudget, BudgetLimits
from tests.agent.test_c_plan_run import fixture, Provider


def module():
    spec = importlib.util.spec_from_file_location('courtyard_recovery', Path(__file__).with_name('run_case.py'))
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def origin(tmp_path):
    m = module(); brief, candidate = fixture()
    request = brief['original_request']
    path = tmp_path / 'origin'; path.mkdir()
    content = json.dumps(brief, ensure_ascii=False)
    selection = select_design_brief_context(user_request=request, conversation=[{
        'turn_id': 'turn-user-001', 'role': 'user', 'content': request}], schema_version='bim-json/2.1')
    for name, value in {
        'conversation.json': [{'role': 'user', 'content': request}],
        'parsed-output.json': brief, 'context-selection.json': selection,
        'response-metadata.json': {'evidence_class': 'offline_fixture', 'response_id': 'fixture', 'usage': {}},
        'response.raw.json': {'id': 'fixture', 'model': 'fake', 'choices': [{'finish_reason': 'stop', 'message': {'content': content}}]},
    }.items(): m.write(path / name, value)
    (path / 'model-text.txt').write_text(content, encoding='utf-8')
    (path / 'prompt-rendered.md').write_text('Offline synthetic source fixture, not a live invocation.', encoding='utf-8')
    m.write(path / 'request.redacted.json', {'evidence_class': 'offline_fixture'})
    return m, path, request, brief, candidate


@pytest.mark.parametrize('attack', ['different_request', 'existing_identity', 'truncated', 'changed_response', 'unknown_citation'])
def test_unverifiable_origin_never_publishes_ready_source(tmp_path, attack):
    m, path, request, brief, _ = origin(tmp_path)
    def replace(name, value): (path / name).write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    if attack == 'different_request': request += '另加一层。'
    if attack == 'existing_identity': replace('conversation.json', [{'turn_id': 'existing', 'role': 'user', 'content': request}])
    if attack == 'truncated':
        raw = m.read(path / 'response.raw.json'); raw['choices'][0]['finish_reason'] = 'length'; replace('response.raw.json', raw)
    if attack == 'changed_response':
        brief['known_facts']['appearance'] = {'profile': 'neutral-gray'}; replace('parsed-output.json', brief)
    if attack == 'unknown_citation':
        for value in brief['known_facts']['semantic_review'].values(): value['source_turns'] = ['unoffered-user']
        content = json.dumps(brief, ensure_ascii=False)
        replace('parsed-output.json', brief)
        raw = m.read(path / 'response.raw.json'); raw['choices'][0]['message']['content'] = content; replace('response.raw.json', raw)
        (path / 'model-text.txt').write_text(content, encoding='utf-8')
    before = {p.name: p.read_bytes() for p in path.iterdir()}
    with pytest.raises((ValueError, AssertionError)):
        m.prepare_source(path, tmp_path / 'ready', request, case_id='offline', expected_evidence='offline_fixture')
    assert not (tmp_path / 'ready').exists()
    assert before == {p.name: p.read_bytes() for p in path.iterdir()}


def test_actual_response_revalidates_without_changing_one_byte(tmp_path):
    m = module(); before = {p.name: p.read_bytes() for p in m.ORIGIN.iterdir() if p.is_file()}
    result = m.prepare_source(m.ORIGIN, tmp_path / 'ready', (m.SOURCE / 'request.txt').read_text(encoding='utf-8'), case_id='offline-real-origin')
    assert result['new_provider_calls'] == 0
    assert result['original_run_remains_failed']
    assert (tmp_path / 'ready/design-brief.json').read_bytes() == (m.ORIGIN / 'parsed-output.json').read_bytes()
    for name in ('prompt-rendered.md', 'request.redacted.json', 'response.raw.json', 'model-text.txt'):
        assert (tmp_path / 'ready' / name).read_bytes() == (m.ORIGIN / name).read_bytes()
    assert before == {p.name: p.read_bytes() for p in m.ORIGIN.iterdir() if p.is_file()}


@pytest.mark.parametrize('strategy', ['legacy_full', 'staged'])
def test_public_resume_compiles_with_no_brief_replay_or_budget_reset(tmp_path, strategy):
    m, path, request, brief, candidate = origin(tmp_path)
    m.SOURCE = tmp_path; m.ORIGIN = path
    (tmp_path / 'request.txt').write_text(request, encoding='utf-8')
    budget = GenerationBudget(tmp_path / 'prior', BudgetLimits(**m.LIMITS))
    slot = budget.reserve(stage='previous_failure', reserved_tokens=100)
    budget.settle(slot, usage={'prompt_tokens': 10, 'completion_tokens': 20}, elapsed_seconds=2, failed=True)
    m.PRIOR_BUDGET = budget.path; before = budget.path.read_bytes()
    provider = Provider(brief, candidate)
    result = m.execute(output=tmp_path / 'run', provider_factory=lambda: provider,
        evidence_class='offline_fake', strategy=strategy, origin_evidence='offline_fixture')
    assert result['status'] == 'compiled', result
    assert result['reused_design_brief'] and not result['new_llm_brief_call']
    assert all(c['state']['stage'] not in {'design-brief', 'design-brief-plan-repair', 'design-brief-semantic-repair'} for c in provider.calls)
    assert result['budget_before']['tokens_used_or_reserved'] == 30
    assert result['budget_after']['calls_used'] == len(provider.calls) + 1
    assert budget.path.read_bytes() == before
    assert Path(result['result']['ifc_path']).is_file()
