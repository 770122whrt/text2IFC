from copy import deepcopy

import httpx
import pytest


@pytest.mark.parametrize('arm', list('ACG'))
def test_keyless_direct_fixture_uses_the_offered_submit_tool(tmp_path, arm):
    import httpx
    from tests.ifc_repair.repair_comparison.demo_http_fixture import FakeDemoTransport
    fixture = FakeDemoTransport(tmp_path, {'stage': 'repair-comparison-scalable-live'})
    request = httpx.Request('POST', 'https://offline.invalid/case-001-'+arm+'/chat',
                           json={'model':'fake', 'messages':[]})
    fixture(request)
    fixture(request)
    result = fixture(request).json()['choices'][0]
    assert result['finish_reason'] == 'tool_calls'
    assert result['message']['tool_calls'][0]['function']['name'] == 'submit'

from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.budget import fixed_budget_profile
from scripts.ifc_repair.repair_comparison.group_config import (
    SCALABLE_STAGE, default_providers, executor, harness_profile, normalize_providers,
)
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from scripts.ifc_repair.repair_comparison.wire_gateway import WireGateway


def configuration(tmp_path):
    return carrier.batch_configuration(
        cases_root=tmp_path, case_ids=['simple', 'other'],
        budgets={name: fixed_budget_profile('S1') for name in ('simple', 'other')},
        stage=SCALABLE_STAGE, providers=default_providers(),
        case_groups={'simple': ['B', 'E', 'F'], 'other': list('ABCDEFG')},
        scene_grounding=True, b_validation_corrections=2,
    )


def test_seven_groups_share_methods_and_frozen_model_pairs(tmp_path):
    config = configuration(tmp_path)
    assert config['order'][0] == 'simple-F'
    assert set(config['order'][:3]) == {'simple-B', 'simple-E', 'simple-F'}
    assert len(config['order']) == 10
    assert [executor(config, arm) for arm in 'ABCDEFG'] == [
        'direct', 'harness', 'direct', 'dsh', 'harness', 'harness', 'direct']
    assert config['models']['C'] == config['models']['E']
    assert config['models']['F'] == config['models']['G'] == 'ms-gmk85rth'
    assert harness_profile(config, 'F')['provider'] == 'qwen'


def test_provider_config_is_secret_free_and_endpoint_specific():
    providers = normalize_providers(default_providers())
    assert providers['qwen']['key_env'] is None
    assert providers['qwen']['chat_endpoint'].endswith('/ms-gmk85rth/v1/chat/completions')
    bad = deepcopy(providers)
    bad['qwen']['api_key'] = 'forbidden'
    with pytest.raises(ValueError):
        normalize_providers(bad)
    bad = deepcopy(providers)
    bad['qwen']['request_options'] = {'model': 'other'}
    with pytest.raises(ValueError):
        normalize_providers(bad)


def test_old_four_group_configuration_is_unchanged(tmp_path):
    config = carrier.batch_configuration(cases_root=tmp_path, case_ids=['one'],
        budgets={'one': fixed_budget_profile('S1')}, stage=carrier.DEMO_STAGE)
    assert config['models'] == carrier.MODELS
    assert config['order'] == ['one-A', 'one-B', 'one-C', 'one-D']
    assert 'providers' not in config


def test_changed_endpoint_invalidates_persisted_configuration(tmp_path):
    config = configuration(tmp_path)
    persisted = {'mode': 'offline', **deepcopy(config), 'configuration': deepcopy(config),
                 'routes': {run_id: {} for run_id in config['order']}}
    assert carrier.validate_configuration(persisted) == config
    persisted['providers']['qwen']['chat_endpoint'] = 'https://other.invalid/v1/chat/completions'
    with pytest.raises(ValueError, match='EXPERIMENT_CONFIGURATION_CHANGED'):
        carrier.validate_configuration(persisted)


@pytest.mark.parametrize('output_limit', [8192, 32768])
def test_qwen_gateway_omits_auth_and_applies_frozen_options(tmp_path, output_limit):
    ledger = Ledger(tmp_path / 'control.sqlite')
    ledger.create('one-F', case_id='one', arm='F', budget=fixed_budget_profile('S1'), mode='offline_development')
    ledger.start('one-F')
    received = []
    def transport(request):
        received.append(request)
        return httpx.Response(200, json={'choices': [{'message': {'role': 'assistant', 'content': '{}'}}],
                                        'usage': {'prompt_tokens': 10, 'completion_tokens': 2}})
    with WireGateway(ledger, tmp_path / 'wire', transport=httpx.MockTransport(transport)) as gateway:
        token = gateway.register('one-F', model='ms-gmk85rth', api_key=None,
            endpoints={'chat': 'https://qwen.invalid/v1/chat/completions'}, evidence_class='fake',
            request_options={'temperature': 0.6, 'top_p': 0.95, 'enable_thinking': False}, max_output_tokens=output_limit)
        response = httpx.post(gateway.url + '/' + token + '/v1/chat/completions',trust_env=False,
            json={'model': 'ms-gmk85rth', 'messages': [{'role': 'user', 'content': 'public'}],
                  'max_completion_tokens': output_limit})
    assert response.status_code == 200, response.text
    assert 'authorization' not in received[0].headers
    import json
    body = json.loads(received[0].content)
    assert body['messages'][0]['content'] == 'public'
    assert body['model'] == 'ms-gmk85rth'
    assert body['enable_thinking'] is False
    assert body['temperature'] == 0.6 and body['top_p'] == 0.95
    assert body['max_completion_tokens'] == output_limit
    assert ledger.snapshot('one-F')['usage']['known_total_tokens'] == 12
    assert ledger.snapshot('one-F')['usage']['reserved_tokens'] == 0
