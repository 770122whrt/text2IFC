"""Controlled development branches share the real, already charged question."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from scripts.ifc_repair.repair_comparison import demo_workflow
from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json
from scripts.ifc_repair.repair_comparison.ledger import Ledger

REPO = Path(__file__).resolve().parents[3]
COMMAND = [sys.executable, '-m', 'scripts.ifc_repair.repair_comparison.demo_workflow']


def trial_module():
    from scripts.ifc_repair.repair_comparison import clarification_trial
    return clarification_trial


def paused(tmp_path, monkeypatch):
    source = tmp_path / 'original'
    demo_workflow.initialize(source, mode='offline')
    ledger = Ledger(source / 'control.sqlite')
    run_id = 'case-002-B'
    ledger.start(run_id)
    ledger.reserve(run_id, 'shared-call', 100)
    ledger.settle(run_id, 'shared-call', usage={'prompt_tokens': 11, 'completion_tokens': 7}, response={})
    native = {'state_version': 3, 'clarification': {'clarification_id': 'question-1'}}
    ledger.set_native(run_id, {'result': native})
    ledger.ask(run_id, question_id='question-1', text='请确认尺寸',
               binding={'state_version': 3, 'native_question': native['clarification']})
    copies = []
    monkeypatch.setattr(trial_module(), '_clone_volume', lambda old, new: copies.append((old, new)))
    return source, ledger, run_id, copies


def test_fork_retains_seed_budget_and_question_but_separates_work_and_volume(tmp_path, monkeypatch):
    source, ledger, run_id, copies = paused(tmp_path, monkeypatch)
    before = ledger.events(run_id)
    original = ledger.snapshot(run_id)
    target = tmp_path / 'offset'
    report = trial_module().fork_pending_b(source, target, run_id, trial='public-offset')
    child = Ledger(target / 'control.sqlite')
    state = child.snapshot(run_id)
    assert state['status'] == 'awaiting_user' and state['question'] == original['question']
    assert state['budget'] == original['budget'] and state['usage']['known_total_tokens'] == 18
    assert state['usage']['calls'] == 1 and state['active_elapsed_s'] == original['active_elapsed_s']
    assert child.calls(run_id) == ledger.calls(run_id)
    assert state['native']['result'] == original['native']['result']
    assert Path(state['metadata']['workspace']) == target / 'workspaces' / run_id
    assert Path(state['metadata']['input_dir']) == target / 'inputs' / 'case-002'
    config = read_json(target / 'experiment.json')
    assert config['order'] == [run_id] and list(config['routes']) == [run_id]
    assert config['routes'][run_id]['volume'] != read_json(source / 'experiment.json')['routes'][run_id]['volume']
    assert len(copies) == 1 and copies[0][0] != copies[0][1]
    assert report['shared_request_ids'] == ['shared-call']
    assert report['shared_known_tokens'] == 18 and report['new_calls_at_fork'] == 0
    assert ledger.events(run_id) == before and ledger.snapshot(run_id)['status'] == 'awaiting_user'
    assert not (target / 'inputs' / 'case-001').exists()
    assert not list(target.rglob('reference.ifc')) and not list(target.rglob('private'))
    (target / 'workspaces' / run_id / 'output' / 'trial.txt').write_text('branch')
    assert not (source / 'workspaces' / run_id / 'output' / 'trial.txt').exists()


@pytest.mark.parametrize('problem', ['answered', 'activity', 'inflight', 'terminal', 'not-b'])
def test_nonquiescent_or_nonpending_runs_cannot_be_branched(tmp_path, monkeypatch, problem):
    source, ledger, run_id, copies = paused(tmp_path, monkeypatch)
    if problem == 'answered':
        ledger.answer(run_id, question_id='question-1', text='回答', event_id='answer')
    elif problem == 'terminal':
        ledger.finish(run_id, 'cancelled')
    elif problem == 'not-b':
        run_id = 'case-002-A'
    else:
        with ledger.transaction() as db:
            state = ledger._load(db, run_id)
            if problem == 'activity':
                state['activities'] = ['worker']
                ledger._save(db, state)
            else:
                db.execute("UPDATE calls SET state='inflight' WHERE run_id=?", (run_id,))
    destination = tmp_path / 'invalid'
    with pytest.raises(ValueError, match='PENDING|QUIESCENT|ARM'):
        trial_module().fork_pending_b(source, destination, run_id, trial='invalid')
    assert not destination.exists() and not copies


def test_existing_destination_is_not_overwritten(tmp_path, monkeypatch):
    source, _, run_id, copies = paused(tmp_path, monkeypatch)
    destination = tmp_path / 'existing'
    destination.mkdir()
    marker = destination / 'user.txt'
    marker.write_text('preserve')
    with pytest.raises(ValueError, match='EXISTS'):
        trial_module().fork_pending_b(source, destination, run_id, trial='offset')
    assert marker.read_text() == 'preserve' and not copies


@pytest.mark.skipif(os.environ.get('REPAIR_DEMO_DOCKER') != '1', reason='explicit native B fork/resume check')
def test_native_docker_branch_resumes_same_question_with_seed_usage(tmp_path):
    source, target = tmp_path / 'native-original', tmp_path / 'native-offset'
    run_id = 'case-002-B'
    console_handles, services = [], []

    def call(root, action, *extra):
        process = subprocess.run(COMMAND + [action, '--root', str(root), *extra], cwd=REPO,
                                 capture_output=True, text=True, encoding='utf8', timeout=600)
        assert process.returncode == 0, (process.stdout[-3000:], process.stderr[-3000:])
        return json.loads(process.stdout)

    def service(root):
        handle = (root / 'service-test.log').open('wb')
        console_handles.append(handle)
        process = subprocess.Popen(COMMAND + ['serve', '--root', str(root)], cwd=REPO,
                                   stdout=handle, stderr=subprocess.STDOUT)
        services.append((root, process))
        deadline = time.monotonic() + 90
        while not (root / 'service.json').exists():
            assert process.poll() is None, (root / 'service-test.log').read_text(encoding='utf8')
            assert time.monotonic() < deadline
            time.sleep(.25)

    try:
        config = call(source, 'init')
        config['fixture_scenarios'] = {run_id: 'question'}
        write_json(source / 'experiment.json', config)
        service(source)
        pending = call(source, 'run', '--run-id', run_id)
        assert pending['status'] == 'awaiting_user'
        source_events = Ledger(source / 'control.sqlite').events(run_id)
        report = trial_module().fork_pending_b(source, target, run_id, trial='offset-fixture')
        child_config = read_json(target / 'experiment.json')
        child_config['fixture_scenarios'] = {}  # Full deterministic answer after the common question.
        write_json(target / 'experiment.json', child_config)
        service(target)
        answer = tmp_path / 'answer.json'
        write_json(answer, {'text': '离线：单扇门，左开。'})
        call(target, 'answer', '--run-id', run_id, '--answer-file', str(answer))
        final = call(target, 'run', '--run-id', run_id)
        assert final['status'] == 'submitted', final
        assert final['budget'] == pending['budget'] and final['usage']['calls'] == 3
        assert final['usage']['known_total_tokens'] == 54
        assert final['native']['result']['run_id'] == pending['native']['result']['run_id']
        assert final['native']['result']['state_version'] > pending['native']['result']['state_version']
        assert Path(final['artifact']['path']).is_relative_to(target)
        assert Ledger(source / 'control.sqlite').events(run_id) == source_events
        assert Ledger(source / 'control.sqlite').snapshot(run_id)['status'] == 'awaiting_user'
        from scripts.ifc_repair.repair_comparison.isolated_b import IsolatedB, IsolatedBConfig
        route = config['routes'][run_id]
        reader = IsolatedB(IsolatedBConfig(source / 'runtime/b', source / 'workspaces' / run_id,
            route['volume'], config['network'], 'http://repair-gateway:8000/' + route['token'] + '/v1'))
        assert reader.read(run_id)['result'] == pending['native']['result']
        snapshot = reader.export_state(tmp_path / 'native-snapshot')
        restore_route = dict(route, volume=route['volume'] + '-restored')
        recovered = IsolatedB(IsolatedBConfig(source / 'runtime/b', source / 'workspaces' / run_id,
            restore_route['volume'], config['network'], 'http://repair-gateway:8000/' + route['token'] + '/v1'))
        assert recovered.restore_state(snapshot)['model_calls'] == 0
        assert recovered.read(run_id)['result'] == pending['native']['result']
        with pytest.raises(ValueError, match='VOLUME_ALREADY_EXISTS'):
            recovered.restore_state(snapshot)
        original_count = Ledger(source / 'control.sqlite').snapshot(run_id)['usage']['calls']
        call(source, 'answer', '--run-id', run_id, '--answer-file', str(answer))
        restored_final = recovered.answer(run_id, answer={'kind': 'add_detail', 'detail': '离线：左开。'},
            clarification_id=pending['native']['result']['clarification']['clarification_id'],
            expected_state_version=pending['native']['result']['state_version'])
        assert restored_final['artifact_relative'] == 'output/native-result.ifc', restored_final
        assert restored_final['result']['run_id'] == pending['native']['result']['run_id']
        assert Ledger(source / 'control.sqlite').snapshot(run_id)['usage']['calls'] == original_count + 2
        from scripts.ifc_repair.repair_comparison.direct_runner import DirectRunner
        assert DirectRunner(source, run_id).submit('output/native-result.ifc')['status'] == 'submitted'
        assert call(target, 'check')[0]['evaluation']['checks']['native_schema_express']
        assert report['shared_request_ids'] == [Ledger(target / 'control.sqlite').calls(run_id)[0]['request_id']]
    finally:
        for root, process in reversed(services):
            if (root / 'service.json').exists():
                call(root, 'stop')
            process.wait(timeout=45)
        for handle in console_handles:
            handle.close()
