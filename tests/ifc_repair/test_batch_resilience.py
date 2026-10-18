"""Transport and controller fault isolation; no paid Provider or IFC inspection."""
import json
from contextlib import closing
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import httpx
import pytest

from scripts.ifc_repair import batch_resilience as resilience
from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from scripts.ifc_repair.repair_comparison.controller_owner import task_owner
from tests.ifc_repair.repair_comparison.test_parallel_batch import _parallel_batch, _jobs


def gateway(tmp_path, upstream, *, calls=8, policy=None):
    ledger = Ledger(tmp_path/'control.sqlite')
    ledger.create('case-E', case_id='case', arm='E', budget={
        'tokens': 500000, 'calls': calls, 'active_seconds': 120,
        'tool_seconds': 10, 'extensions': []})
    ledger.start('case-E')
    waits = []
    wire = resilience.ResilientGateway(ledger, tmp_path/'wire',
        transport=httpx.MockTransport(upstream), sleeper=waits.append,
        policy=policy or resilience.Policy(backoff_seconds=(1, 2), jitter_fraction=0))
    token = wire.register('case-E', model='frozen-model', api_key='test-secret',
        endpoints={'chat': 'https://test.invalid/v1/chat/completions',
                   'messages': 'https://test.invalid/v1/messages'},
        evidence_class='deterministic_fake_http', max_output_tokens=100)
    return wire, ledger, token, waits


def post(wire, token, *, suffix='chat/completions', stream=False):
    req = Request(f'{wire.url}/{token}/v1/{suffix}', headers={'Content-Type': 'application/json'},
        data=json.dumps({'model': 'frozen-model', 'messages': [],
                         'max_tokens': 100, 'stream': stream}).encode())
    with urlopen(req, timeout=5) as response:
        return response.status, response.read()


def test_429_retry_after_recovers_and_every_attempt_is_accounted(tmp_path):
    replies = [httpx.Response(429, json={'error': {'code': 'rate_limit'}},
                              headers={'Retry-After': '3'}),
               httpx.Response(200, json={'choices': [], 'usage': {
                   'prompt_tokens': 4, 'completion_tokens': 2}})]
    wire, ledger, token, waits = gateway(tmp_path, lambda request: replies.pop(0))
    with wire:
        assert post(wire, token)[0] == 200
    assert waits == [3]
    calls = ledger.calls('case-E')
    assert len(calls) == 2 and [c['failed'] for c in calls] == [1, 0]
    assert calls[0]['response']['body']['error']['code'] == 'rate_limit'
    assert ledger.snapshot('case-E')['usage']['known_total_tokens'] == 6
    assert ledger.snapshot('case-E')['usage']['unknown_calls'] == 1
    assert not resilience.interface_fault(tmp_path, 'case-E')
    assert not resilience.Holds(tmp_path).groups()
    assert 'test-secret' not in json.dumps(calls)


def test_native_d_stream_is_forwarded_unchanged_after_transient_error(tmp_path):
    sse = (b'data: {"type":"message_start","message":{"usage":{"input_tokens":5,"output_tokens":0}}}\n\n'
           b'data: {"type":"content_block_delta","delta":{"type":"thinking_delta","thinking":"evidence"}}\n\n'
           b'data: {"type":"message_delta","usage":{"output_tokens":2}}\n\n'
           b'data: {"type":"message_stop"}\n\n')
    replies = [httpx.Response(503, json={'error': 'busy'}),
               httpx.Response(200, content=sse, headers={'Content-Type': 'text/event-stream'})]
    wire, ledger, token, waits = gateway(tmp_path, lambda request: replies.pop(0))
    with wire:
        assert post(wire, token, suffix='messages', stream=True)[1] == sse
    assert waits == [1]
    assert len(ledger.calls('case-E')) == 2
    assert ledger.calls('case-E')[-1]['normalized_usage']['total_tokens'] == 7


@pytest.mark.parametrize('code', [429, 503, 401])
def test_exhausted_or_auth_fault_holds_only_affected_provider(tmp_path, code):
    seen = []
    def upstream(request):
        seen.append(request)
        return httpx.Response(code, json={'error': 'busy'})
    wire, ledger, token, waits = gateway(tmp_path, upstream)
    with wire, pytest.raises(HTTPError):
        post(wire, token)
    assert len(seen) == (1 if code == 401 else 3)
    assert len(ledger.calls('case-E')) == len(seen)
    assert resilience.Holds(tmp_path).groups() == ['C', 'E']
    assert not resilience.interface_fault(tmp_path, 'case-E')


