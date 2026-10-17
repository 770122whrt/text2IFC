"""Qwen-only gateway uses the existing ledger and scheduler."""
import json
from copy import deepcopy

import httpx
import pytest

from scripts.ifc_repair.qwen_batch import QwenGateway, QwenPolicy, limited_providers, interface_fault
from scripts.ifc_repair.repair_comparison.group_config import default_providers
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from scripts.ifc_repair.repair_comparison.budget import fixed_budget_profile


def make_ledger(tmp_path, arm='G'):
    ledger = Ledger(tmp_path/'control.sqlite')
    work = tmp_path/'workspace'
    work.mkdir()
    ledger.create('case-'+arm, case_id='case', arm=arm, budget=fixed_budget_profile('S1'), metadata={'workspace': str(work)})
    ledger.start('case-'+arm)
    return ledger


def success():
    return httpx.Response(200, json={'choices': [{'message': {'role': 'assistant', 'content': 'ok'}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 100, 'completion_tokens': 2, 'total_tokens': 102}})


def send(gateway, token, *, content='hi'):
    return httpx.post(gateway.url+'/'+token+'/v1/chat/completions', json={
        'model': 'qwen', 'messages': [{'role': 'user', 'content': content}],
        'stream': False, 'max_completion_tokens': 512}, trust_env=False)


def test_retry_success_preserves_failed_attempt_and_does_not_pause(tmp_path):
    ledger = make_ledger(tmp_path)
    calls = []
    def transport(request):
        calls.append(json.loads(request.content))
        return httpx.Response(503, json={'error': 'busy'}) if len(calls) == 1 else success()
    sleeps = []
    with QwenGateway(ledger, tmp_path/'wire', policy=QwenPolicy(backoff_seconds=(.01, .02)),
                     transport=httpx.MockTransport(transport), sleeper=sleeps.append) as gateway:
        token = gateway.register('case-G', model='qwen', api_key=None, endpoints={'chat': 'https://fake.test/v1/chat/completions'}, evidence_class='fake', max_output_tokens=512)
        result = send(gateway, token)
    assert result.status_code == 200 and len(calls) == 2 and calls[0] == calls[1]
    records = ledger.calls('case-G')
    assert len(records) == 2 and records[0]['failed'] and not records[1]['failed']
    assert records[0]['usage'] is None and ledger.snapshot('case-G')['usage']['known_total_tokens'] == 102
    assert not interface_fault(tmp_path, 'case-G')
    assert len(sleeps) == 1


def test_exhausted_endpoint_opens_persistent_circuit_and_pauses_queue(tmp_path):
    ledger = make_ledger(tmp_path)
    calls = []
    def transport(request):
        calls.append(1)
        return httpx.Response(503, json={'error': 'busy'})
    policy = QwenPolicy(backoff_seconds=(0, 0), cooldown_seconds=60)
    with QwenGateway(ledger, tmp_path/'wire', policy=policy, transport=httpx.MockTransport(transport)) as gateway:
        token = gateway.register('case-G', model='qwen', api_key=None, endpoints={'chat': 'https://fake.test/v1/chat/completions'}, evidence_class='fake', max_output_tokens=512)
        assert send(gateway, token).status_code == 503
    assert len(calls) == 3 and interface_fault(tmp_path, 'case-G')
    with QwenGateway(ledger, tmp_path/'wire', policy=policy, transport=httpx.MockTransport(transport)) as restored:
        token = restored.register('case-G', model='qwen', api_key=None, endpoints={'chat': 'https://fake.test/v1/chat/completions'}, evidence_class='fake', max_output_tokens=512)
        blocked = send(restored, token)
    assert blocked.status_code == 503 and blocked.json()['error'] == 'QWEN_ENDPOINT_COOLDOWN'
    assert len(calls) == 3


@pytest.mark.parametrize('status', [400, 401, 403])
def test_non_transient_errors_are_not_retried(tmp_path, status):
    ledger = make_ledger(tmp_path)
    with QwenGateway(ledger, tmp_path/'wire', policy=QwenPolicy(), transport=httpx.MockTransport(lambda _: httpx.Response(status, json={'error': 'bad request'}))) as gateway:
        token = gateway.register('case-G', model='qwen', api_key=None, endpoints={'chat': 'https://fake.test/v1/chat/completions'}, evidence_class='fake', max_output_tokens=512)
        assert send(gateway, token).status_code == status
    assert len(ledger.calls('case-G')) == 1


def test_projection_happens_before_budget_reservation_and_preserves_request(tmp_path):
    ledger = make_ledger(tmp_path)
    received = []
    def transport(request):
        received.append(json.loads(request.content))
        return success()
    # The public request itself is protected, so its over-limit rejection makes
    # no HTTP attempt and records the explicit controller reason.
    with QwenGateway(ledger, tmp_path/'wire', policy=QwenPolicy(context_tokens=8000, output_tokens=512), transport=httpx.MockTransport(transport)) as gateway:
        token = gateway.register('case-G', model='qwen', api_key=None, endpoints={'chat': 'https://fake.test/v1/chat/completions'}, evidence_class='fake', max_output_tokens=512)
        result = send(gateway, token, content='x'*20000)
    assert result.status_code == 403 and 'PROTECTED_CONTEXT_EXCEEDS_WINDOW' in result.text
    assert not received and not ledger.calls('case-G')


def test_provider_configuration_only_changes_qwen():
    original = default_providers()
    before = deepcopy(original)
    configured = limited_providers(original, QwenPolicy())
    assert original == before
    assert configured['deepseek'] == original['deepseek'] and configured['gpt'] == original['gpt']
    assert configured['qwen']['max_output_tokens'] == 8192
    assert configured['qwen']['request_options']['chat_template_kwargs'] == {'enable_thinking': False}


def test_compacted_g_history_reaches_wire_and_archive_is_recoverable(tmp_path):
    from scripts.ifc_repair.repair_comparison.neutral_tools import NeutralTools
    from tests.ifc_repair.test_qwen_context import pair
    ledger = make_ledger(tmp_path)
    received = []
    def transport(request):
        received.append(json.loads(request.content))
        return success()
    messages = [{'role': 'system', 'content': 'protocol'}, {'role': 'user', 'content': '修复窗。'}]
    for i in range(9):
        messages += pair(i, 'public data\n'*5000)
    with QwenGateway(ledger, tmp_path/'wire', policy=QwenPolicy(), transport=httpx.MockTransport(transport)) as gateway:
        token = gateway.register('case-G', model='qwen', api_key=None, endpoints={'chat': 'https://fake.test/chat'}, evidence_class='fake', max_output_tokens=8192)
        result = httpx.post(gateway.url+'/'+token+'/v1/chat/completions', trust_env=False, json={
            'model': 'qwen', 'messages': messages, 'max_tokens': 8192})
    assert result.status_code == 200
    wire = json.dumps(received[0], ensure_ascii=False, separators=(',', ':')).encode()
    assert len(wire)+8192+2048 <= 50000
    archive = next((tmp_path/'workspace'/'.qwen-context').glob('*.txt'))
    tools = NeutralTools(tmp_path/'workspace', tool_seconds=120)
    reread = tools.read_file(archive.relative_to(tmp_path/'workspace').as_posix(), offset=0, limit=4096)
    assert 'public data' in reread['text']
    assert any(e['payload']['mode'] == 'tool_archive' for e in ledger.events('case-G') if e['kind'] == 'qwen_context_projection')


def test_retry_reservation_does_not_reset_cumulative_budget(tmp_path):
    ledger = make_ledger(tmp_path)
    # One preexisting call consumes all but one allowed attempt.
    state = ledger.snapshot('case-G')
    for i in range(state['limits']['calls']-1):
        ledger.reserve('case-G', 'old-'+str(i), 1)
        ledger.settle('case-G', 'old-'+str(i), usage={'prompt_tokens': 1, 'completion_tokens': 0}, response={'usage_complete': True})
    with QwenGateway(ledger, tmp_path/'wire', policy=QwenPolicy(backoff_seconds=(0, 0)), transport=httpx.MockTransport(lambda _: httpx.Response(503, json={'error': 'busy'}))) as gateway:
        token = gateway.register('case-G', model='qwen', api_key=None, endpoints={'chat': 'https://fake.test/chat'}, evidence_class='fake', max_output_tokens=512)
        result = send(gateway, token)
    assert result.status_code == 403 and 'CALL_BUDGET_EXHAUSTED' in result.text
    assert len(ledger.calls('case-G')) == state['limits']['calls']


def test_context_error_gets_one_tighter_projection_not_generic_400_retry(tmp_path):
    ledger = make_ledger(tmp_path)
    received = []
    def transport(request):
        received.append(json.loads(request.content))
        return httpx.Response(400, json={'error': 'maximum context length is 32768 tokens'}) if len(received) == 1 else success()
    with QwenGateway(ledger, tmp_path/'wire', policy=QwenPolicy(), transport=httpx.MockTransport(transport)) as gateway:
        token = gateway.register('case-G', model='qwen', api_key=None, endpoints={'chat': 'https://fake.test/chat'}, evidence_class='fake', max_output_tokens=8192)
        result = send(gateway, token)
    assert result.status_code == 200 and len(received) == 2
    assert any(e['payload'].get('trigger') == 'upstream_context_error' for e in ledger.events('case-G') if e['kind'] == 'qwen_context_projection')
    assert not interface_fault(tmp_path, 'case-G')


def test_official_local_tokenizer_and_policy_round_trip(tmp_path):
    from scripts.ifc_repair.qwen_context import estimate_input
    from scripts.ifc_repair.qwen_batch import default_policy, policy_document, load_policy_file
    from scripts.ifc_repair.repair_comparison.contracts import write_json
    policy = default_policy()
    assert policy.tokenizer_path is not None
    count, method = estimate_input({'messages': [{'role': 'user', 'content': '修复窗，宽度864毫米。'}]}, policy)
    assert 0 < count < 200 and method == 'local_qwen_tokenizer_json'
    path = tmp_path/'custom-policy.json'
    write_json(path, policy_document(policy))
    assert load_policy_file(path) == policy
