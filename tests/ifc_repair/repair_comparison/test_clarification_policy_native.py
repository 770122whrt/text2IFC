"""All seven real Linux executors fail unanswered questions over keyless fake HTTP."""
import csv
import json
import os
import shutil
import subprocess
import sys

import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.contracts import read_json, sha256, write_json
from scripts.ifc_repair.repair_comparison.formal_admission import capture_sources
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from tests.ifc_repair.repair_comparison.test_scalable_native import _offline_environment, _stopped


@pytest.mark.skipif(os.environ.get('REPAIR_SCALABLE_DOCKER') != '1',
                    reason='explicit keyless clarification-policy native Docker check')
def test_seven_native_groups_fail_questions_and_resume_without_new_calls(tmp_path):
    inputs = tmp_path/'public-inputs'
    inputs.mkdir()
    for source, destination in [('model.ifc', 'case-001.ifc'), ('request.txt', 'case-001.txt')]:
        shutil.copyfile(carrier.CASES/'case-001'/'public'/source, inputs/destination)
    with (inputs/'inputs.csv').open('w', encoding='utf8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['case_id', 'ifc_path', 'request_path', 'level', 'task_kind'])
        writer.writerow(['case-001', 'case-001.ifc', 'case-001.txt', 'S1', 'geometry'])
    before = {p.name: sha256(p) for p in inputs.iterdir()}
    root = tmp_path/'batch'
    batch.prepare(root, inputs, mode='offline', scope='full', input_format='pairs',
                  groups=list('ABCDEFG'), concurrency=2, retain_debug=True)
    value = batch.plan(root)
    config = batch._initialize(root, value)
    config['fixture_scenarios'] = {run: 'question' for run in config['order']}
    write_json(root/'experiment.json', config)
    cli = [sys.executable, '-m', 'scripts.ifc_repair.repair_comparison.batch_operator']
    environment = _offline_environment()
    process = subprocess.Popen(cli+['run', '--root', str(root), '--clarification-policy', 'fail'],
        cwd=carrier.REPO, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=900)
    except subprocess.TimeoutExpired:
        batch.pause(root)
        pytest.fail('Native clarification check timed out; cooperative pause requested, owner retained at '+str(root))
    (tmp_path/'summary.json').write_bytes(stdout)
    (tmp_path/'stderr.txt').write_bytes(stderr)
    assert process.returncode == 0, 'Inspect retained bounded summary.'
    summaries = stdout.decode('utf8').splitlines()
    assert len(summaries) == 1
    assert json.loads(summaries[0])['status_counts'] == {'no_output': 7}
    ledger = Ledger(root/'control.sqlite')
    rows = []
    for run in config['order']:
        state = ledger.snapshot(run)
        assert state['status'] == 'no_output' and state['artifact'] is None and state['question']
        assert not state['activities']
        calls = ledger.calls(run)
        assert calls and not any(c['state'] == 'inflight' for c in calls)
        events = ledger.events(run)
        assert not any(e['kind'] == 'answer' for e in events)
        assert events[-1]['kind'] == 'terminal'
        assert events[-1]['payload']['detail'] == batch.CLARIFICATION_FAILURE
        _stopped(config['routes'][run]['container'])
        assert state['usage']['known_total_tokens'] > 0 and state['usage']['unknown_calls'] == 0
        case, arm = run.rsplit('-', 1)
        report = (root/'results'/case/arm/'report.md').read_text(encoding='utf8')
        assert state['question']['question_id'] in report and batch.CLARIFICATION_FAILURE in report
        assert not (root/'results'/case/arm/'repaired.ifc').exists()
        if arm == 'D':
            stopped = read_json(root/'runtime'/run/'container.json')['State']
            assert not stopped['Running'] and stopped['Pid'] == 0
            assert (root/'runtime'/run/'sessions').is_dir()
        rows.append({'run_id': run, 'status': state['status'], 'usage': state['usage'],
                     'question_id': state['question']['question_id'], 'container_stopped': True})
    resumed = subprocess.run(cli+['resume', '--root', str(root)], cwd=carrier.REPO,
        env=environment, capture_output=True, timeout=120)
    assert resumed.returncode == 0
    for row in rows:
        assert ledger.snapshot(row['run_id'])['usage'] == row['usage']
    assert {p.name: sha256(p) for p in inputs.iterdir()} == before
    write_json(tmp_path/'clarification-policy-native.json', {
        'all_passed': True, 'real_models_called': False, 'gateway_mode': 'offline',
        'source_bindings': capture_sources('execution'), 'batch_sha256': value['sha256'], 'rows': rows})