def test_no_retry_beyond_call_budget(tmp_path):
    seen = []
    wire, ledger, token, waits = gateway(tmp_path,
        lambda req: seen.append(req) or httpx.Response(429, json={'error': 'busy'}), calls=1)
    with wire, pytest.raises(HTTPError):
        post(wire, token)
    assert len(seen) == 1 and len(ledger.calls('case-E')) == 1
    assert ledger.calls('case-E')[0]['failed']
    assert not resilience.Holds(tmp_path).groups()


def test_incomplete_200_stream_is_retried_before_any_content_is_delivered(tmp_path):
    seen = []
    raw = b'data: {"type":"message_start","message":{}}\n\n'
    complete = raw + b'data: {"type":"message_stop"}\n\n'
    replies = [raw, complete]
    wire, ledger, token, waits = gateway(tmp_path, lambda req:
        seen.append(req) or httpx.Response(200, content=replies.pop(0),
                                           headers={'Content-Type': 'text/event-stream'}))
    with wire:
        assert post(wire, token, suffix='messages', stream=True)[1] == complete
    assert len(seen) == 2 and waits == [1]
    assert ledger.calls('case-E')[0]['failed']
    assert not ledger.calls('case-E')[-1]['failed']
    assert not resilience.Holds(tmp_path).groups()


class BrokenResponse(httpx.SyncByteStream):
    def __iter__(self):
        yield b'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n'
        raise httpx.RemoteProtocolError('peer closed connection during body')


def test_200_body_disconnect_recovers_and_charges_each_attempt(tmp_path):
    replies = [httpx.Response(200, stream=BrokenResponse(),
                              headers={'Content-Type': 'text/event-stream'}),
               httpx.Response(200, json={'choices': [], 'usage': {
                   'prompt_tokens': 4, 'completion_tokens': 2}})]
    wire, ledger, token, waits = gateway(tmp_path, lambda request: replies.pop(0))
    with wire:
        code, raw = post(wire, token)
    assert code == 200 and b'partial' not in raw
    assert waits == [1]
    calls = ledger.calls('case-E')
    assert [c['failed'] for c in calls] == [1, 0]
    assert calls[0]['response']['http_status'] == 200
    assert calls[0]['response']['error_type'] == 'RemoteProtocolError'
    assert ledger.snapshot('case-E')['usage']['unknown_calls'] == 1
    assert not resilience.Holds(tmp_path).groups()


def test_repeated_200_disconnect_only_holds_provider_after_all_retries(tmp_path):
    seen = []
    wire, ledger, token, waits = gateway(tmp_path, lambda request:
        seen.append(request) or httpx.Response(200, stream=BrokenResponse(),
                                  headers={'Content-Type': 'text/event-stream'}),
        policy=resilience.Policy(jitter_fraction=0))
    with ledger.transaction() as db:
        state = ledger._load(db, 'case-E')
        state['arm'] = 'B'
        ledger._save(db, state)
    with wire, pytest.raises(HTTPError) as failure:
        post(wire, token)
    assert failure.value.code == 502
    assert len(seen) == 4 and waits == [5, 15, 45]
    calls = ledger.calls('case-E')
    assert len(calls) == 4 and all(c['failed'] for c in calls)
    assert all(c['response']['http_status'] == 200 for c in calls)
    assert resilience.Holds(tmp_path).groups() == ['A', 'B', 'D']
    assert ledger.snapshot('case-E')['usage']['unknown_calls'] == 4


def test_200_disconnect_cannot_publish_partial_content_when_retry_budget_is_empty(tmp_path):
    wire, ledger, token, waits = gateway(tmp_path, lambda request:
        httpx.Response(200, stream=BrokenResponse(), headers={'Content-Type': 'text/event-stream'}), calls=1)
    with wire, pytest.raises(HTTPError) as failure:
        post(wire, token)
    assert failure.value.code == 403
    assert json.loads(failure.value.read()) == {'error': 'CALL_BUDGET_EXHAUSTED', 'origin': 'repair-controller'}
    assert len(ledger.calls('case-E')) == 1
    assert not resilience.Holds(tmp_path).groups()


def test_quota_exhaustion_is_not_blindly_retried(tmp_path):
    wire, ledger, token, waits = gateway(tmp_path, lambda req: httpx.Response(429,
        json={'error': {'code': 'insufficient_quota'}}))
    with wire, pytest.raises(HTTPError):
        post(wire, token)
    assert len(ledger.calls('case-E')) == 1 and not waits
    assert resilience.Holds(tmp_path).groups() == ['C', 'E']


