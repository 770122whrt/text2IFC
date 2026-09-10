"""Public ChangeSet failure evidence must survive parser/transport rejection."""
import json
from types import SimpleNamespace

import pytest

from text2ifc_agent.generation_budget import BudgetedProvider, BudgetLimits, GenerationBudget, GenerationBudgetExceeded
from text2ifc_agent.openai_compat import OpenAICompatibleLiveProvider, load_openai_compatible_runtime_config
from tests.agent.test_phase6_5_changeset_stage import _run, _candidate, _expected, _changeset


def _provider(payload):
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        return payload
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    config = load_openai_compatible_runtime_config({'TEXT2IFC_PROVIDER': 'deepseek',
        'API_KEY': 'not-a-real-test-key', 'OpenAI_BASE_URL': 'https://provider.invalid',
        'TEXT2IFC_DEEPSEEK_MODEL': 'fixture-model'})
    return OpenAICompatibleLiveProvider(config=config, client_factory=lambda **kwargs: client), calls


def _response(scenario, usage=True):
    payload = {'id': 'offline-response', 'model': 'fixture-model', 'choices': [
        {'finish_reason': 'length' if scenario == 'truncated' else 'stop',
         'message': {'role': 'assistant', 'content': '{"operations":[' if scenario == 'truncated' else
                    'ISO-10303-21;' if scenario == 'forbidden' else
                    'not valid json' if scenario == 'malformed' else json.dumps(_changeset(_candidate(), _expected()))}}]}
    if scenario == 'no_choices':
        payload['choices'] = []
    if usage:
        payload['usage'] = {'prompt_tokens': 11, 'completion_tokens': 7, 'total_tokens': 18}
    return payload


@pytest.mark.parametrize('scenario', ['truncated', 'no_choices', 'forbidden'])
@pytest.mark.parametrize('known_usage', [True, False])
def test_failed_public_stage_preserves_received_response_and_budget(tmp_path, scenario, known_usage):
    payload = _response(scenario, known_usage)
    provider, calls = _provider(payload)
    budget = GenerationBudget(tmp_path/'budget', BudgetLimits(max_calls=2, max_tokens=1000000, max_active_seconds=100))
    result = _run(tmp_path/'stage', BudgetedProvider(provider, budget))
    assert result['classification'] == 'provider_failed' and not result['valid']
    assert len(calls) == 1
    assert json.loads((tmp_path/'stage/response.raw.json').read_text(encoding='utf-8')) == payload
    error = json.loads((tmp_path/'stage/provider-error.json').read_text(encoding='utf-8'))
    assert error['valid'] is False
    assert not (tmp_path/'stage/changeset.json').exists()
    attempt = budget.snapshot()['attempts'][0]
    assert attempt['status'] == 'failed'
    assert attempt['tokens_charged'] == (18 if known_usage else attempt['reserved_tokens'])
    assert 'not-a-real-test-key' not in ''.join(p.read_text(encoding='utf-8') for p in (tmp_path/'stage').glob('*.json'))


@pytest.mark.parametrize('scenario', ['valid', 'malformed'])
def test_normal_or_malformed_json_keeps_existing_stage_contract(tmp_path, scenario):
    payload = _response(scenario)
    provider, calls = _provider(payload)
    result = _run(tmp_path, provider)
    assert result['classification'] == ('changeset' if scenario == 'valid' else 'invalid')
    assert len(calls) == 1
    assert (tmp_path/'response.raw.json').is_file()


def test_budget_exhaustion_still_escapes_before_provider_attempt(tmp_path):
    provider, calls = _provider(_response('valid'))
    budget = GenerationBudget(tmp_path/'budget', BudgetLimits(max_calls=1, max_tokens=1, max_active_seconds=100))
    with pytest.raises(GenerationBudgetExceeded):
        _run(tmp_path/'stage', BudgetedProvider(provider, budget))
    assert calls == []
    assert not (tmp_path/'stage/response.raw.json').exists()
