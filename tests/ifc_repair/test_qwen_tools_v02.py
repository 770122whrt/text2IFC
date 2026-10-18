"""Literal JSON controls are normalized; invalid calls still fail closed."""
import json

import httpx
import pytest

from scripts.ifc_repair import qwen_tools as base, qwen_tools_v02 as candidate
from scripts.ifc_repair.qwen_batch import QwenPolicy
from scripts.ifc_repair.repair_comparison.isolated_direct import TOOLS
from tests.ifc_repair.test_qwen_batch import make_ledger


def call(arguments):
    return '<tool_call>{"name":"write_file","arguments":'+arguments+'}</tool_call>'


@pytest.mark.parametrize('value', ['first\nsecond', 'first\r\nsecond', 'first\tsecond'])
def test_original_rejects_literal_control_candidate_preserves_exact_text(value):
    raw = call('{"path":"work/repair.py","text":"'+value+'"}')
    with pytest.raises(ValueError):
        candidate._BASE_DECODE(raw, TOOLS)
    decoded = candidate.decode_tools(raw, TOOLS)
    assert json.loads(decoded[0]['function']['arguments']) == {'path':'work/repair.py','text':value}
    assert decoded == candidate.decode_tools(raw, TOOLS)


def test_escaped_json_is_unchanged():
    raw = call(json.dumps({'path':'work/test.py','text':'print("\\n")\nprint("\\t")'}))
    assert candidate.decode_tools(raw, TOOLS) == candidate._BASE_DECODE(raw, TOOLS)


def test_xml_string_code_is_unchanged():
    raw = '<tool_call><function=write_file><parameter=path>work/a.py</parameter><parameter=text>print("x")\nprint("y")</parameter></function></tool_call>'
    assert candidate.decode_tools(raw, TOOLS) == candidate._BASE_DECODE(raw, TOOLS)


def test_xml_typed_array_accepts_literal_json_newline():
    raw = '<tool_call><function=execute><parameter=argv>["python","-c","print(1)\nprint(2)"]</parameter></function></tool_call>'
    decoded = candidate.decode_tools(raw, TOOLS)
    assert json.loads(decoded[0]['function']['arguments'])['argv'] == ['python','-c','print(1)\nprint(2)']


@pytest.mark.parametrize('raw', [
    call('{"path":"a","path":"b","text":"code"}'),
    call('{"path":"a","text":"a\x00b"}'),
    call('{"path":"a","text":"a\x01b"}'),
    call('{"path":"a","text":"code",}'),
    call("{'path':'a','text':'code'}"),
    call('{"path":"a","text":"code"} {"extra":1}'),
    call('{"path":"a","text":"code","extra":"not offered"}'),
    call('{"path":"a"}'),
    '<tool_call>{"name":"unknown","arguments":{}}</tool_call>',
    '<tool_call>{"name":"execute","arguments":{"argv":true}}</tool_call>',
    '<tool_call>{"name":"execute","arguments":{"argv":[],"timeout_s":NaN}}</tool_call>',
    '<tool_call><function=read_file><parameter=path>a</parameter><parameter=extra>x</parameter></function></tool_call>',
    '<tool_call><function=read_file><parameter=path>a</parameter><parameter=path>b</parameter></function></tool_call>',
])
def test_no_guessing_and_no_weaker_schema_or_whitelist(raw):
    with pytest.raises(ValueError):
        candidate.decode_tools(raw, TOOLS)


@pytest.mark.parametrize('arm', ['F','G'])
def test_gateway_g_compat_preserves_f_raw_response_and_usage(tmp_path, monkeypatch, arm):
    monkeypatch.setattr(base, 'decode_tools', candidate.decode_tools)
    monkeypatch.setattr(base, 'VERSION', candidate.VERSION)
    ledger = make_ledger(tmp_path, arm)
    received = []
    raw = call('{"path":"work/test.py","text":"first\nsecond"}')
    def provider(request):
        received.append(json.loads(request.content))
        return httpx.Response(200,json={'choices':[{'message':{'role':'assistant','content':raw},'finish_reason':'stop'}],
            'usage':{'prompt_tokens':100,'completion_tokens':30,'total_tokens':130}})
    with base.ToolGateway(ledger,tmp_path/'wire',policy=QwenPolicy(),transport=httpx.MockTransport(provider)) as gateway:
        token = gateway.register('case-'+arm,model='qwen',api_key=None,endpoints={'chat':'https://fake.invalid/chat'},evidence_class='fake',max_output_tokens=512)
        body = {'model':'qwen','messages':[{'role':'user','content':'public request'}],'max_tokens':512,'stream':False}
        if arm == 'G':
            body['tools'] = TOOLS
        response = httpx.post(gateway.url+'/'+token+'/v1/chat/completions',json=body,trust_env=False)
    assert response.status_code == 200 and len(received) == 1
    assert ledger.calls('case-'+arm)[0]['response']['body']['choices'][0]['message']['content'] == raw
    assert ledger.snapshot('case-'+arm)['usage']['known_total_tokens'] == 130
    message = response.json()['choices'][0]['message']
    if arm == 'G':
        assert json.loads(message['tool_calls'][0]['function']['arguments'])['text'] == 'first\nsecond'
    else:
        assert message['content'] == raw and 'tool_calls' not in message