def test_dynamic_provider_hold_does_not_stop_other_groups(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch,
        groups=('E', 'A', 'C', 'B', 'D'))
    resilience.install(root, monkeypatch=monkeypatch)
    # Synthetic process fixture uses the unchanged base command shape.
    monkeypatch.setattr(batch, 'CLI', ['python', '-m', 'carrier'])
    started, _, _ = _jobs(monkeypatch, root, ledger, order, fail_first=True)
    assert batch.run(root) == 0
    assert started == [order[i] for i in (0, 1, 3, 4)]
    assert ledger.snapshot(order[0])['status'] == 'runtime_error'
    assert ledger.snapshot(order[2])['status'] == 'ready'
    summary = batch.brief_status(root)
    assert summary['state'] == 'paused'
    assert summary['held_groups'] == ['C', 'E']
    assert summary['reason'] == 'PROVIDER_GROUPS_HELD'


def test_hold_release_keeps_manual_holds_and_old_terminal_failure(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, groups=('E', 'B', 'C', 'F'))
    batch.set_group_hold(root, ['F'], hold=True, reason='API unavailable')
    resilience.install(root, monkeypatch=monkeypatch)
    monkeypatch.setattr(batch, 'CLI', ['python', '-m', 'carrier'])
    started, _, _ = _jobs(monkeypatch, root, ledger, order, fail_first=True)
    assert batch.run(root) == 0
    before = ledger.snapshot(order[0])
    resilience.Holds(root).release(['C', 'E'], reason='API restored')
    started, _, _ = _jobs(monkeypatch, root, ledger, order)
    assert batch.resume(root) == 0
    assert started == [order[2]]
    assert ledger.snapshot(order[0])['usage'] == before['usage']
    assert ledger.snapshot(order[0])['status'] == before['status']
    assert batch.brief_status(root)['held_groups'] == ['F']


def test_alerts_are_quiet_normally_deduplicated_and_persistent(tmp_path):
    alerts = resilience.Alerts(tmp_path)
    assert not alerts.emit('running', active_count=3)
    assert alerts.emit('attention', reason='PROVIDER_GROUPS_HELD', groups=['C', 'E'])
    assert not alerts.emit('attention', reason='PROVIDER_GROUPS_HELD', groups=['C', 'E'])
    assert alerts.emit('paused', reason='requested_between_tasks')
    assert alerts.emit('complete', completed=10, total=10)
    first = alerts.pending(acknowledge=True)
    assert len(first) == 3 and not alerts.pending(acknowledge=True)
    assert not resilience.Alerts(tmp_path).emit('complete', completed=10, total=10)
    assert len(alerts.pending(acknowledge=False)) == 0


def test_retry_after_dates_and_long_wait_are_not_clamped_early():
    assert resilience.retry_after('Thu, 01 Jan 1970 00:00:10 GMT', now=4) == 6
    assert resilience.retry_after('not a date', now=4) == 0


def test_long_retry_after_opens_hold_instead_of_retrying_early(tmp_path):
    wire, ledger, token, waits = gateway(tmp_path, lambda req: httpx.Response(429,
        json={'error': 'rate limit'}, headers={'Retry-After': '600'}))
    with wire, pytest.raises(HTTPError):
        post(wire, token)
    assert not waits and len(ledger.calls('case-E')) == 1
    assert resilience.Holds(tmp_path).groups() == ['C', 'E']


def test_before_header_connection_error_is_retried_with_unknown_usage(tmp_path):
    requests = []
    def upstream(request):
        requests.append(request)
        if len(requests) == 1:
            raise httpx.ConnectError('connection refused', request=request)
        return httpx.Response(200, json={'choices': [], 'usage': {'prompt_tokens': 2, 'completion_tokens': 1}})
    wire, ledger, token, waits = gateway(tmp_path, upstream)
    with wire:
        assert post(wire, token)[0] == 200
    assert waits == [1] and len(requests) == 2
    assert ledger.calls('case-E')[0]['response']['error_type'] == 'ConnectError'
    assert ledger.snapshot('case-E')['usage']['unknown_calls'] == 1


def test_configure_preserves_frozen_batch_and_refuses_active_task(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch)
    before = (root/'batch.json').read_bytes()
    resilience.configure(root, policy=resilience.Policy(desktop_notifications=False))
    assert (root/'batch.json').read_bytes() == before
    assert resilience.load_policy(root).gpt_requests == 2
    with pytest.raises(ValueError, match='OPERATIONS_POLICY_FROZEN'):
        resilience.configure(root, policy=resilience.Policy(gpt_requests=1))
    ledger.start(order[0])
    with pytest.raises(ValueError, match='QUIESCENT'):
        resilience.configure(root)


