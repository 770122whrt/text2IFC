"""Public Brief exceptions retain received evidence and never overwrite attempts."""
import json
from types import SimpleNamespace

import pytest

from text2ifc_agent.generation_budget import BudgetedProvider, BudgetLimits, GenerationBudget, GenerationBudgetExceeded
from text2ifc_agent.live_pipeline import run_design_brief_stage, complete_room_case
from text2ifc_agent.openai_compat import OpenAICompatibleLiveProvider, load_openai_compatible_runtime_config


def provider_for(kind, known_usage=True):
    response = {'id': 'offline-brief', 'model': 'fixture', 'choices': [] if kind == 'no_choices' else [
        {'finish_reason': 'length' if kind == 'truncated' else 'stop', 'message': {
            'content': '{"status":' if kind == 'truncated' else 'ISO-10303-21;' if kind == 'forbidden'
            else '' if kind == 'empty' else 'not json', 'reasoning_content': 'synthetic reasoning'}}]}
    if known_usage:
        response['usage'] = {'prompt_tokens': 11, 'completion_tokens': 7, 'total_tokens': 18}
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        if kind == 'connection':
            raise TimeoutError('private-error-detail')
        return response
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    config = load_openai_compatible_runtime_config({'TEXT2IFC_PROVIDER': 'deepseek',
        'API_KEY': 'fixture-secret-key', 'OPENAI_BASE_URL': 'https://example.invalid',
        'TEXT2IFC_DEEPSEEK_MODEL': 'fixture'})
    return OpenAICompatibleLiveProvider(config=config, client_factory=lambda **_: client,
        connection_max_attempts=1), calls, response


@pytest.mark.parametrize('kind', ['truncated', 'no_choices', 'forbidden', 'connection'])
@pytest.mark.parametrize('known_usage', [True, False])
def test_exception_evidence_survives_public_brief_stage(tmp_path, kind, known_usage):
    provider, calls, response = provider_for(kind, known_usage)
    budget = GenerationBudget(tmp_path / 'budget')
    stage = tmp_path / 'stage'
    with pytest.raises(Exception):
        run_design_brief_stage(provider=BudgetedProvider(provider, budget), output_dir=stage,
            case=complete_room_case(), design_brief_schema_version='text2ifc/design-brief/2.3')
    assert len(calls) == 1
    failure = json.loads((stage / 'provider-error.json').read_text(encoding='utf-8'))
    assert failure['stage'] == 'design-brief' and failure['valid'] is False
    assert (stage / 'request.redacted.json').is_file()
    if kind == 'connection':
        assert not (stage / 'response.raw.json').exists()
    else:
        assert json.loads((stage / 'response.raw.json').read_text(encoding='utf-8')) == response
    attempt = budget.snapshot()['attempts'][0]
    assert attempt['status'] == 'failed'
    assert attempt['tokens_charged'] == (18 if known_usage and kind != 'connection' else attempt['reserved_tokens'])
    assert not (stage / 'design-brief.json').exists()
    contents = ''.join(p.read_text(encoding='utf-8') for p in stage.iterdir() if p.is_file())
    assert 'fixture-secret-key' not in contents and 'private-error-detail' not in contents


@pytest.mark.parametrize('artifact', ['input.txt', 'response.raw.json', 'request.redacted.json',
    'provider-error.json', 'design-brief.json', '.design-brief-attempt'])
def test_existing_attempt_is_immutable_before_transport(tmp_path, artifact):
    target = tmp_path / artifact
    target.write_bytes(b'original evidence')
    provider, calls, _ = provider_for('truncated')
    with pytest.raises(Exception, match='DESIGN_BRIEF_ATTEMPT_ALREADY_EXISTS'):
        run_design_brief_stage(provider=provider, output_dir=tmp_path, case=complete_room_case())
    assert not calls
    assert target.read_bytes() == b'original evidence'


@pytest.mark.parametrize('kind', ['empty', 'malformed'])
def test_invalid_returned_content_keeps_existing_rejection(tmp_path, kind):
    provider, calls, response = provider_for(kind)
    result = run_design_brief_stage(provider=provider, output_dir=tmp_path, case=complete_room_case())
    assert not result['valid'] and len(calls) == 1
    assert json.loads((tmp_path / 'response.raw.json').read_text(encoding='utf-8'))['choices'] == response['choices']
    assert not (tmp_path / 'design-brief.json').exists()


def test_budget_rejection_remains_nontransport_failure(tmp_path):
    provider, calls, _ = provider_for('truncated')
    budget = GenerationBudget(tmp_path / 'budget', BudgetLimits(max_tokens=1))
    with pytest.raises(GenerationBudgetExceeded):
        run_design_brief_stage(provider=BudgetedProvider(provider, budget), output_dir=tmp_path / 'stage',
            case=complete_room_case())
    assert not calls and budget.snapshot()['calls_used'] == 0
    assert not (tmp_path / 'stage/response.raw.json').exists()


def test_case_runner_persists_failed_initial_brief_and_does_not_generate(tmp_path):
    import importlib.util
    from pathlib import Path
    path = Path('dataset/processed/ifc-presentation-validation/c-shaped-teaching-building-20260910/run_case.py')
    spec = importlib.util.spec_from_file_location('c_case_runner', path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    provider, calls, payload = provider_for('truncated')
    output = tmp_path / 'public-run'
    with pytest.raises(Exception, match='finish_reason=length'):
        runner.execute(output=output, provider_factory=lambda: provider, evidence_class='synthetic_offline')
    record = json.loads((output / 'execution.json').read_text(encoding='utf-8'))
    assert record['status'] == 'exception' and record['budget_after']['calls_used'] == 1
    assert len(calls) == 1 and not list(output.rglob('*.ifc'))
    response = output / 'runs' / record['run_id'] / 'calls/01-design-brief/response.raw.json'
    assert json.loads(response.read_text(encoding='utf-8')) == payload
