"""Host dispatch/visibility regressions; no Provider or native repair evidence."""
import json
import sqlite3
import sys
from types import SimpleNamespace

import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from tests.ifc_repair.repair_comparison.test_parallel_batch import _parallel_batch, _jobs
from tests.ifc_repair.repair_comparison.test_scalable_controller_safety import _charge


def test_delayed_registration_does_not_queue_competing_starts(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(
        tmp_path, monkeypatch, capacity=7, groups=tuple('ABCDEFG'))
    launched, registered, overlaps, peaks = [], set(), [], []

    class Process:
        def __init__(self, command):
            self.role, self.polls = command[3], 0
            self.process = SimpleNamespace(pid=4242, returncode=None)
            self.tail = b''
            if self.role == 'serve':
                marker = command[command.index('--service-start-id')+1]
                batch.write_json(root/'service.json', {'state': 'running', 'start_id': marker, 'pid': 7777})
            else:
                self.run = command[command.index('--run-id')+1]
                overlaps.append(any(run not in registered for run in launched))
                launched.append(self.run)

        def poll(self):
            if self.role == 'serve':
                return None
            self.polls += 1
            if self.process.returncode is not None:
                return self.process.returncode
            if self.polls >= 2 and self.run not in registered:
                _charge(ledger, self.run)
                registered.add(self.run)
                peaks.append(sum(s['status'] == 'running' for s in batch._states(root)))
            if len(registered) == len(order) and self.polls >= 4:
                ledger.finish(self.run, 'no_output', detail='Synthetic startup sibling.')
                self.process.returncode = 0
                return 0
            return None

        def wait(self, timeout=None):
            return self.process.returncode or 0

    monkeypatch.setattr(batch, '_Process', Process)
    assert batch.run(root) == 0
    assert not any(overlaps)
    assert launched == order and max(peaks) == 7
    assert all(len(ledger.calls(run)) == 1 for run in order)


def test_pre_registration_failure_stops_dispatch_with_reason(tmp_path, monkeypatch, capsys):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, capacity=2)
    launched = []

    class Process:
        def __init__(self, command):
            self.role = command[3]
            self.process = SimpleNamespace(pid=4242, returncode=None)
            self.tail = b''
            if self.role == 'serve':
                marker = command[command.index('--service-start-id')+1]
                batch.write_json(root/'service.json', {'state': 'running', 'start_id': marker, 'pid': 7777})
            else:
                self.run = command[command.index('--run-id')+1]
                launched.append(self.run)

        def poll(self):
            if self.role == 'serve':
                return None
            self.tail = json.dumps({'event': 'attention',
                'reason': 'ValueError: RUN_CONTROLLER_ALREADY_ACTIVE', 'body': 'must stay hidden'}).encode()
            self.process.returncode = 2
            return 2

        def wait(self, timeout=None):
            return self.process.returncode or 0

    monkeypatch.setattr(batch, '_Process', Process)
    assert batch.run(root) == 2
    assert launched == order[:1]
    summary = json.loads(capsys.readouterr().out)
    assert summary['reason'] == 'TASK_PROCESS_EXITED'
    assert summary['run_id'] == order[0]
    assert summary['worker_reason'] == 'ValueError: RUN_CONTROLLER_ALREADY_ACTIVE'
    assert 'body' not in summary and 'stderr' not in summary
    assert all(ledger.snapshot(run)['status'] == 'ready' for run in order)
    assert all(not ledger.calls(run) for run in order)


def test_stdout_failure_tail_is_captured_and_bounded():
    message = json.dumps({'event': 'attention', 'reason': 'ValueError: STARTUP_FAILED'})
    child = batch._Process([sys.executable, '-c',
        'import sys; print("x"*40000); print('+repr(message)+'); sys.exit(2)'])
    assert child.wait(timeout=15) == 2
    assert 0 < len(child.tail) <= 16384
    assert message.encode() in child.tail