def test_repeated_provider_failures_are_isolated_but_runtime_faults_still_block(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, groups=('E', 'B'))
    resilience.install(root, monkeypatch=monkeypatch)
    resilience.Holds(root).hold('E', reason='PROVIDER_INTERFACE_FAILURE')
    states = [{'run_id': 'one-E', 'case_id': 'one', 'arm': 'E', 'status': 'runtime_error',
               'detail': 'PROVIDER_HTTP_429'},
              {'run_id': 'two-E', 'case_id': 'two', 'arm': 'E', 'status': 'runtime_error',
               'detail': 'PROVIDER_HTTP_429'}]
    assert batch.common_failure(states) is None
    for state in states:
        state['detail'] = 'WORKER_BUNDLE_CHANGED'
    assert batch.common_failure(states)['reason'] == 'COMMON_HARNESS_SYSTEM_FAILURE'


def test_watchdog_notifies_owner_loss_once_without_touching_task_status(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch)
    batch._control(root, 'running')
    monkeypatch.setattr(resilience, 'process_alive', lambda pid: False)
    before = [ledger.snapshot(run)['status'] for run in order]
    resilience.watchdog(root)
    resilience.watchdog(root)
    alerts = resilience.Alerts(root).pending()
    assert len(alerts) == 1 and alerts[0]['reason'] == 'CONTROLLER_NOT_RUNNING_CHECKPOINT_RETAINED'
    assert [ledger.snapshot(run)['status'] for run in order] == before


def test_provider_can_be_released_while_an_unrelated_group_is_running(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, groups=('E', 'B'))
    resilience.Holds(root).hold('E', reason='PROVIDER_INTERFACE_FAILURE', run_id=order[0])
    ledger.start(order[1])
    with task_owner(root, 'batch-owner'):
        assert resilience.main(['release-provider', '--root', str(root), '--groups', 'C', 'E',
                                '--reason', 'API restored']) == 0
    assert not resilience.Holds(root).groups()
    assert ledger.snapshot(order[1])['status'] == 'running'


def test_provider_release_refuses_unfinished_affected_group(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, groups=('E', 'B'))
    ledger.start(order[0])
    resilience.Holds(root).hold('E', reason='PROVIDER_INTERFACE_FAILURE', run_id=order[0])
    with pytest.raises(ValueError, match='PROVIDER_RELEASE_REQUIRES_QUIESCENT_GROUPS'):
        resilience.Holds(root).release(['C', 'E'], reason='API restored')
    assert resilience.Holds(root).groups() == ['C', 'E']


def test_released_provider_does_not_retrigger_global_pause_from_old_failures(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, groups=('E', 'E', 'B'))
    resilience.install(root, monkeypatch=monkeypatch)
    states = [{'run_id': run, 'case_id': run.rsplit('-', 1)[0], 'arm': 'E',
               'status': 'runtime_error', 'detail': 'PROVIDER_HTTP_429'} for run in order[:2]]
    for state in states:
        resilience.Holds(root).hold('E', reason='PROVIDER_INTERFACE_FAILURE', run_id=state['run_id'])
    resilience.Holds(root).release(['C', 'E'], reason='API restored')
    assert batch.common_failure(states) is None


def test_alert_cli_summary_includes_automatic_provider_holds(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, groups=('E', 'B'))
    resilience.Holds(root).hold('E', reason='PROVIDER_INTERFACE_FAILURE', run_id=order[0])
    process = subprocess.run([sys.executable, '-B', '-m', 'scripts.ifc_repair.batch_resilience',
                              'alerts', '--root', str(root)], capture_output=True,
                             text=True, encoding='utf8', timeout=30)
    assert process.returncode == 0
    assert json.loads(process.stdout)['summary']['held_groups'] == ['C', 'E']


def test_retry_reserves_fresh_budget_after_wait_including_suspend(tmp_path):
    seen = []
    wire, ledger, token, waits = gateway(tmp_path,
        lambda req: seen.append(req) or httpx.Response(429, json={'error': 'busy'}))
    import time
    wire.sleeper = lambda delay: setattr(ledger, 'clock', lambda: time.time()+1000)
    with wire, pytest.raises(HTTPError):
        post(wire, token)
    assert len(seen) == 1 and len(ledger.calls('case-E')) == 1
    assert any(event['kind'] == 'provider_retry_budget_stopped'
               and event['payload']['reason'] == 'TIME_BUDGET_EXHAUSTED'
               for event in ledger.events('case-E'))
