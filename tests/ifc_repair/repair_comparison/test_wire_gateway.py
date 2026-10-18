import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import httpx
import pytest

from scripts.ifc_repair.repair_comparison.ledger import Ledger


def setup_gateway(tmp_path, handler):
    from scripts.ifc_repair.repair_comparison.wire_gateway import WireGateway
    ledger = Ledger(tmp_path / 'control.sqlite')
    ledger.create('demo-A', case_id='demo', arm='A', budget={
        'tokens': 500000, 'calls': 5, 'active_seconds': 120, 'tool_seconds': 10, 'extensions': []})
    ledger.start('demo-A')
    gateway = WireGateway(ledger, tmp_path / 'wire', transport=httpx.MockTransport(handler))
    token = gateway.register('demo-A', model='frozen-model', api_key='secret-for-upstream-only',
        endpoints={'chat': 'https://model.example/v1/chat/completions', 'messages': 'https://model.example/anthropic/v1/messages'},
        evidence_class='deterministic_fake_http', max_output_tokens=100)
    return gateway, ledger, token


def post(gateway, token, payload, suffix='v1/chat/completions'):
    req = Request(f'{gateway.url}/{token}/{suffix}', data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
    with urlopen(req, timeout=5) as response:
        return response.status, response.read()


def test_raw_chat_and_missing_usage_are_retained_without_secrets(tmp_path):
    seen = []
    def upstream(request):
        seen.append(request)
        return httpx.Response(200, json={'id':'r1','model':'observed-model','choices':[{'message':{'role':'assistant','content':'ok','reasoning_content':'returned reasoning'},'finish_reason':'stop'}]})
    gateway, ledger, token = setup_gateway(tmp_path, upstream)
    with gateway:
        status, body = post(gateway, token, {'model':'frozen-model','messages':[], 'max_tokens':100})
        assert status == 200 and json.loads(body)['id'] == 'r1'
    assert seen[0].headers['authorization'] == 'Bearer secret-for-upstream-only'
    assert ledger.snapshot('demo-A')['usage']['coverage'] == 'unavailable'
    calls = ledger.calls('demo-A')
    assert len(calls) == 1 and calls[0]['response']['body']['model'] == 'observed-model'
    assert 'secret-for-upstream-only' not in ''.join(p.read_text(encoding='utf8') for p in (tmp_path/'wire').rglob('*.json'))


def test_native_sse_input_output_and_thinking_survive_forwarding(tmp_path):
    wire = b'event: message_start\ndata: {"type":"message_start","message":{"id":"s1","usage":{"input_tokens":12,"output_tokens":0}}}\n\nevent: content_block_delta\ndata: {"type":"content_block_delta","delta":{"type":"thinking_delta","thinking":"returned"}}\n\nevent: message_delta\ndata: {"type":"message_delta","usage":{"output_tokens":7}}\n\nevent: message_stop\ndata: {"type":"message_stop"}\n\n'
    gateway, ledger, token = setup_gateway(tmp_path, lambda request: httpx.Response(200, content=wire, headers={'Content-Type':'text/event-stream'}))
    with gateway:
        _, body = post(gateway, token, {'model':'frozen-model','messages':[], 'max_tokens':100,'stream':True}, 'v1/messages')
    assert body == wire
    assert ledger.snapshot('demo-A')['usage']['known_total_tokens'] == 19
    assert ledger.calls('demo-A')[0]['response']['stream_complete'] is True


@pytest.mark.parametrize('stream', [False, True])
def test_messages_cached_input_is_additive_and_raw_counts_survive(tmp_path, stream):
    usage = {'input_tokens': 12, 'cache_read_input_tokens': 40,
             'cache_creation_input_tokens': 6, 'output_tokens': 7}
    if stream:
        start = {'type': 'message_start', 'message': {'usage': {**usage, 'output_tokens': 0}}}
        events = [start, {'type': 'message_delta', 'usage': {'output_tokens': 7}}, {'type': 'message_stop'}]
        raw = ''.join('data: ' + json.dumps(event) + '\n\n' for event in events).encode()
        response = httpx.Response(200, content=raw, headers={'Content-Type': 'text/event-stream'})
    else:
        response = httpx.Response(200, json={'type': 'message', 'usage': usage})
    gateway, ledger, token = setup_gateway(tmp_path, lambda request: response)
    with gateway:
        post(gateway, token, {'model': 'frozen-model', 'messages': [], 'max_tokens': 100,
                             'stream': stream}, 'v1/messages')
    call = ledger.calls('demo-A')[0]
    assert call['usage'] == usage
    assert call['normalized_usage'] == {'input_tokens': 58, 'output_tokens': 7, 'total_tokens': 65}
    assert Ledger(ledger.path).snapshot('demo-A')['usage']['total_tokens'] == 65


@pytest.mark.parametrize('end', ['truncated', 'stop_without_final_usage', 'wrong_chat_done'])
def test_messages_seed_zero_is_not_final_usage(tmp_path, end):
    seed = {'input_tokens': 12, 'cache_read_input_tokens': 40, 'output_tokens': 0}
    events = [{'type': 'message_start', 'message': {'usage': seed}},
              {'type': 'content_block_delta', 'delta': {'type': 'thinking_delta', 'thinking': 'partial'}}]
    if end == 'stop_without_final_usage':
        events.append({'type': 'message_stop'})
    wire = ''.join('data: ' + json.dumps(event) + '\n\n' for event in events).encode()
    if end == 'wrong_chat_done':
        wire += b'data: [DONE]\n\n'
    gateway, ledger, token = setup_gateway(tmp_path, lambda request:
        httpx.Response(200, content=wire, headers={'Content-Type': 'text/event-stream'}))
    with gateway:
        _, returned = post(gateway, token, {'model': 'frozen-model', 'messages': [],
                                           'max_tokens': 100, 'stream': True}, 'v1/messages')
    call = ledger.calls('demo-A')[0]
    assert returned == wire and call['usage'] == seed
    assert call['normalized_usage'] is None
    summary = ledger.snapshot('demo-A')['usage']
    assert summary['total_tokens'] is None and summary['reserved_tokens'] == call['reservation']
    assert ledger.events('demo-A')[-1]['payload']['usage_known'] is False


def test_chat_cache_hit_is_already_in_prompt_total(tmp_path):
    usage = {'prompt_tokens': 58, 'prompt_cache_hit_tokens': 40,
             'prompt_cache_miss_tokens': 18, 'completion_tokens': 7}
    gateway, ledger, token = setup_gateway(tmp_path, lambda request:
        httpx.Response(200, json={'usage': usage}))
    with gateway:
        post(gateway, token, {'model': 'frozen-model', 'messages': [], 'max_tokens': 100})
    assert ledger.snapshot('demo-A')['usage']['total_tokens'] == 65


def test_truncated_and_http_failure_keep_attempts_and_unknown_usage(tmp_path):
    replies = [httpx.Response(503, json={'error':'temporary'}), httpx.Response(200, content=b'event: message_start\ndata: {"type":"message_start","message":{}}\n\n', headers={'Content-Type':'text/event-stream'})]
    gateway, ledger, token = setup_gateway(tmp_path, lambda req: replies.pop(0))
    with gateway:
        with pytest.raises(HTTPError):
            post(gateway, token, {'model':'frozen-model','messages':[],'max_tokens':100})
        post(gateway, token, {'model':'frozen-model','messages':[],'max_tokens':100,'stream':True}, 'v1/messages')
    assert len(ledger.calls('demo-A')) == 2
    assert all(c['failed'] for c in ledger.calls('demo-A'))
    assert ledger.snapshot('demo-A')['usage']['unknown_calls'] == 2


@pytest.mark.parametrize('suffix,model', [('v1/files','frozen-model'),('v1/chat/completions','other-model')])
def test_unoffered_route_or_model_cannot_reach_upstream(tmp_path, suffix, model):
    gateway, ledger, token = setup_gateway(tmp_path, lambda req: pytest.fail('blocked route reached upstream'))
    with gateway, pytest.raises(HTTPError):
        post(gateway, token, {'model':model,'messages':[],'max_tokens':100}, suffix)
    assert not ledger.calls('demo-A')


def test_terminal_task_revokes_model_access(tmp_path):
    gateway, ledger, token = setup_gateway(tmp_path, lambda req: pytest.fail('terminal task reached upstream'))
    ledger.finish('demo-A','no_output')
    with gateway, pytest.raises(HTTPError):
        post(gateway, token, {'model':'frozen-model','messages':[],'max_tokens':100})
    assert not ledger.calls('demo-A')
@pytest.mark.parametrize('raw',[b'null',b'[]',b'"unexpected"'])
def test_non_object_json_is_preserved_as_failed_unknown_usage(tmp_path,raw):
    from scripts.ifc_repair.repair_comparison.wire_gateway import wire_usage
    usage,complete,payload=wire_usage(raw,'application/json','chat')
    assert usage is None and complete is False
    assert payload==json.loads(raw)
    gateway,ledger,token=setup_gateway(tmp_path,lambda req:httpx.Response(200,headers={'Content-Type':'application/json'},content=raw))
    with gateway:
        status,returned=post(gateway,token,{'model':'frozen-model','messages':[],'max_tokens':100})
    assert status==200 and returned==raw
    calls=ledger.calls('demo-A')
    assert len(calls)==1 and calls[0]['state']=='failed' and calls[0]['usage'] is None
    assert ledger.snapshot('demo-A')['usage']['unknown_calls']==1
    assert Path(calls[0]['response']['raw_file']).read_bytes()==raw