@pytest.mark.parametrize('drain_status_locked', [False, True])
def test_controller_database_failure_drains_owned_tasks_before_return(tmp_path, monkeypatch, capsys,
                                                                    drain_status_locked):
    root, ledger, order, stopped = _parallel_batch(tmp_path, monkeypatch)
    launched, processes, _ = _jobs(monkeypatch, root, ledger, order)
    original_control = batch._control
    failed = []

    def locked_once(path, state, **fields):
        if state == 'running' and launched and not failed:
            failed.append(True)
            raise sqlite3.OperationalError('database is locked')
        if state == 'draining' and drain_status_locked:
            raise sqlite3.OperationalError('database is locked during drain status')
        return original_control(path, state, **fields)

    monkeypatch.setattr(batch, '_control', locked_once)
    assert batch.run(root) == 2
    assert launched == order[:2]
    assert all(ledger.snapshot(run)['status'] == 'no_output' for run in launched)
    assert all(ledger.snapshot(run)['status'] == 'ready' for run in order[2:])
    assert all(p.process.returncode == 0 for p in processes if p.role != 'serve')
    assert stopped
    summary = json.loads(capsys.readouterr().out)
    assert summary['reason'] == 'OperationalError: database is locked'
    assert summary['active_count'] == 0
    assert 'failure_site' in summary and 'stderr' not in summary


def test_failed_controller_still_delivers_answer_to_owned_warm_d(tmp_path, monkeypatch, capsys):
    root, ledger, order, stopped = _parallel_batch(tmp_path, monkeypatch, capacity=1, groups=('D', 'B'))
    launched, _, _ = _jobs(monkeypatch, root, ledger, order)
    base_process, original_control = batch._Process, batch._control
    asked, failures, delivered = [], [], []

    class WarmProcess(base_process):
        def poll(self):
            if self.role == 'serve':
                return super().poll()
            if not asked:
                asked.append(self.run)
                ledger.set_native(self.run, {'result': {'session_id': 'offline-warm-d'}})
                ledger.ask(self.run, question_id='width', text='Confirm the public width?')
                with ledger.transaction() as db:
                    db.execute('INSERT INTO batch_control VALUES(?,?)',
                        ('answer:'+self.run, json.dumps({'run_id': self.run, 'answer': {
                            'source': 'user_confirmed', 'question_id': 'width',
                            'event_id': 'offline-user-answer', 'text': 'The width is confirmed.'}})))
                    # Drain must leave non-owned answer entries untouched.
                    db.execute('INSERT INTO batch_control VALUES(?,?)',
                        ('answer:foreign', json.dumps({'run_id': 'foreign', 'answer': {}})))
                return None
            if not delivered:
                return None
            return super().poll()

    def locked_once(path, state, **fields):
        if state == 'running' and launched and not failures:
            failures.append(True)
            raise sqlite3.OperationalError('database is locked')
        return original_control(path, state, **fields)

    def answer(path, run, value):
        delivered.append(run)
        ledger.answer(run, question_id=value['question_id'], text=value['text'], event_id=value['event_id'])

    monkeypatch.setattr(batch, '_Process', WarmProcess)
    monkeypatch.setattr(batch, '_control', locked_once)
    monkeypatch.setattr(batch.carrier, 'answer', answer)
    assert batch.run(root) == 2
    assert launched == delivered == asked == order[:1]
    state = ledger.snapshot(order[0])
    assert state['status'] == 'no_output' and state['native']['result']['session_id'] == 'offline-warm-d'
    assert len(ledger.calls(order[0])) == 1 and not ledger.calls(order[1])
    assert ledger.snapshot(order[1])['status'] == 'ready' and stopped
    with ledger.transaction() as db:
        assert db.execute("SELECT 1 FROM batch_control WHERE key='answer:foreign'").fetchone()
    assert json.loads(capsys.readouterr().out)['active_count'] == 0
