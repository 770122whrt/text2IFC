"""Native D cooperative stop and trusted no-output mapping, without Docker."""
from types import SimpleNamespace

import pytest

from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison import isolated_dsh as isolated
from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json
from tests.ifc_repair.repair_comparison.test_batch_clarification_policy import pending
from tests.ifc_repair.repair_comparison.test_d_budget_terminal import run_native_error


REASON = 'UNANSWERED_CLARIFICATION_COMPLETE_INPUT_POLICY'


def test_stop_request_is_question_bound_and_does_not_finish(tmp_path, monkeypatch):
    root, ledger, order = pending(tmp_path, monkeypatch, groups=('D',))
    before = ledger.snapshot(order[0])
    carrier.request_clarification_stop(root, order[0], 'q1')
    assert read_json(root/'runtime'/order[0]/'stop-clarification.json') == {
        'run_id': order[0], 'question_id': 'q1', 'reason': REASON}
    after = ledger.snapshot(order[0])
    assert after['status'] == 'awaiting_user' and after['usage'] == before['usage']
    with pytest.raises(ValueError, match='QUESTION_BINDING'):
        carrier.request_clarification_stop(root, order[0], 'different')


def test_native_owner_waits_for_quiescence_then_stops_and_exports(tmp_path, monkeypatch):
    root, ledger, order = pending(tmp_path, monkeypatch, groups=('D',))
    run = order[0]
    work = root/'workspace'
    work.mkdir()
    native = isolated.NativeDSH(work, root/'runtime'/run, name='unit-d',
        state_volume='unit-d-state', network='unit-internal',
        base_url='http://repair-gateway:8000/'+'a'*32, model='fake', session_id=run)
    write_json(native.control/'stop-clarification.json', {
        'run_id': run, 'question_id': 'q1', 'reason': REASON})
    calls, quiet, stopped = [], [], []
    def docker(*args, **kwargs):
        calls.append(args)
        if args[:2] == ('network', 'inspect'):
            return 'true'
        if args[0] == 'inspect':
            return '[{"State":{"Running":false,"Pid":0}}]'
        if args[0] == 'stop':
            stopped.append(True)
        return ''
    monkeypatch.setattr(isolated, 'docker', docker)
    monkeypatch.setattr(isolated.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0))
    monkeypatch.setattr(isolated.subprocess, 'Popen', lambda *a, **k: SimpleNamespace(
        poll=lambda: 0 if stopped else None, wait=lambda **k: 0))
    def quiescent(packet=None):
        quiet.append(True)
        assert ledger.snapshot(run)['status'] == 'awaiting_user'
        return len(quiet) > 1
    monkeypatch.setattr(native, 'quiescent', quiescent)
    sleeps = []
    def sleep(_):
        sleeps.append(True)
        assert len(sleeps) <= 2, 'Native owner ignored the explicit clarification stop request'
        assert not stopped
        assert ledger.snapshot(run)['status'] == 'awaiting_user'
    monkeypatch.setattr(isolated.time, 'sleep', sleep)
    result = native.run(ledger=ledger, run_id=run)
    assert len(quiet) == 2 and stopped
    assert result == {'ok': False, 'error': REASON, 'question_id': 'q1', 'container_stopped': True}
    assert any(args[:2] == ('cp', 'unit-d:/state/sessions') for args in calls)
    assert calls[-1] == ('rm', 'unit-d')
    assert ledger.snapshot(run)['status'] == 'awaiting_user'  # Only the owner carrier may finish.


def test_carrier_maps_confirmed_stop_to_no_output_without_answer(tmp_path, monkeypatch):
    original = carrier.Ledger.record
    def record(ledger, run_id, kind, payload, **kwargs):
        result = original(ledger, run_id, kind, payload, **kwargs)
        if kind == 'd_native_started':
            ledger.ask(run_id, question_id='q1', text='Need reference', binding={})
        return result
    monkeypatch.setattr(carrier.Ledger, 'record', record)
    result = {'ok': False, 'error': REASON, 'question_id': 'q1', 'container_stopped': True}
    state, runner = run_native_error(tmp_path, monkeypatch, result=result)
    assert state['status'] == 'no_output' and state['question']['question_id'] == 'q1'
    assert not any(e['kind'] == 'answer' for e in runner.ledger.events(state['run_id']))
    assert runner.ledger.events(state['run_id'])[-1]['payload']['detail'] == REASON


def test_carrier_does_not_infer_clarification_from_error_text(tmp_path, monkeypatch):
    state, _ = run_native_error(tmp_path, monkeypatch, result={
        'ok': False, 'error': REASON, 'question_id': 'q1', 'container_stopped': True})
    assert state['status'] == 'runtime_error'
