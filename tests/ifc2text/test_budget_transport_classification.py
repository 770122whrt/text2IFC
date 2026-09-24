"""A budget refusal occurs before SDK transport, and must never be retried."""
from types import SimpleNamespace
import pytest
from text2ifc_ifc2text.goal_budget import BudgetClient, GoalBudget, GoalStopped
from text2ifc_agent.openai_compat import OpenAICompatRuntimeConfig, OpenAICompatibleLiveProvider
from text2ifc_agent.providers import ProviderOutputError


def configuration():
    return OpenAICompatRuntimeConfig(provider='deepseek', provider_label='offline-budget-test',
        api_key='test-secret', api_key_env='TEST_KEY', base_url='https://provider.invalid',
        base_url_env='TEST_URL', model='fixture', model_env='TEST_MODEL', timeout_seconds=1,
        max_completion_tokens=100, max_input_tokens=10000)


def test_local_budget_refusal_is_not_a_connection_error(tmp_path):
    calls = []
    sdk = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **request: calls.append(request))))
    budget = GoalBudget(tmp_path / 'budget', tokens=10)
    client = BudgetClient(sdk, budget, 'reconstruction')
    provider = OpenAICompatibleLiveProvider(config=configuration(), client_factory=lambda **_: client,
        connection_max_attempts=3, sleep=lambda _: pytest.fail('local refusals must not retry'))
    with pytest.raises(ProviderOutputError) as caught:
        provider.generate_live(session_id='budget-repro', prompt='A short audit request', schema={}, state={})
    assert caught.value.details['failure_class'] == 'client_budget_blocked'
    assert caught.value.details['transport_attempts'] == 0
    assert caught.value.details['transport_attempted'] is False
    assert caught.value.details['reason_code'] == 'CUMULATIVE_GOAL_BUDGET_EXCEEDED'
    assert calls == []
    assert budget.snapshot()['attempts'] == []
    assert 'test-secret' not in str(caught.value.details)


def test_direct_budget_wrapper_keeps_goalstopped_compatibility(tmp_path):
    sdk = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_: pytest.fail('transport'))))
    client = BudgetClient(sdk, GoalBudget(tmp_path, tokens=1), 'reconstruction')
    with pytest.raises(GoalStopped):
        client.create(messages=[{'role': 'user', 'content': 'x'}], max_tokens=100)
