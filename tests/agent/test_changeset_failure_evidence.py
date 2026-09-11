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


@pytest.mark.parametrize('entry', ['scoped', 'staged'])
def test_public_loops_stop_after_truncation_without_promoting_candidate(tmp_path, entry):
    import copy
    provider, calls = _provider(_response('truncated'))
    if entry == 'scoped':
        from text2ifc_agent.scoped_loop import run_scoped_changeset_round
        from tests.agent.test_phase6_5_scoped_loop import _candidate as candidate_fixture, _expected as expected_fixture, _issue
        candidate = candidate_fixture()
        frozen = copy.deepcopy(candidate)
        result = run_scoped_changeset_round(provider=provider, output_dir=tmp_path,
            case_id='failure-family', round_number=1, user_request='修正墙名称。',
            conversation=[], design_brief={'status': 'ready'}, expected_facts=expected_fixture(),
            candidate=candidate, issues=[_issue()])
        assert candidate == frozen
    else:
        from text2ifc_agent.staged_generation import run_staged_generation
        from tests.agent.test_phase6_5_staged_generation import _fixture
        skeleton, manifest, expected, _ = _fixture(2)
        frozen = copy.deepcopy(skeleton)
        result = run_staged_generation(provider=provider, output_dir=tmp_path,
            case_id='failure-family', user_request='生成两层建筑。', conversation=[],
            design_brief={'status': 'ready'}, expected_facts=expected, skeleton=skeleton, manifest=manifest)
        assert skeleton == frozen
    assert result['status'] == 'provider_failed' and not result['valid']
    assert len(calls) == 1
    assert not (tmp_path/'candidate.json').exists()
    assert not (tmp_path/'output.ifc').exists()
    assert list(tmp_path.rglob('provider-error.json'))


def test_transport_failure_has_no_fabricated_response(tmp_path):
    from text2ifc_agent.providers import ProviderOutputError
    class FailedConnection:
        def generate_live(self, **kwargs):
            raise ProviderOutputError('connection failed', details={
                'failure_class': 'provider_connection_error', 'request': {'model': 'fixture'}})
    result = _run(tmp_path, FailedConnection())
    assert result['classification'] == 'provider_failed'
    assert not (tmp_path/'response.raw.json').exists()
    assert (tmp_path/'request.redacted.json').is_file()


def test_result_carrying_provider_error_keeps_its_evidence(tmp_path):
    from text2ifc_agent.providers import ProviderOutputError
    from tests.agent.test_phase6_5_changeset_stage import RecordingProvider
    delegate = RecordingProvider(_changeset(_candidate(), _expected()))
    class FailedResult:
        def generate_live(self, **kwargs):
            result = delegate.generate_live(**kwargs)
            raise ProviderOutputError('output rejected', live_result=result)
    result = _run(tmp_path, FailedResult())
    assert result['classification'] == 'provider_failed'
    assert (tmp_path/'response.raw.json').is_file()
