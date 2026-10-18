"""Bounded controller scheduling, not model repair/capability evidence."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import csv
import json
import sqlite3
from threading import Event
from types import SimpleNamespace

import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json
from scripts.ifc_repair.repair_comparison.ledger import Ledger, encode
from scripts.ifc_repair.repair_comparison.controller_owner import task_owner
from tests.ifc_repair.repair_comparison.test_scalable_controller_safety import _batch, _charge


def _parallel_batch(tmp_path, monkeypatch, capacity=2, groups=('B', 'E', 'F', 'G')):
    root, ledger, order, stopped = _batch(tmp_path, monkeypatch, groups=groups)
    value = read_json(root/'batch.json')
    value.update(schema_version='repair-comparison-small-rounds/0.2',
                 scheduler={'max_running': capacity}, selection='full')
    value.pop('sha256')
    value['sha256'] = batch._digest(value)
    write_json(root/'batch.json', value)
    with ledger.transaction() as db:
        for run in order:
            state = ledger._load(db, run)
            state['metadata']['runtime'] = {'stage': batch.SCALABLE_STAGE}
            ledger._save(db, state)
    return root, ledger, order, stopped


def _jobs(monkeypatch, root, ledger, order, *, fail_first=False, pause_first=False, clarify_first_two=False):
    started, processes, peaks = [], [], []
    class Process:
        def __init__(self, command):
            self.role, self.polls = command[3], 0
            self.process = SimpleNamespace(pid=4242, returncode=None)
            self.tail = b'offline process detail must stay hidden'
            processes.append(self)
            if self.role == 'serve':
                marker = command[command.index('--service-start-id')+1]
                write_json(root/'service.json', {'state':'running','start_id':marker,'pid':7777})
            else:
                self.run = command[command.index('--run-id')+1]
                started.append(self.run)
                if not ledger.calls(self.run):
                    _charge(ledger, self.run)
                peaks.append(sum(s['status']=='running' for s in batch._states(root)))
                self.qwen_peak = sum(s['status']=='running' and s['arm'] in 'FG'
                                     for s in batch._states(root))
        def poll(self):
            if self.role == 'serve':
                return None
            self.polls += 1
            if self.process.returncode is not None:
                return self.process.returncode
            first = self.run == order[0]
            if self.polls < (1 if first and fail_first else 3):
                return None
            if (clarify_first_two and self.run in order[:2]
                    and not any(event['kind']=='answer' for event in ledger.events(self.run))):
                ledger.set_native(self.run, {'result': {'session_id': 'kept-'+self.run}})
                ledger.ask(self.run, question_id='width', text='Confirm the public width?')
                self.process.returncode = 0
                return 0
            if first and fail_first:
                ledger.reserve(self.run, 'bad-wire', 10)
                ledger.settle(self.run, 'bad-wire', usage=None,
                              response={'http_status':401,'error_type':'authentication_error'}, failed=True)
                ledger.finish(self.run,'runtime_error',detail='PROVIDER_HTTP_401')
            else:
                ledger.finish(self.run,'no_output',detail='Synthetic no-submit result.')
            if first and pause_first:
                batch.pause(root)
            self.process.returncode = 0
            return 0
        def wait(self, timeout=None):
            self.process.returncode = self.process.returncode or 0
            return self.process.returncode
    monkeypatch.setattr(batch,'_Process',Process)
    return started, processes, peaks


def test_slots_overlap_but_never_exceed_frozen_capacity(tmp_path, monkeypatch, capsys):
    root, ledger, order, stopped = _parallel_batch(tmp_path,monkeypatch)
    started, _, peaks = _jobs(monkeypatch,root,ledger,order)
    assert batch.run(root) == 0
    assert started == order and max(peaks) == 2
    assert all(ledger.snapshot(run)['status']=='no_output' for run in order)
    assert stopped
    lines = capsys.readouterr().out.splitlines()
    assert len(lines)==1 and json.loads(lines[0])['completed']==4
    assert 'Synthetic no-submit' not in lines[0]
    assert len(list((root/'results').rglob('report.md')))==4


def test_interface_fault_stops_dispatch_and_drains_other_active_job(tmp_path, monkeypatch, capsys):
    root, ledger, order, stopped = _parallel_batch(tmp_path,monkeypatch)
    started, _, _ = _jobs(monkeypatch,root,ledger,order,fail_first=True)
    assert batch.run(root)==2
    assert started==order[:2]
    assert ledger.snapshot(order[0])['status']=='runtime_error'
    assert ledger.snapshot(order[1])['status']=='no_output'
    assert not ledger.calls(order[2]) and not ledger.calls(order[3])
    assert stopped
    lines=capsys.readouterr().out.splitlines()
    assert len(lines)==1
    assert json.loads(lines[0])['reason']=='PROVIDER_INTERFACE_FAILURE'


def test_pause_drains_slots_and_resume_keeps_terminal_outputs_and_costs(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path,monkeypatch)
    started, _, _ = _jobs(monkeypatch,root,ledger,order,pause_first=True)
    assert batch.run(root)==0
    assert started==order[:2]
    charges={run:ledger.snapshot(run)['usage'] for run in order[:2]}
    with closing(sqlite3.connect(root/'control.sqlite')) as db:
        assert db.execute('SELECT COUNT(*) FROM batch_exports').fetchone()[0]==2
    started, _, peaks=_jobs(monkeypatch,root,ledger,order)
    assert batch.resume(root)==0
    assert started==order[2:] and max(peaks)==2
    assert {run:ledger.snapshot(run)['usage'] for run in order[:2]}==charges
    assert len(list((root/'results').rglob('report.md')))==4


def test_group_hold_runs_other_arms_and_preserves_pending_tasks_on_resume(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch)
    original_plan = (root/'batch.json').read_bytes()
    batch.set_group_hold(root, ['F', 'G'], hold=True, reason='Operator deferred Qwen.')
    started, _, _ = _jobs(monkeypatch, root, ledger, order)
    assert batch.run(root) == 0
    assert started == order[:2]
    summary = batch.brief_status(root)
    assert summary['state'] == 'paused'
    assert summary['reason'] == 'HELD_GROUPS_REMAINING'
    assert summary['held_groups'] == ['F', 'G']
    assert summary['held_pending'] == 2
    assert all(ledger.snapshot(run)['status'] == 'ready' for run in order[2:])
    charges = {run: ledger.snapshot(run)['usage'] for run in order[:2]}
    batch.set_group_hold(root, ['F', 'G'], hold=False, reason='Operator restored Qwen.')
    started, _, _ = _jobs(monkeypatch, root, ledger, order)
    assert batch.resume(root) == 0
    assert started == order[2:]
    assert charges == {run: ledger.snapshot(run)['usage'] for run in order[:2]}
    assert (root/'batch.json').read_bytes() == original_plan


def test_group_hold_refuses_active_or_unknown_arms_without_resetting_state(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch)
    _charge(ledger, order[2])
    before = ledger.snapshot(order[2])
    with pytest.raises(ValueError, match='GROUP_HOLD_REQUIRES_QUIESCENT_TASKS'):
        batch.set_group_hold(root, ['F'], hold=True, reason='Cannot hide an active task.')
    after = ledger.snapshot(order[2])
    assert {k: after[k] for k in ('status', 'budget', 'usage', 'metadata')} == {
        k: before[k] for k in ('status', 'budget', 'usage', 'metadata')}
    assert after['active_elapsed_s'] >= before['active_elapsed_s']
    with pytest.raises(ValueError, match='INVALID_EXPERIMENT_ARMS'):
        batch.set_group_hold(root, ['Z'], hold=True, reason='Invalid arm.')


def test_group_hold_preserves_interface_failure_barrier(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, groups=tuple('ABCDEFG'))
    batch.set_group_hold(root, ['F', 'G'], hold=True, reason='Operator deferred Qwen.')
    started, _, _ = _jobs(monkeypatch, root, ledger, order, fail_first=True)
    assert batch.run(root) == 2
    assert started == order[:2]
    assert batch.brief_status(root)['reason'] == 'PROVIDER_INTERFACE_FAILURE'
    assert all(ledger.snapshot(run)['status'] == 'ready' for run in order[2:])


def test_group_hold_cli_is_persistent_and_summary_only(tmp_path, monkeypatch, capsys):
    root, _, _, _ = _parallel_batch(tmp_path, monkeypatch)
    assert batch.main(['hold-groups', '--root', str(root), '--groups', 'F', 'G',
                       '--reason', 'Operator deferred Qwen.']) == 0
    assert json.loads(capsys.readouterr().out)['held_groups'] == ['F', 'G']
    assert batch.main(['status', '--root', str(root), '--brief']) == 0
    assert json.loads(capsys.readouterr().out)['held_groups'] == ['F', 'G']
    assert batch.main(['release-groups', '--root', str(root), '--groups', 'F', 'G',
                       '--reason', 'Operator restored Qwen.']) == 0
    assert json.loads(capsys.readouterr().out)['held_groups'] == []


def test_plain_directory_prepare_expands_all_pairs_to_seven_groups(tmp_path,monkeypatch):
    inputs=tmp_path/'inputs';inputs.mkdir()
    for case in ('one','two','three'):
        (inputs/(case+'.ifc')).write_bytes(b'opaque synthetic IFC bytes')
        (inputs/(case+'.txt')).write_text('Restore the specified public object.',encoding='utf8')
    with (inputs/'inputs.csv').open('w',newline='',encoding='utf8') as stream:
        writer=csv.writer(stream)
        writer.writerow(['case_id','ifc_path','request_path','level','task_kind'])
        for case in ('one','two','three'):
            writer.writerow([case,case+'.ifc',case+'.txt','S1','geometry'])
    monkeypatch.setattr(batch,'check_ifc',lambda path:{'passed':True,'status':'passed','evidence':'synthetic unit validator'})
    prepared=batch.prepare(tmp_path/'out',inputs,scope='full',input_format='pairs',concurrency=2,mode='offline')
    assert prepared['tasks']==21
    value=batch.plan(tmp_path/'out')
    assert value['scheduler']=={'max_running':2}
    assert value['selection']=='full'
    assert set(value['configuration']['case_groups'])=={'one','two','three'}
    assert all(set(groups)==set('ABCDEFG') for groups in value['configuration']['case_groups'].values())
    assert all(p['passed'] for p in value['input_format_checks'].values())
    assert all({p.name for p in folder.iterdir()}=={'model.ifc','request.txt'}
               for folder in (tmp_path/'out/cases').glob('*/public'))


def test_service_transition_waits_for_short_owner_without_weakening_task_lock(tmp_path):
    acquired, attempted = Event(), Event()

    def transition():
        attempted.set()
        with task_owner(tmp_path, 'service-transition', wait_seconds=2):
            acquired.set()

    with ThreadPoolExecutor(max_workers=1) as executor:
        with task_owner(tmp_path, 'service-transition'):
            with pytest.raises(ValueError, match='RUN_CONTROLLER_ALREADY_ACTIVE'):
                with task_owner(tmp_path, 'service-transition'):
                    pytest.fail('Duplicate nonblocking owner was admitted.')
            future = executor.submit(transition)
            assert attempted.wait(1)
            assert not acquired.wait(.05)
        future.result(timeout=3)
    assert acquired.is_set()


def test_bad_answer_stops_dispatch_but_drains_owned_jobs(tmp_path, monkeypatch, capsys):
    root, ledger, order, stopped = _parallel_batch(tmp_path, monkeypatch)
    started, _, _ = _jobs(monkeypatch, root, ledger, order)
    rejected = []

    def invalid_answer(path):
        if started and not rejected:
            rejected.append(True)
            raise ValueError('PENDING_QUESTION_CHANGED')

    monkeypatch.setattr(batch, '_queued_answer', invalid_answer)
    assert batch.run(root) == 2
    assert started == order[:2]
    assert all(ledger.snapshot(run)['status'] == 'no_output' for run in order[:2])
    assert all(ledger.snapshot(run)['status'] == 'ready' for run in order[2:])
    assert stopped
    assert 'PENDING_QUESTION_CHANGED' in json.loads(capsys.readouterr().out)['reason']


def test_resume_cannot_silently_change_frozen_concurrency(tmp_path, monkeypatch, capsys):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch)
    started, _, _ = _jobs(monkeypatch, root, ledger, order)
    assert batch.main(['resume', '--root', str(root), '--concurrency', '3']) == 2
    assert not started and all(ledger.snapshot(run)['status'] == 'ready' for run in order)
    assert 'CONCURRENCY_POLICY_FROZEN' in json.loads(capsys.readouterr().out)['reason']


def test_two_pending_answers_resume_only_existing_tasks_before_new_dispatch(tmp_path, monkeypatch, capsys):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch)
    monkeypatch.setattr(batch.carrier, 'answer', lambda root, run, answer:
        ledger.answer(run, question_id=answer['question_id'], text=answer['text'], event_id=answer['event_id']))
    started, _, _ = _jobs(monkeypatch, root, ledger, order, clarify_first_two=True)
    assert batch.run(root) == 2 and started == order[:2]
    summary = json.loads(capsys.readouterr().out)
    assert summary['pending_count'] == summary['active_count'] == 2
    before = {run: ledger.snapshot(run) for run in order[:2]}
    for index in (0, 1):
        answer = tmp_path/f'answer-{index}.json'
        write_json(answer, {'source': 'user_confirmed', 'text': 'The public width is confirmed.'})
        resumed, _, _ = _jobs(monkeypatch, root, ledger, order, clarify_first_two=True)
        assert batch.resume(root, run_id=order[index], answer_file=answer) == (2 if index==0 else 0)
        assert resumed == ([order[0]] if index==0 else order[1:])
        state = ledger.snapshot(order[index])
        assert state['status'] == 'no_output'
        assert state['usage'] == before[order[index]]['usage']
        assert state['native'] == before[order[index]]['native']
        assert state['budget'] == before[order[index]]['budget']


def test_invalid_public_ifc_fails_before_service_or_model_start(tmp_path, monkeypatch, capsys):
    inputs = tmp_path/'inputs'; inputs.mkdir()
    (inputs/'broken.ifc').write_bytes(b'not an IFC')
    (inputs/'broken.txt').write_text('Restore the missing window.', encoding='utf8')
    monkeypatch.setattr(batch, 'check_ifc', lambda path: {'passed': False, 'status': 'error'})
    with pytest.raises(ValueError, match='INPUT_IFC_FORMAT_FAILED'):
        batch.prepare(tmp_path/'out', inputs, scope='full', default_level='S1', mode='offline')
    assert batch.main(['run', '--root', str(tmp_path/'out')]) == 2
    assert 'INPUT_IFC_FORMAT_FAILED' in json.loads(capsys.readouterr().out)['reason']
    assert not (tmp_path/'out/experiment.json').exists()


def _qwen_priority(root):
    value = read_json(root/'batch.json')
    value.update(schema_version='repair-comparison-small-rounds/0.3',
                 scheduler={'max_running': 7, 'priority': 'qwen-first', 'qwen_max_running': 2})
    value.pop('sha256')
    value['sha256'] = batch._digest(value)
    write_json(root/'batch.json', value)
    return value


def test_seven_slots_prioritize_qwen_without_flooding_its_shared_endpoint(tmp_path, monkeypatch, capsys):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, capacity=7,
                                           groups=tuple('ABCDEFGFGABCDE'))
    _qwen_priority(root)
    started, processes, peaks = _jobs(monkeypatch, root, ledger, order)
    assert batch.main(['run', '--root', str(root)]) == 0
    assert started[:2] == [order[5], order[6]]
    assert started[:7] == [order[5], order[6], *order[:5]]
    assert set(started) == set(order) and len(started) == len(order)
    assert max(peaks) == 7
    assert max(p.qwen_peak for p in processes if p.role != 'serve') == 2
    assert all(len(ledger.calls(run)) == 1 for run in order)
    assert len(capsys.readouterr().out.splitlines()) == 1


def test_qwen_priority_pause_resume_preserves_outputs_usage_and_original_csv_order(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, capacity=7,
                                           groups=tuple('ABCDEFGFGABCDE'))
    original = _qwen_priority(root)
    started, _, _ = _jobs(monkeypatch, root, ledger, order, pause_first=True)
    assert batch.run(root) == 0 and len(started) == 7
    costs = {run: ledger.snapshot(run)['usage'] for run in started}
    pending = set(order)-set(started)
    resumed, processes, peaks = _jobs(monkeypatch, root, ledger, order)
    assert batch.resume(root) == 0
    assert set(resumed) == pending and max(peaks) == 7
    assert max(p.qwen_peak for p in processes if p.role != 'serve') <= 2
    assert {run: ledger.snapshot(run)['usage'] for run in costs} == costs
    assert batch.plan(root)['configuration']['order'] == original['configuration']['order']
    assert all(len(ledger.calls(run)) == 1 for run in order)


def test_unstarted_scheduler_refreeze_preserves_inputs_harness_and_budgets(tmp_path, monkeypatch):
    inputs = tmp_path/'inputs'; inputs.mkdir()
    (inputs/'one.ifc').write_bytes(b'opaque synthetic IFC')
    (inputs/'one.txt').write_text('Restore the specified window.', encoding='utf8')
    monkeypatch.setattr(batch, 'check_ifc', lambda _: {'passed': True, 'status': 'passed'})
    root = tmp_path/'prepared'
    batch.prepare(root, inputs, scope='full', input_format='pairs', default_level='S1',
                  mode='offline', concurrency=2)
    old = batch.plan(root)
    original = (root/'batch.json').read_bytes()
    result = batch.refresh_unstarted(root, concurrency=7, qwen_first=True)
    new = batch.plan(root)
    assert result['state'] == 'refrozen_requires_admission'
    assert new['scheduler'] == {'max_running': 7, 'priority': 'qwen-first', 'qwen_max_running': 2}
    assert new['schema_version'] == 'repair-comparison-small-rounds/0.3'
    assert new['configuration'] == old['configuration']
    assert new['input_bindings'] == old['input_bindings']
    assert (root/'admission'/('prepared-'+old['sha256']+'.json')).read_bytes() == original
    assert batch.refresh_unstarted(root, concurrency=7, qwen_first=True)['state'] == 'unchanged'
    (root/'control.sqlite').touch()
    with pytest.raises(ValueError, match='STARTED_BATCH_IMMUTABLE'):
        batch.refresh_unstarted(root, concurrency=2, qwen_first=False)


def test_qwen_priority_prepare_and_resume_policy_are_explicit(tmp_path, monkeypatch, capsys):
    inputs = tmp_path/'inputs'; inputs.mkdir()
    (inputs/'one.ifc').write_bytes(b'opaque synthetic IFC')
    (inputs/'one.txt').write_text('Restore the specified window.', encoding='utf8')
    monkeypatch.setattr(batch, 'check_ifc', lambda _: {'passed': True, 'status': 'passed'})
    root = tmp_path/'prepared'
    assert batch.main(['prepare', '--root', str(root), '--dataset', str(inputs),
                      '--input-format', 'pairs', '--default-level', 'S1', '--mode', 'offline',
                      '--concurrency', '7', '--qwen-first']) == 0
    assert batch.plan(root)['scheduler']['priority'] == 'qwen-first'
    capsys.readouterr()
    assert batch.main(['resume', '--root', str(root), '--no-qwen-first']) == 2
    assert 'SCHEDULER_POLICY_FROZEN' in capsys.readouterr().out


def test_priority_restores_existing_session_before_starting_new_qwen_tasks(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, capacity=7,
                                           groups=tuple('ABCDEFG'))
    _qwen_priority(root)
    ledger.configure_concurrency(7)
    _charge(ledger, order[0])
    before = ledger.snapshot(order[0])
    started, _, _ = _jobs(monkeypatch, root, ledger, order)
    assert batch.run(root) == 0
    assert started[:3] == [order[0], order[5], order[6]]
    assert ledger.snapshot(order[0])['usage'] == before['usage']
    assert ledger.snapshot(order[0])['metadata'] == before['metadata']


@pytest.mark.parametrize('replacement', [{'qwen_max_running': True}, {'qwen_max_running': 7},
                                        {'priority': 'arbitrary'}, {'max_running': 8}])
def test_priority_policy_rejects_unsupported_limits_even_with_a_new_digest(tmp_path, monkeypatch, replacement):
    root, _, _, _ = _parallel_batch(tmp_path, monkeypatch)
    value = _qwen_priority(root)
    value['scheduler'].update(replacement)
    value.pop('sha256')
    value['sha256'] = batch._digest(value)
    write_json(root/'batch.json', value)
    with pytest.raises(ValueError, match='INVALID_(QWEN_PRIORITY_POLICY|CONCURRENCY_CAPACITY)'):
        batch.plan(root)


def test_speed_summary_uses_ledger_times_without_reading_task_exports(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, capacity=7)
    assert batch.brief_status(root)['eta_days_at_capacity'] is None
    ledger.configure_concurrency(7)
    for run in order[:2]:
        ledger.start(run)
        ledger.finish(run, 'no_output', detail='Synthetic timing fixture.')
        with ledger.transaction() as db:
            state = ledger._load(db, run)
            state.update(started=100, ended=400)
            ledger._save(db, state)
    def forbidden(*args, **kwargs):
        pytest.fail('Timing calibration must not read reports, IFC, or response files.')
    monkeypatch.setattr(batch, 'read_json', forbidden)
    status = batch.brief_status(root)
    assert status['timing_by_group'] == {
        'B': {'timed': 1, 'mean_wall_s': 300.0}, 'E': {'timed': 1, 'mean_wall_s': 300.0}}
    assert status['eta_days_at_capacity'] == pytest.approx(2*300/7/86400, abs=0.00005)
