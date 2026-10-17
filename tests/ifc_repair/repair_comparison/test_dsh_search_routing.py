"""Native search forwarding/accounting; no real network or model calls."""
import json
from urllib.error import HTTPError

import httpx
import pytest

from scripts.ifc_repair.repair_comparison.ledger import Ledger
from tests.ifc_repair.repair_comparison.test_wire_gateway import post


def config():
    from scripts.ifc_repair.repair_comparison.dsh_search import search_configuration
    return search_configuration({})


def gateway_fixture(tmp_path, transport, *, enabled=True, calls=5):
    from scripts.ifc_repair.repair_comparison.wire_gateway import WireGateway
    ledger = Ledger(tmp_path / 'control.sqlite')
    ledger.create('search-D', case_id='search', arm='D', budget={
        'tokens': 500000, 'calls': calls, 'active_seconds': 120,
        'tool_seconds': 10, 'extensions': []})
    ledger.start('search-D')
    gateway = WireGateway(ledger, tmp_path / 'wire', transport=httpx.MockTransport(transport))
    token = gateway.register('search-D', model='deepseek-v4-flash', api_key='chat-secret',
        endpoints={'messages': 'https://model.example/messages'},
        evidence_class='deterministic_fake_http',
        web_search=config() if enabled else None,
        search_api_key='search-secret' if enabled else None)
    return gateway, ledger, token


def search_body():
    return {'model': 'deepseek-v4-flash', 'max_tokens': 4096,
            'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': 'IFC documentation'}]}],
            'tools': [{'type': 'web_search_20250305', 'name': 'web_search', 'max_uses': 5}]}


def test_search_has_separate_endpoint_and_key_but_same_task_accounting(tmp_path):
    seen = []
    def upstream(request):
        seen.append(request)
        return httpx.Response(200, json={'type': 'message', 'content': [
            {'type': 'web_search_tool_result', 'tool_use_id': 's1', 'content': [
                {'type': 'web_search_result', 'url': 'https://example.org/ifc', 'title': 'IFC'}]}],
            'usage': {'input_tokens': 7, 'cache_read_input_tokens': 3, 'output_tokens': 2}})
    gateway, ledger, token = gateway_fixture(tmp_path, upstream)
    with gateway:
        _, raw = post(gateway, token, search_body(), 'v1/search/messages')
    assert json.loads(raw)['content'][0]['type'] == 'web_search_tool_result'
    assert str(seen[0].url) == config()['endpoint']
    assert seen[0].headers['x-api-key'] == 'search-secret'
    assert seen[0].headers['authorization'] == 'Bearer search-secret'
    assert ledger.snapshot('search-D')['usage']['known_total_tokens'] == 12
    assert ledger.calls('search-D')[0]['metadata']['stage'] == 'web_search'
    assert 'search-secret' not in ''.join(p.read_text(encoding='utf8') for p in (tmp_path/'wire').rglob('*') if p.is_file())


@pytest.mark.parametrize('change', ['model', 'output', 'tools', 'uses'])
def test_search_refuses_unoffered_model_output_or_server_tool(tmp_path, change):
    seen = []
    gateway, ledger, token = gateway_fixture(tmp_path, lambda request: seen.append(request))
    body = search_body()
    if change == 'model': body['model'] = 'other'
    if change == 'output': body['max_tokens'] = 4097
    if change == 'tools': body['tools'][0]['type'] = 'code_execution'
    if change == 'uses': body['tools'][0]['max_uses'] = 6
    with gateway, pytest.raises(HTTPError) as error:
        post(gateway, token, body, 'v1/search/messages')
    assert error.value.code == 403 and not seen
    assert ledger.snapshot('search-D')['usage']['calls'] == 0


def test_search_is_unavailable_on_old_routes_and_shares_call_limit(tmp_path):
    gateway, _, token = gateway_fixture(tmp_path/'off', lambda request: None, enabled=False)
    with gateway, pytest.raises(HTTPError) as error:
        post(gateway, token, search_body(), 'v1/search/messages')
    assert error.value.code == 404
    gateway, ledger, token = gateway_fixture(tmp_path/'on', lambda request:
        httpx.Response(200, json={'usage': {'input_tokens': 1, 'output_tokens': 1}}), calls=1)
    with gateway:
        post(gateway, token, search_body(), 'v1/search/messages')
        with pytest.raises(HTTPError) as error:
            post(gateway, token, search_body(), 'v1/search/messages')
        assert json.loads(error.value.read())['error'] == 'CALL_BUDGET_EXHAUSTED'
    assert ledger.snapshot('search-D')['usage']['calls'] == 1


def test_search_configuration_and_key_are_separate_from_chat_endpoint():
    from scripts.ifc_repair.repair_comparison.dsh_search import search_configuration, search_api_key
    settings = search_configuration({'OPENAI_BASE_URL': 'https://chat.example/v1'})
    assert settings['endpoint'] == 'https://api.deepseek.com/anthropic/v1/messages'
    assert search_api_key({'DEEPSEEK_API_KEY': 'host-only'}, settings) == 'host-only'
    custom = search_configuration({'DEEPSEEK_SEARCH_BASE_URL': 'https://search.example/v1'})
    with pytest.raises(ValueError, match='SEARCH_CREDENTIAL_REQUIRED'):
        search_api_key({'DEEPSEEK_API_KEY': 'host-only'}, custom)
    assert search_api_key({'DEEPSEEK_SEARCH_API_KEY': 'explicit'}, custom) == 'explicit'


def test_native_patch_enables_search_without_host_credentials():
    from scripts.ifc_repair.repair_comparison.dsh.native_worker import runtime_patches
    patches = runtime_patches({'base_url': 'http://repair-gateway:8000/'+'a'*32, 'web_search': config()})
    search = next(p for p in patches if p.get('id') == 'web-search-deepseek')['config']
    assert search['baseURL'].endswith('/v1/search')
    assert search['apiKey'] == 'isolated-dsh-search-no-external-credential'
    assert search['model'] == 'deepseek-v4-flash'
    old = runtime_patches({'base_url': 'http://repair-gateway:8000/'+'a'*32})
    assert not any(p.get('id') == 'web-search-deepseek' for p in old)
