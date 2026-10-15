"""Controller-only safety checks: fake processes, real task accounting, no Docker/model.

Synthetic gate receipts below exercise admission rejection, not earned admission.
"""
from contextlib import closing
from copy import deepcopy
import json
import sqlite3
import sys
from types import SimpleNamespace

import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as workflow
from scripts.ifc_repair.repair_comparison.contracts import read_json, sha256, write_json
from scripts.ifc_repair.repair_comparison.ledger import Ledger


BUDGET = {'tokens': 100, 'calls': 4, 'active_seconds': 120,
          'tool_seconds': 10, 'extensions': []}


def _batch(tmp_path, monkeypatch, *, groups=('B', 'E'), mode='offline'):
    root = tmp_path/'batch'
    root.mkdir(parents=True)
    order = [f'case-{i:03}-{arm}' for i, arm in enumerate(groups, 1)]
    configuration = {'stage': workflow.SCALABLE_STAGE, 'order': order, 'b': None}
    value = {'schema_version': workflow.PLAN_SCHEMA, 'mode': mode,
             'budget_policy': workflow.TASK_BUDGET_ONLY, 'configuration': configuration,
             'rounds': {'round1': [r.rsplit('-', 1)[0] for r in order], 'round2': []},
             'input_bindings': {}}
    value['sha256'] = workflow._digest(value)
    write_json(root/'batch.json', value)
    config = {'mode': mode, 'configuration': configuration, 'order': order,
              'routes': {run: {'container': 'fake-'+run, 'volume': 'fake-volume-'+run}
                         for run in order}}
    write_json(root/'experiment.json', config)
    ledger = Ledger(root/'control.sqlite')
    for run in order:
        case, arm = run.rsplit('-', 1)
        ledger.create(run, case_id=case, arm=arm, budget=deepcopy(BUDGET),
                      mode='offline_development', metadata={'session_id': 'original-'+run})

    def forbidden(*args, **kwargs):
        pytest.fail('Controller safety tests must not launch Docker, models, or initialize a replacement task.')

    stopped = []
    monkeypatch.setattr(workflow, 'docker', forbidden)
    monkeypatch.setattr(workflow.carrier, 'docker', forbidden)
    monkeypatch.setattr(workflow.carrier, 'initialize', forbidden)
    monkeypatch.setattr(workflow, '_retire_task', lambda *args: None, raising=False)
    monkeypatch.setattr(workflow.carrier, 'request_service_stop', lambda path: stopped.append(str(path)))
    monkeypatch.setattr(workflow.time, 'sleep', lambda seconds: None)
    return root, ledger, order, stopped


def _charge(ledger, run_id, *, failed=False, response=None, known=True):
    state = ledger.snapshot(run_id)
    if state['status'] == 'ready':
        ledger.start(run_id)
    ledger.reserve(run_id, 'original-call', 20, {'stage': 'offline controller fixture'})
    ledger.settle(run_id, 'original-call', usage={'prompt_tokens': 3, 'completion_tokens': 2} if known else None,
                  response=response or {'body': {'choices': []}}, failed=failed)


def _processes(monkeypatch, root, ledger, job, *, ready=True, service_exit_after=None, ready_pid=4242):
    started, processes = [], []

    class FakeProcess:
        def __init__(self, command):
            self.role = command[3]
            self.process = SimpleNamespace(pid=4242 if self.role == 'serve' else 4243, returncode=None)
            self.tail = b'offline process fixture'
            self.polls = 0
            self.poll_hook = None
            self.waited = False
            processes.append(self)
            if self.role == 'serve':
                if ready:
                    marker = command[command.index('--service-start-id')+1] if '--service-start-id' in command else None
                    write_json(root/'service.json', {'state': 'running', 'pid': ready_pid, 'start_id': marker})
            else:
                run_id = command[command.index('--run-id')+1]
                started.append(run_id)
                job(ledger, run_id, self)

        def poll(self):
            self.polls += 1
            if self.role == 'serve':
                if service_exit_after is not None and self.polls >= service_exit_after:
                    self.process.returncode = 1
                    return 1
                return None
            return self.poll_hook(self) if self.poll_hook else 0

        def wait(self, timeout=None):
            self.waited = True
            self.process.returncode = self.process.returncode or 0
            return self.process.returncode

    monkeypatch.setattr(workflow, '_Process', FakeProcess)
    return started, processes


