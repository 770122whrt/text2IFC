"""Explicit existing-Linux-runtime acceptance; keyless fake HTTP only."""
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts.ifc_repair import qwen_batch as qwen
from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.contracts import read_json, sha256, write_json
from scripts.ifc_repair.repair_comparison.formal_admission import file_ref
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from tests.ifc_repair.repair_comparison import test_scalable_native as native

NATIVE = os.environ.get('REPAIR_QWEN_DOCKER') == '1'
CLI = [sys.executable, '-m', 'scripts.ifc_repair.qwen_batch']


def acceptance_policy():
    path = os.environ.get('REPAIR_QWEN_POLICY_FILE')
    return qwen.load_policy_file(path) if path else qwen.default_policy()


def unchanged_stop_sources(current, old):
    # Context serialization/profile changes do not change Linux process stops.
    context_files = {'scripts/ifc_repair/qwen_batch.py',
        'scripts/ifc_repair/repair_comparison/group_config.py', 'qwen-policy.json'}
    assert all(current['files'].get(k) == h for k,h in old['files'].items() if k not in context_files)


@pytest.mark.skipif(not NATIVE, reason='explicit Qwen existing Docker fake-provider gate')
def test_fg_actual_runtime_preserves_clarification_and_profile(tmp_path, request, monkeypatch):
    policy = acceptance_policy()
    root = tmp_path/'runtime'
    for module, name in ((carrier, 'bindings'), (carrier, 'WireGateway'), (batch, 'CLI'), (batch, '_interface_fault')):
        monkeypatch.setattr(module, name, getattr(module, name))
    monkeypatch.setattr(carrier, '_qwen_entry_installed', False, raising=False)
    qwen.install(root, policy)
    original = carrier.initialize
    def initialize(*args, **kwargs):
        kwargs['providers'] = qwen.limited_providers(kwargs['providers'], policy)
        config = original(*args, **kwargs)
        write_json(root/'qwen-policy.json', qwen.policy_document(policy))
        return config
    monkeypatch.setattr(carrier, 'initialize', initialize)
    providers = qwen.limited_providers(qwen.default_providers(), policy)
    monkeypatch.setattr(native, 'default_providers', lambda: providers)
    monkeypatch.setattr(native, 'CLI', CLI+['worker'])
    # Linux tool timeout/stop code is unmodified. Reuse its sufficient previous
    # receipt, verifying evidence and runtime source hashes instead of rerunning.
    previous_path = Path(os.environ['REPAIR_QWEN_PRIOR_NATIVE'])
    previous = read_json(previous_path)
    prior_stop = previous['timeout_stop']
    assert prior_stop['container_stopped'] and prior_stop['quiescent'] and prior_stop['timed_out']
    assert sha256(Path(prior_stop['evidence']['path'])) == prior_stop['evidence']['sha256']
    def reuse_timeout(_):
        current = batch._runtime_bindings(carrier.bindings(read_json(root/'experiment.json')['configuration']))
        old = batch._runtime_bindings(previous['runtime_bindings_after'])
        unchanged_stop_sources(current, old)
        return {**prior_stop, 'reused_from': file_ref(previous_path)}
    monkeypatch.setattr(native, '_native_timeout_check', reuse_timeout)
    native._native_grid(tmp_path, request, case_groups={'case-001': ['F', 'G'], 'case-002': ['F']})
    receipt = read_json(tmp_path/'native-stage.json')
    receipt['test_file'] = file_ref(Path(__file__))
    receipt['helper_file'] = file_ref(Path(native.__file__))
    write_json(tmp_path/'native-stage.json', receipt)
    ledger = Ledger(root/'control.sqlite')
    assert all(any(e['kind'] == 'qwen_context_projection' for e in ledger.events(run)) for run in receipt['configuration']['order'])
    batch._verify_native(tmp_path/'native-stage.json', receipt['configuration'], groups=['F', 'G'])


@pytest.mark.skipif(not NATIVE, reason='explicit Qwen existing Docker public batch CLI gate')
def test_fg_batch_summary_pause_resume_and_minimal_outputs(tmp_path):
    inputs = tmp_path/'inputs'
    inputs.mkdir()
    for source, suffix in (('model.ifc', '.ifc'), ('request.txt', '.txt')):
        shutil.copyfile(carrier.CASES/'case-002'/'public'/source, inputs/('case-002'+suffix))
    with (inputs/'inputs.csv').open('w', encoding='utf8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['case_id', 'ifc_path', 'request_path', 'level', 'primary_target_count', 'task_kind'])
        writer.writerow(['case-002', 'case-002.ifc', 'case-002.txt', 'S1', '1', 'geometry'])
    root = tmp_path/'batch'
    environment = native._offline_environment()
    def call(action, *args, timeout=240):
        process = subprocess.run(CLI+[action, '--root', str(root), *map(str, args)], cwd=carrier.REPO,
            env=environment, capture_output=True, text=True, encoding='utf8', timeout=timeout)
        if process.returncode:
            (tmp_path/('failure-'+action+'.txt')).write_text((process.stdout+process.stderr)[-8192:], encoding='utf8')
        assert process.returncode == 0, action+' failed; bounded failure retained at '+str(tmp_path)
        assert not process.stderr and len(process.stdout.splitlines()) == 1
        return json.loads(process.stdout)
    hashes = {p.name: sha256(p) for p in inputs.iterdir()}
    policy_args = ['--policy', os.environ['REPAIR_QWEN_POLICY_FILE']] if os.environ.get('REPAIR_QWEN_POLICY_FILE') else []
    assert call('prepare', '--dataset', inputs, '--mode', 'offline', '--input-format', 'pairs', *policy_args)['tasks'] == 2
    assert {run.rsplit('-', 1)[1] for run in batch.plan(root)['configuration']['order']} == {'F', 'G'}
    call('pause')
    assert call('run')['state'] == 'paused'
    summary = call('resume', '--from-case', '1')
    assert summary['state'] == 'complete' and summary['status_counts'] == {'submitted': 2}
    ledger = Ledger(root/'control.sqlite')
    counts = {run: len(ledger.calls(run)) for run in batch.plan(root)['configuration']['order']}
    assert call('resume')['state'] == 'complete'
    assert {run: len(ledger.calls(run)) for run in counts} == counts
    assert call('status', '--brief')['completed'] == 2
    for arm in 'FG':
        out = root/'results'/'case-002'/arm
        assert {p.name for p in out.iterdir()} == {'report.md', 'repaired.ifc'}
        assert (out/'report.md').stat().st_size <= 65536
    assert {p.name: sha256(p) for p in inputs.iterdir()} == hashes
    assert read_json(root/'service.json')['state'] == 'stopped'
    write_json(tmp_path/'batch-summary.json', {'summary': summary, 'source_unchanged': True,
        'resume_skips_terminals': True, 'minimal_outputs': True, 'fake_provider_only': True})
