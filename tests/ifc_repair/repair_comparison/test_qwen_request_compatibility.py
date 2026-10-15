"""Offline contract for Qwen's vLLM/SGLang non-thinking request option."""
from copy import deepcopy
import json

import httpx
import pytest

from scripts.ifc_repair.repair_comparison.budget import fixed_budget_profile
from scripts.ifc_repair.repair_comparison.group_config import (
    default_providers,
    normalize_providers,
)
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from scripts.ifc_repair.repair_comparison.wire_gateway import WireGateway


@pytest.mark.parametrize('enabled', [False, True])
def test_qwen_chat_template_switch_is_explicit_and_preserved(enabled):
    providers = default_providers()
    before = deepcopy(providers)
    providers['qwen']['request_options'] = {
        'temperature': 0.6,
        'top_p': 0.95,
        'chat_template_kwargs': {'enable_thinking': enabled},
    }

    normalized = normalize_providers(providers)

    assert normalized['qwen']['request_options'] == providers['qwen']['request_options']
    assert default_providers() == before
    normalized['qwen']['request_options']['chat_template_kwargs']['enable_thinking'] = not enabled
    assert providers['qwen']['request_options']['chat_template_kwargs']['enable_thinking'] is enabled


INVALID_TEMPLATE_OPTIONS = [
    False,
    [],
    {'enable_thinking': 'false'},
    {'enable_thinking': 0},
    {'enable_thinking': None},
    {'enable_thinking': False, 'unknown_template_override': 'not-authorized'},
]


@pytest.mark.parametrize('template_options', INVALID_TEMPLATE_OPTIONS)
def test_invalid_qwen_template_switch_fails_configuration(template_options):
    providers = default_providers()
    providers['qwen']['request_options'] = {'chat_template_kwargs': template_options}

    with pytest.raises(ValueError, match='PROVIDER_REQUEST_OPTIONS_INVALID'):
        normalize_providers(providers)


@pytest.mark.parametrize('template_options', INVALID_TEMPLATE_OPTIONS)
def test_invalid_qwen_template_switch_fails_gateway_registration(tmp_path, template_options):
    ledger = Ledger(tmp_path / 'control.sqlite')
    with WireGateway(ledger, tmp_path / 'wire', transport=httpx.MockTransport(
            lambda request: pytest.fail('Invalid options reached upstream transport'))) as gateway:
        with pytest.raises(ValueError, match='PROVIDER_REQUEST_OPTIONS_INVALID'):
            gateway.register(
                'one-F', model='ms-gmk85rth', api_key=None,
                endpoints={'chat': 'https://qwen.invalid/v1/chat/completions'},
                evidence_class='fake',
                request_options={'chat_template_kwargs': template_options},
            )
        assert not gateway.routes


@pytest.mark.parametrize('arm,limit_field', [('F', 'max_completion_tokens'), ('G', 'max_tokens')])
def test_qwen_wire_uses_nested_switch_for_both_executors(tmp_path, arm, limit_field):
    ledger = Ledger(tmp_path / 'control.sqlite')
    run_id = 'one-' + arm
    ledger.create(run_id, case_id='one', arm=arm, budget=fixed_budget_profile('S1'),
                  mode='offline_development')
    ledger.start(run_id)
    received = []

    def transport(request):
        received.append(request)
        return httpx.Response(200, json={
            'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': '{}'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 2},
        })

    options = {'temperature': 0.6, 'top_p': 0.95,
               'chat_template_kwargs': {'enable_thinking': False}}
    public_request = {
        'model': 'ms-gmk85rth',
        'messages': [{'role': 'user', 'content': 'public fixture'}],
        limit_field: 32768,
        'chat_template_kwargs': {'enable_thinking': True},
    }
    if arm == 'F':
        public_request['response_format'] = {'type': 'json_object'}
    else:
        public_request['tools'] = [{'type': 'function', 'function': {
            'name': 'submit', 'parameters': {'type': 'object', 'properties': {}},
        }}]

    with WireGateway(ledger, tmp_path / 'wire', transport=httpx.MockTransport(transport)) as gateway:
        token = gateway.register(
            run_id, model='ms-gmk85rth', api_key=None,
            endpoints={'chat': 'https://qwen.invalid/v1/chat/completions'},
            evidence_class='fake', max_output_tokens=32768, request_options=options,
        )
        response = httpx.post(gateway.url + '/' + token + '/v1/chat/completions',
                              trust_env=False, json=public_request)

    assert response.status_code == 200, response.text
    assert len(received) == 1
    assert 'authorization' not in received[0].headers
    wire_body = json.loads(received[0].content)
    assert wire_body == {**public_request, **options}
    assert 'enable_thinking' not in wire_body
    assert 'extra_body' not in wire_body
    assert ledger.snapshot(run_id)['usage']['known_total_tokens'] == 12
    assert ledger.snapshot(run_id)['usage']['reserved_tokens'] == 0