def _no_output(ledger, run_id, process):
    if ledger.snapshot(run_id)['status'] == 'ready':
        _charge(ledger, run_id)
    ledger.finish(run_id, 'no_output', detail='No explicit IFC submission in offline fixture.')


def test_public_run_returns_one_summary_without_per_task_details(tmp_path, monkeypatch, capsys):
    root, ledger, order, _ = _batch(tmp_path, monkeypatch)
    started, _ = _processes(monkeypatch, root, ledger, _no_output)
    assert workflow.main(['run', '--root', str(root)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    summary = json.loads(lines[0])
    assert summary['event'] == 'summary' and summary['state'] == 'complete'
    assert summary['completed'] == summary['total'] == 2
    assert summary['status_counts'] == {'no_output': 2}
    assert started == order
    assert 'No explicit IFC' not in lines[0] and 'task_complete' not in lines[0]
    assert len(lines[0].encode('utf8')) < 2048


def test_summary_filters_question_and_process_details(capsys):
    workflow._emit('task_started', run_id='one-F')
    workflow._emit('task_complete', reason='private task detail')
    workflow._emit('attention', reason='CLARIFICATION_REQUIRED', run_id='one-F',
                   question={'text': 'Private question body'}, stderr='Private process log',
                   response={'reasoning_content': 'Private reasoning'}, warm_owner=True)
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {'event': 'summary', 'state': 'attention',
        'reason': 'CLARIFICATION_REQUIRED', 'run_id': 'one-F', 'warm_owner': True}
    assert 'Private' not in lines[0]


def test_preinitialization_error_is_one_summary_without_traceback(tmp_path, capsys):
    assert workflow.main(['run', '--root', str(tmp_path/'missing-batch')]) == 2
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert len(lines) == 1 and not captured.err
    assert json.loads(lines[0])['event'] == 'summary'
    assert json.loads(lines[0])['state'] == 'attention'
    assert 'Traceback' not in lines[0] and len(lines[0].encode('utf8')) < 2048


def test_public_entry_help_exposes_batch_commands(monkeypatch, capsys):
    from scripts.ifc_repair.repair_comparison import batch_operator
    monkeypatch.setattr(sys, 'argv', ['batch_operator', '--help'])
    with pytest.raises(SystemExit) as stopped:
        batch_operator.main()
    assert stopped.value.code == 0
    help_text = capsys.readouterr().out
    assert all(command in help_text for command in ('prepare', 'run', 'pause', 'resume', 'status'))


def test_pause_resume_preserves_session_native_state_and_consumed_budget(tmp_path, monkeypatch):
    root, ledger, order, _ = _batch(tmp_path, monkeypatch, groups=('B',))
    run_id = order[0]
    _charge(ledger, run_id)
    ledger.set_native(run_id, {'result': {'session_id': 'native-original', 'status': 'in_progress'}})
    before = ledger.snapshot(run_id)
    started, _ = _processes(monkeypatch, root, ledger, _no_output)
    workflow.pause(root)
    assert workflow.run(root) == 0
    paused = ledger.snapshot(run_id)
    assert not started and paused['status'] == 'running'
    assert paused['usage'] == before['usage']
    assert paused['native'] == before['native']
    assert paused['metadata'] == before['metadata']
    assert workflow.resume(root) == 0
    after = ledger.snapshot(run_id)
    assert started == [run_id]
    assert after['usage'] == before['usage']
    assert after['native'] == before['native']
    assert after['limits'] == before['limits']
    assert after['started'] == before['started']
    assert after['active_elapsed_s'] >= before['active_elapsed_s']


def test_no_output_advances_and_exports_once_into_the_shared_ledger(tmp_path, monkeypatch):
    root, ledger, order, _ = _batch(tmp_path, monkeypatch)
    started, _ = _processes(monkeypatch, root, ledger, _no_output)
    assert workflow.run(root) == 0
    assert started == order
    assert all(ledger.snapshot(run)['status'] == 'no_output' for run in order)
    status = workflow.brief_status(root)
    assert status['completed'] == 2 and status['known_tokens'] == 10 and status['unknown_calls'] == 0
    assert len(list((root/'results').rglob('report.md'))) == 2
    assert not list((root/'results').rglob('*.ifc'))
    assert list(root.rglob('control.sqlite')) == [root/'control.sqlite']
    with closing(sqlite3.connect(root/'control.sqlite')) as db:
        assert db.execute('SELECT COUNT(*) FROM batch_exports').fetchone()[0] == 2
    assert workflow.run(root) == 0
    assert started == order
    with closing(sqlite3.connect(root/'control.sqlite')) as db:
        assert db.execute('SELECT COUNT(*) FROM batch_exports').fetchone()[0] == 2


def test_single_interface_failure_pauses_without_spending_the_next_task(tmp_path, monkeypatch):
    root, ledger, order, _ = _batch(tmp_path, monkeypatch)

    def interface_failure(ledger, run_id, process):
        _charge(ledger, run_id, failed=True, known=False,
                response={'http_status': 401, 'error_type': 'authentication_error'})
        ledger.finish(run_id, 'runtime_error', detail='PROVIDER_HTTP_401')

    started, _ = _processes(monkeypatch, root, ledger, interface_failure)
    assert workflow.run(root) == 2
    assert started == order[:1]
    assert ledger.snapshot(order[1])['status'] == 'ready'
    assert not ledger.calls(order[1])
    assert workflow.brief_status(root)['reason'] == 'PROVIDER_INTERFACE_FAILURE'
    assert workflow.brief_status(root)['unknown_calls'] == 1


def test_first_environment_isolation_failure_pauses_before_another_task(tmp_path, monkeypatch):
    root, ledger, order, _ = _batch(tmp_path, monkeypatch)

    def isolation_failure(ledger, run_id, process):
        _charge(ledger, run_id)
        ledger.set_native(run_id, {'result': {'error_code': 'DOCKER_ISOLATION_WORKER_FAILED'}})
        ledger.finish(run_id, 'runtime_error', detail='DOCKER_ISOLATION_WORKER_FAILED')

    started, _ = _processes(monkeypatch, root, ledger, isolation_failure)
    assert workflow.run(root) == 2
    assert started == order[:1]
    assert ledger.snapshot(order[1])['status'] == 'ready'
    assert workflow.brief_status(root)['state'] == 'attention'


def test_d_clarification_keeps_the_same_warm_process_session_and_usage(tmp_path, monkeypatch):
    root, ledger, order, stopped = _batch(tmp_path, monkeypatch, groups=('D',))
    run_id = order[0]
    observed = []

    def warm_question(ledger, run_id, process):
        _charge(ledger, run_id)
        ledger.set_native(run_id, {'result': {'session_id': 'warm-native-session'}})
        ledger.ask(run_id, question_id='question-1', text='Which offered candidate?')
        before = ledger.snapshot(run_id)

        def poll(process):
            if process.polls == 1:
                return None
            assert observed == ['warm attention without service stop']
            assert ledger.snapshot(run_id)['native'] == before['native']
            assert ledger.snapshot(run_id)['usage'] == before['usage']
            ledger.finish(run_id, 'no_output')
            return 0

        process.poll_hook = poll

    def answer_at_attention(seconds):
        state = ledger.snapshot(run_id)
        if state['status'] != 'awaiting_user':
            return
        assert workflow.brief_status(root)['reason'] == 'CLARIFICATION_REQUIRED'
        assert not stopped
        observed.append('warm attention without service stop')
        ledger.answer(run_id, question_id='question-1', text='The offered first candidate.', event_id='user-1')

    started, processes = _processes(monkeypatch, root, ledger, warm_question)
    monkeypatch.setattr(workflow.time, 'sleep', answer_at_attention)
    assert workflow.run(root) == 0
    assert started == [run_id]
    assert len([p for p in processes if p.role == 'run']) == 1
    assert ledger.snapshot(run_id)['usage']['known_total_tokens'] == 5
    assert ledger.snapshot(run_id)['native']['result']['session_id'] == 'warm-native-session'


def test_stale_service_marker_cannot_start_a_task_before_new_gateway_readiness(tmp_path, monkeypatch):
    root, ledger, order, _ = _batch(tmp_path, monkeypatch, groups=('B',))
    write_json(root/'service.json', {'state': 'running', 'pid': 4242, 'start_id': 'old-service'})
    started, _ = _processes(monkeypatch, root, ledger, _no_output,
                           ready=False, service_exit_after=2)
    assert workflow.run(root) == 2
    assert not started
    assert ledger.snapshot(order[0])['status'] == 'ready'
    assert not ledger.calls(order[0])


def test_gateway_launch_marker_accepts_windows_redirected_python_pid(tmp_path, monkeypatch):
    root, ledger, order, stopped = _batch(tmp_path, monkeypatch, groups=('B',))
    started, _ = _processes(monkeypatch, root, ledger, _no_output,
                           ready_pid=7777, service_exit_after=2)
    assert workflow.run(root) == 0
    assert started == order and stopped
    assert workflow.brief_status(root)['state'] == 'complete'


def _gate_fixture(root, monkeypatch, *, junit_body=None):
    folder = root/'admission'
    folder.mkdir(exist_ok=True)
    repository = root/'dummy-source'
    (repository/'tests').mkdir(parents=True)
    test_file = repository/'tests'/'focused.py'
    test_file.write_text('# offline receipt fixture, never executed\n', encoding='utf8')
    monkeypatch.setattr(workflow.carrier, 'REPO', repository)
    current = {'files': {'controller.py': 'fixture-source-binding'},
               'images': {workflow.carrier.IMAGE: 'sha256:tools', workflow.carrier.DSH_IMAGE: 'sha256:dsh'},
               'models': {arm: 'offline-model-'+arm for arm in 'ABCDEFG'}}
    monkeypatch.setattr(workflow.carrier, 'bindings', lambda configuration: deepcopy(current))
    log, junit = folder/'scoped.log', folder/'scoped.xml'
    log.write_text('Synthetic gate log for controller validation only.\n', encoding='utf8')
    junit.write_text(junit_body or '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0">'
                     '<testcase name="fixture_case"/></testsuite></testsuites>', encoding='utf8')

    def ref(path):
        return {'path': str(path.resolve()), 'sha256': sha256(path)}

    configuration = workflow.plan(root)['configuration']
    receipt = {'exit_code': 0, 'configuration': configuration, 'source_before': deepcopy(current),
               'source_after': deepcopy(current), 'tests': {'tests/focused.py': sha256(test_file)},
               'log': ref(log), 'junit': ref(junit)}
    write_json(folder/'scoped.json', receipt)
    source, artifact = folder/'source.ifc', folder/'artifact.ifc'
    source.write_bytes(b'not an experimental IFC: source hashing fixture only')
    artifact.write_bytes(b'not an experimental IFC: output hashing fixture only')
    native = {'all_passed': True, 'real_models_called': False, 'real_credentials_used': False,
              'runs': [{'arm': arm, 'status': 'submitted', 'source_unchanged': True,
                        'mode': 'real_runtime_fake_model', 'reopen': {'express_errors': 0},
                        'public_source': ref(source), 'artifact': ref(artifact)}
                       for arm in 'ABCDEFG'], 'native_timeout_stop': {'quiescent': True},
              'test_file': ref(test_file), 'service_log': ref(log), 'images': deepcopy(current['images']),
              'runtime_bindings_before': deepcopy(current), 'runtime_bindings_after': deepcopy(current)}
    native_path = folder/'native.json'
    write_json(native_path, native)
    return current, native_path


def test_gate_rejects_suite_failure_counts_with_missing_testcases(tmp_path, monkeypatch):
    root, _, _, _ = _batch(tmp_path, monkeypatch)
    _gate_fixture(root, monkeypatch, junit_body='<testsuites><testsuite tests="2" failures="1" errors="0" skipped="0">'
                  '<testcase name="only_retained_passing_case"/></testsuite></testsuites>')
    with pytest.raises(ValueError, match='SCOPED_GATE_INCOMPLETE'):
        workflow._gate_report(root/'admission'/'scoped.json')


def test_native_admission_cannot_omit_all_image_bindings(tmp_path, monkeypatch):
    root, _, _, _ = _batch(tmp_path, monkeypatch)
    _, native_path = _gate_fixture(root, monkeypatch)
    native = read_json(native_path)
    native['images'] = {}
    native['runtime_bindings_before']['images'] = {}
    native['runtime_bindings_after']['images'] = {}
    write_json(native_path, native)
    with pytest.raises(ValueError, match='NATIVE_IMAGE'):
        workflow.admit(root, native_path)
    assert not (root/'admission'/'live.json').exists()


def test_native_admission_cannot_omit_its_runtime_source_bindings(tmp_path, monkeypatch):
    root, _, _, _ = _batch(tmp_path, monkeypatch)
    _, native_path = _gate_fixture(root, monkeypatch)
    native = read_json(native_path)
    native['runtime_bindings_before']['files'] = {}
    native['runtime_bindings_after']['files'] = {}
    write_json(native_path, native)
    with pytest.raises(ValueError, match='NATIVE_RUNTIME'):
        workflow.admit(root, native_path)
    assert not (root/'admission'/'live.json').exists()


def test_native_receipt_drift_blocks_live_resume_before_any_process(tmp_path, monkeypatch):
    root, ledger, order, _ = _batch(tmp_path, monkeypatch, mode='live')
    _, native_path = _gate_fixture(root, monkeypatch)
    workflow.admit(root, native_path)
    native = read_json(native_path)
    native['all_passed'] = False
    write_json(native_path, native)
    started, processes = _processes(monkeypatch, root, ledger, _no_output)
    assert workflow.run(root) == 2
    assert not processes and not started
    assert all(ledger.snapshot(run)['status'] == 'ready' for run in order)
    assert any(code in workflow.brief_status(root)['reason'] for code in ('RECEIPT_CHANGED', 'EVIDENCE_CHANGED'))


def test_selected_group_admission_does_not_claim_untested_groups(tmp_path, monkeypatch):
    root, _, _, _ = _batch(tmp_path, monkeypatch, groups=('E',), mode='live')
    _, native_path = _gate_fixture(root, monkeypatch)
    native = read_json(native_path)
    native['runs'] = [row for row in native['runs'] if row['arm'] == 'E']
    write_json(native_path, native)
    workflow.admit(root, native_path)
    assert read_json(root/'admission/live.json')['authorized_arms'] == ['E']
    assert workflow._check_admission(root, workflow.plan(root)['configuration'])['passed']


def test_selected_group_admission_still_requires_every_requested_group(tmp_path, monkeypatch):
    root, _, _, _ = _batch(tmp_path, monkeypatch, groups=('B', 'E'), mode='live')
    _, native_path = _gate_fixture(root, monkeypatch)
    native = read_json(native_path)
    native['runs'] = [row for row in native['runs'] if row['arm'] == 'E']
    write_json(native_path, native)
    with pytest.raises(ValueError, match='NATIVE_GROUPS_REQUIRED'):
        workflow.admit(root, native_path)
    assert not (root/'admission/live.json').exists()
