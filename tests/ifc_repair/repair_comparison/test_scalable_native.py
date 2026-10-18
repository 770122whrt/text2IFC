"""Seven real Linux executors over keyless fake HTTP; never live model evidence."""
from __future__ import annotations

from contextlib import closing
import csv
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

import pytest

from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.budget import fixed_budget_profile
from scripts.ifc_repair.repair_comparison.container_tools import ContainerTools, IMAGE
from scripts.ifc_repair.repair_comparison.contracts import read_json, sha256, write_json
from scripts.ifc_repair.repair_comparison.formal_admission import file_ref
from scripts.ifc_repair.repair_comparison.group_config import (
    GROUPS, SCALABLE_STAGE, default_providers, executor, harness_profile,
)
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from scripts.ifc_repair.repair_comparison.isolated_b import PROPERTY_RUNTIME_IMAGE, PROPERTY_RUNTIME_VERSION


REPO = Path(__file__).resolve().parents[3]
CLI = [sys.executable, '-m', 'scripts.ifc_repair.repair_comparison.demo_workflow']
NATIVE = os.environ.get('REPAIR_SCALABLE_DOCKER') == '1'
REOPEN_SCRIPT = '''
import hashlib, json, platform, sys
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.validate
source = Path('result.ifc')
model = ifcopenshell.open(str(source))
logger = ifcopenshell.validate.json_logger()
ifcopenshell.validate.validate(model, logger, express_rules=False)
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)
geometries, geometry_errors = 0, 0
for entity in model.by_type(sys.argv[1]):
    if entity.Representation is None:
        continue
    try:
        shape = ifcopenshell.geom.create_shape(settings, entity)
        if len(shape.geometry.verts) > 0:
            geometries += 1
        else:
            geometry_errors += 1
    except Exception:
        geometry_errors += 1
print(json.dumps({'schema': model.schema, 'projects': len(model.by_type('IfcProject')),
    'products': len(model.by_type('IfcProduct')), 'schema_errors': len(logger.statements),
    'geometries': geometries, 'geometry_errors': geometry_errors,
    'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'python': platform.python_version(), 'ifcopenshell': ifcopenshell.__version__}))
'''
EXPRESS_SCRIPT = '''
import hashlib, json, platform, sys
from pathlib import Path
import ifcopenshell
import ifcopenshell.validate
source = Path(sys.argv[1])
model = ifcopenshell.open(str(source))
logger = ifcopenshell.validate.json_logger()
ifcopenshell.validate.validate(model, logger, express_rules=True)
print(json.dumps({'schema': model.schema, 'express_errors': len(logger.statements),
    'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'python': platform.python_version(), 'ifcopenshell': ifcopenshell.__version__}))
'''


@pytest.mark.skipif(not NATIVE, reason='explicit keyless parallel batch CLI in existing Docker')
@pytest.mark.parametrize('case_ids,arms,slots', [
    (('case-002',), 'ABCDEFG', 2),
    (('case-001', 'case-002'), 'BE', 4),
    (('case-002',), 'ABCDEF', 6),
], ids=['seven-groups-two-slots', 'be-two-cases-four-slots', 'six-groups-six-slots'])
def test_paired_directory_public_cli_runs_seven_groups_in_two_slots(tmp_path, case_ids, arms, slots):
    """Public paired inputs, real Linux tools, fake HTTP, one bounded summary."""
    from scripts.ifc_repair.repair_comparison import batch_workflow as batch

    # Explicitly reuse a completed *offline* batch when only an assertion was
    # corrected. Resuming terminal tasks performs no new model/tool calls.
    reuse = os.environ.get('REPAIR_SCALABLE_COMPLETE_ROOT')
    root = Path(reuse).resolve() if reuse else tmp_path/'parallel-batch'
    inputs = root.parent/'public-inputs'
    cli = [sys.executable, '-m', 'scripts.ifc_repair.repair_comparison.batch_operator']
    environment = _offline_environment()
    expected_groups = {case: list(arms) for case in case_ids}
    task_count = len(case_ids) * len(arms)
    prior_calls = None
    if reuse:
        assert arms != 'BE', 'B/E concurrency validation requires a fresh native runtime bundle.'
        value = batch.plan(root)
        assert value['mode'] == 'offline' and value['selection'] == 'full'
        assert value['scheduler'] == {'max_running': slots}
        assert value['configuration']['case_groups'] == expected_groups
        ledger = Ledger(root/'control.sqlite')
        assert all(ledger.snapshot(run)['status']=='submitted' for run in value['configuration']['order'])
        prior_calls = {run: ledger.calls(run) for run in value['configuration']['order']}
    else:
        inputs.mkdir()
        for case in case_ids:
            for source, suffix in (('model.ifc', '.ifc'), ('request.txt', '.txt')):
                shutil.copyfile(carrier.CASES/case/'public'/source, inputs/(case+suffix))
        with (inputs/'inputs.csv').open('w', newline='', encoding='utf8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['case_id', 'ifc_path', 'request_path', 'level', 'primary_target_count', 'task_kind'])
            for case in case_ids:
                writer.writerow([case, case+'.ifc', case+'.txt', 'S1', '1', 'geometry'])
        prepared = subprocess.run(cli+['prepare', '--root', str(root), '--dataset', str(inputs),
            '--input-format', 'pairs', '--scope', 'full', '--concurrency', str(slots),
            '--mode', 'offline', '--groups', *arms] + (['--retain-debug'] if arms == 'BE' else []),
            cwd=REPO, env=environment, capture_output=True, text=True, encoding='utf8', timeout=150)
        assert prepared.returncode == 0, 'Public paired prepare failed.'
        preparation = json.loads(prepared.stdout)
        assert preparation['tasks'] == task_count and preparation['concurrency'] == slots
    before = {p.name: sha256(p) for p in inputs.iterdir()}
    for case in case_ids:
        assert sha256(inputs/(case+'.ifc')) == sha256(carrier.CASES/case/'public/model.ifc')
        assert sha256(inputs/(case+'.txt')) == sha256(carrier.CASES/case/'public/request.txt')
        assert {p.name for p in (root/'cases'/case/'public').iterdir()} == {'model.ifc', 'request.txt'}
    runtime_bindings = carrier.bindings(batch.plan(root)['configuration'])
    write_json(tmp_path/'parallel-runtime-bindings-before.json', runtime_bindings)
    process = subprocess.Popen(cli+['run', '--root', str(root)], cwd=REPO, env=environment,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=1200)
    except subprocess.TimeoutExpired:
        batch.pause(root)
        # Cooperative drain preserves unresolved native owners; no process kill.
        try:
            stdout, stderr = process.communicate(timeout=180)
        except subprocess.TimeoutExpired:
            pytest.fail('Parallel native smoke paused; unresolved owner retained at '+str(root))
        pytest.fail('Parallel native smoke exceeded its limit and cooperatively paused.')
    if process.returncode:
        (tmp_path/'bounded-failure.txt').write_bytes(stderr[-16384:])
        (tmp_path/'failure-summary.json').write_bytes(stdout[-2048:])
    assert process.returncode == 0, 'Parallel CLI failed; inspect retained bounded summary.'
    assert stderr == b''
    lines = stdout.decode('utf8').splitlines()
    assert len(lines) == 1 and len(stdout) < 2048
    summary = json.loads(lines[0])
    assert summary['event'] == 'summary' and summary['state'] == 'complete'
    assert summary['completed'] == summary['total'] == task_count
    assert summary['status_counts'] == {'submitted': task_count}
    assert summary['active_count'] == 0 and summary['unknown_calls'] == 0
    ledger = Ledger(root/'control.sqlite')
    config = read_json(root/'experiment.json')
    with closing(sqlite3.connect(root/'control.sqlite')) as db:
        edges = db.execute("SELECT kind FROM events WHERE kind IN ('started','terminal') ORDER BY at,seq").fetchall()
        exports = {run: json.loads(raw) for run, raw in db.execute('SELECT run_id,summary FROM batch_exports')}
    active = peak = 0
    for (kind,) in edges:
        active += 1 if kind == 'started' else -1
        peak = max(peak, active)
        assert 0 <= active <= slots
    assert peak == slots and active == 0
    for run in config['order']:
        case, arm = run.rsplit('-', 1)
        output = root/'results'/case/arm
        assert {p.name for p in output.iterdir()} == {'report.md', 'repaired.ifc'}
        assert (output/'report.md').stat().st_size <= 65536
        check = exports[run]['common_format_validation']
        assert check['passed'] and check['status'] == 'passed'
        report = (output/'report.md').read_text(encoding='utf8')
        if arms == 'BE':
            diagnostics = exports[run]['scene_diagnostics']
            assert isinstance(diagnostics, dict) and diagnostics['rounds']
            assert diagnostics['terminal_reason'] == 'repair_intent'
            assert 'Bounded scene diagnostics (missing means not retained):' in report
        section = report.split('Common format validation (separate from submission and task score):', 1)[1]
        detail = json.loads(section.split('```json', 1)[1].split('```', 1)[0])['detail']
        assert detail['passed'] and detail['express_rules'] and detail['diagnostic_count'] == 0
        state = ledger.snapshot(run)
        assert state['mode'] == 'real_runtime_fake_model' and not state['activities']
        assert state['budget'] == fixed_budget_profile('S1')
        assert state['metadata']['runtime']['model_requested'] == config['models'][arm]
        assert not any(c['state'] == 'inflight' or c['failed'] for c in ledger.calls(run))
        assert not any(e['kind'] == 'controller_request_rejected' for e in ledger.events(run))
        _stopped(config['routes'][run]['container'])
        assert (root/'workspaces'/run).exists() is (arms == 'BE')
    if arms == 'BE':
        from scripts.ifc_repair.repair_comparison.group_config import harness_profile
        calls_before = {run: ledger.calls(run) for run in config['order']}
        with closing(sqlite3.connect(root/'control.sqlite')) as db:
            states_before = db.execute('SELECT run_id,state FROM runs ORDER BY run_id').fetchall()
        snapshot_hashes = None
        for attempt in range(2):
            exported = subprocess.run(cli+['debug-export', '--root', str(root)], cwd=REPO,
                env=environment, capture_output=True, text=True, encoding='utf8', timeout=600)
            assert exported.returncode == 0, exported.stdout + exported.stderr
            assert exported.stderr == '' and len(exported.stdout.splitlines()) == 1
            detail = json.loads(exported.stdout)
            assert detail['debug_snapshots'] == task_count
            assert detail['exported'] == (task_count if attempt == 0 else 0)
            assert detail['reused'] == (task_count if attempt == 1 else 0)
            for run in config['order']:
                case, arm = run.rsplit('-', 1)
                receipt = read_json(root/'debug'/run/'receipt.json')
                task = read_json(root/'debug'/run/'state/task.json')
                assert task['run_id'] == run
                assert task['source_sha256'] == sha256(root/'cases'/case/'public/model.ifc')
                assert task['request_sha256'] == sha256(root/'cases'/case/'public/request.txt')
                assert task['model_profile'] == harness_profile(config, arm)
                assert receipt['identity']['binding'] == {k: task[k] for k in receipt['identity']['binding']}
            current_hashes = {str(p.relative_to(root/'debug')): sha256(p)
                              for p in (root/'debug').rglob('*') if p.is_file()}
            if snapshot_hashes is not None:
                assert current_hashes == snapshot_hashes
            snapshot_hashes = current_hashes
        assert {run: ledger.calls(run) for run in config['order']} == calls_before
        with closing(sqlite3.connect(root/'control.sqlite')) as db:
            assert db.execute('SELECT run_id,state FROM runs ORDER BY run_id').fetchall() == states_before
    if prior_calls is not None:
        assert {run: ledger.calls(run) for run in config['order']} == prior_calls
    assert read_json(root/'service.json')['state'] == 'stopped'
    assert {p.name: sha256(p) for p in inputs.iterdir()} == before
    batch._source_guard(root, batch.plan(root))
    assert carrier.bindings(batch.plan(root)['configuration']) == runtime_bindings
    write_json(tmp_path/'parallel-summary-receipt.json', {
        'scope': 'Public paired CLI, selected native executors, fake HTTP only; no live model admission.',
        'case_groups': expected_groups,
        'runtime_bindings': runtime_bindings,
        'summary': summary, 'concurrency_peak': peak, 'source_unchanged': True,
        'service_stopped': True, 'minimal_exports': True, 'ifc_schema_express_passed': True,
        'no_live_api_calls': True, 'scene_diagnostics_checked': arms == 'BE',
        'debug_export_reuse_checked': arms == 'BE',
        'reused_complete_batch': bool(reuse), 'experiment_root': str(root)})


@pytest.mark.skipif(not NATIVE, reason='explicit keyless batch CLI smoke in existing Docker')
def test_batch_public_cli_exports_minimal_results_and_one_summary(tmp_path):
    """One real tool task plus budget exhaustion; no live API or full-matrix claim."""
    from scripts.ifc_repair.repair_comparison import batch_workflow as batch

    root = tmp_path/'batch'
    cases = root/'cases'
    bindings = {}
    for case in ('case-002', 'case-003'):
        public = cases/case/'public'
        public.mkdir(parents=True)
        for name in ('model.ifc', 'request.txt'):
            shutil.copyfile(carrier.CASES/'case-002'/'public'/name, public/name)
        bindings[case] = {'input_digests': {name: sha256(public/name)
                         for name in ('model.ifc', 'request.txt')}, 'metadata_bindings': {}}
    # Synthetic offline boundary budget, not a change to the real S1/S2/S3 policy.
    tiny = {**fixed_budget_profile('S1'), 'tokens': 1, 'calls': 1}
    configuration = carrier.batch_configuration(cases_root=cases,
        case_ids=['case-002', 'case-003'], budgets={'case-002': fixed_budget_profile('S1'), 'case-003': tiny},
        stage=SCALABLE_STAGE, providers=default_providers(), case_groups={'case-002': ['A'], 'case-003': ['C']},
        scene_grounding=True, b_validation_corrections=2)
    value = {'schema_version': batch.PLAN_SCHEMA, 'mode': 'offline',
             'budget_policy': batch.TASK_BUDGET_ONLY, 'configuration': configuration,
             'rounds': {'round1': ['case-002'], 'round2': ['case-003']}, 'input_bindings': bindings}
    value['sha256'] = batch._digest(value)
    write_json(root/'batch.json', value)
    command = [sys.executable, '-m', 'scripts.ifc_repair.repair_comparison.batch_operator',
               'run', '--root', str(root)]
    process = subprocess.Popen(command, cwd=REPO, env=_offline_environment(),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=600)
    except subprocess.TimeoutExpired:
        batch.pause(root)
        # Preserve an unresolved owner instead of killing its models or tools.
        stdout, stderr = process.communicate(timeout=150)
        pytest.fail('Offline batch exceeded its smoke limit and cooperatively paused.')
    if process.returncode:
        (tmp_path/'bounded-failure.txt').write_bytes(stderr[-16384:])
        (tmp_path/'failure-summary.json').write_bytes(stdout[-2048:])
    assert process.returncode == 0, 'Public CLI failed; inspect retained bounded-failure.txt.'
    assert stderr == b''
    lines = stdout.decode('utf8').splitlines()
    assert len(lines) == 1 and len(stdout) < 2048
    summary = json.loads(lines[0])
    assert summary['event'] == 'summary' and summary['state'] == 'complete'
    assert summary['completed'] == summary['total'] == 2
    assert summary['status_counts'] == {'budget_exhausted': 1, 'submitted': 1}
    output = root/'results/case-002/A'
    assert {p.name for p in output.iterdir()} == {'report.md', 'repaired.ifc'}
    assert (output/'report.md').stat().st_size <= 65536
    empty = root/'results/case-003/C'
    assert {p.name for p in empty.iterdir()} == {'report.md'}
    assert read_json(root/'service.json')['state'] == 'stopped'
    config = read_json(root/'experiment.json')
    for run_id in configuration['order']:
        _stopped(config['routes'][run_id]['container'])
        assert not (root/'workspaces'/run_id).exists()
    batch._source_guard(root, value)
    ledger = Ledger(root/'control.sqlite')
    assert all(ledger.snapshot(run)['mode'] == 'real_runtime_fake_model' for run in configuration['order'])
    assert all(not s['activities'] for s in carrier.status(root))
    assert ledger.snapshot('case-002-A')['artifact'] is not None
    write_json(tmp_path/'summary-receipt.json', {'scope': 'offline fake-provider public batch CLI only',
        'summary': summary, 'source_unchanged': True, 'service_stopped': True,
        'minimal_exports': True, 'no_live_api_calls': True})


def _runtime_bindings(configuration):
    value = carrier.bindings(configuration)
    excluded = {'batch_workflow.py', 'batch_operator.py', 'batch_cases.py', 'results.py',
                'formal_admission.py', 'formal_workflow.py'}
    value['files'] = {name: digest for name, digest in value['files'].items()
                      if Path(name).name not in excluded}
    return value


def _offline_environment():
    environment = dict(os.environ)
    for name in ('OPENAI_API_KEY', 'DEEPSEEK_API_KEY', 'ANTHROPIC_API_KEY',
                 'DEEPSEEK_SEARCH_API_KEY', 'QWEN_API_KEY'):
        environment.pop(name, None)
    environment['PYTHONUTF8'] = '1'
    return environment


def _wait_service(root, service, timeout=90):
    deadline = time.monotonic() + timeout
    while True:
        path = root/'service.json'
        if path.exists() and read_json(path).get('state') == 'running':
            return
        assert service.poll() is None, 'Keyless service exited; inspect retained service.log.'
        assert time.monotonic() < deadline, 'Keyless service startup timed out.'
        time.sleep(.2)


def _stopped(name):
    running = carrier.docker('ps', '--filter', f'name=^/{name}$', '--format', '{{.Names}}')
    assert not running, 'Task-owned native container is still running: ' + name


def _volume_binding(config, run_id):
    volume = config['routes'][run_id]['volume']
    value = carrier.docker('run', '--rm', '--pull=never', '--network=none', '--read-only',
        '--user=65532:65532', '--cap-drop=ALL', '--security-opt=no-new-privileges',
        '--memory=256m', '--cpus=1', '--pids-limit=32',
        '--mount', f'type=volume,source={volume},target=/state,readonly,volume-nocopy',
        IMAGE, 'python', '-c', 'from pathlib import Path; print(Path("/state/task.json").read_text())')
    return json.loads(value)


def _reopen_frozen(artifact, evidence_directory, run_id):
    tools = ContainerTools(artifact.parent, tool_seconds=120)
    result = tools.execute(['python', '-c', REOPEN_SCRIPT,
                            'IfcWindow' if run_id.startswith('case-001-') else 'IfcDoor'], timeout_s=120)
    record = tools.records[-1]
    path = evidence_directory/(run_id+'-reopen.json')
    write_json(path, {'linux_command': result, 'linux_container': record})
    assert result['quiescent'] and not result['timed_out'], run_id + ' IFC reopen did not stop cleanly.'
    assert result['exit_code'] == 0, run_id + ' frozen IFC reopen failed; inspect retained evidence.'
    value = json.loads(result['stdout'])
    assert value['schema'] == 'IFC2X3' and value['projects'] == 1
    assert value['products'] > 0 and value['schema_errors'] == 0, (run_id, value['schema_errors'])
    assert value['geometries'] > 0 and value['geometry_errors'] == 0
    assert value['sha256'] == sha256(artifact)
    assert value['python'].startswith('3.12.') and value['ifcopenshell'] == '0.8.5'
    assert not record['state']['Running'] and record['state']['Pid'] == 0
    assert record['network_mode'] == 'none'
    host = subprocess.run([sys.executable, '-c', EXPRESS_SCRIPT, str(artifact)], cwd=REPO,
                           env=_offline_environment(), capture_output=True, text=True,
                           encoding='utf8', timeout=120)
    host_command = {'exit_code': host.returncode, 'stdout': host.stdout, 'stderr': host.stderr}
    write_json(path, {'linux_validation': value, 'linux_command': result,
                     'linux_container': record, 'host_express_command': host_command})
    assert host.returncode == 0, run_id + ' host EXPRESS script failed; inspect retained evidence.'
    express = json.loads(host.stdout)
    assert express['schema'] == value['schema'] and express['sha256'] == value['sha256']
    assert express['ifcopenshell'] == '0.8.5' and express['express_errors'] == 0
    return {'file': file_ref(path), 'schema': value['schema'], 'express_errors': express['express_errors'],
            'reopen_environment': 'linux', 'schema_environment': 'linux',
            'geometry_environment': 'linux', 'express_environment': 'host',
            'geometry_count': value['geometries'], 'geometry_errors': 0,
            'python': value['python'], 'ifcopenshell': value['ifcopenshell'],
            'container_stopped': True}


def _native_timeout_check(tmp_path):
    work = tmp_path/'timeout-workspace'
    work.mkdir()
    tools = ContainerTools(work, tool_seconds=1)
    result = tools.execute(['python', '-c', 'import time; time.sleep(30)'], timeout_s=1)
    assert result['timed_out'] and result['quiescent']
    assert len(tools.records) == 1
    record = tools.records[0]
    assert not record['state']['Running'] and record['state']['Pid'] == 0
    assert record['network_mode'] == 'none'
    _stopped(record['container'])
    path = tmp_path/'native-timeout-stop.json'
    write_json(path, {'command': result, 'container': record, 'stopped': True})
    return {'quiescent': result['quiescent'], 'timed_out': result['timed_out'],
            'container_stopped': True, 'evidence': file_ref(path)}


def _native_grid(tmp_path, request, *, case_groups, property_runtime=False, receipt_name='native-stage.json'):
    root = tmp_path/'runtime'
    logs = tmp_path/'logs'
    logs.mkdir()
    validations = tmp_path/'reopened'
    validations.mkdir()
    cases = list(case_groups)
    public_hashes = {(case, name): sha256(carrier.CASES/case/'public'/name)
                     for case in cases for name in ('model.ifc', 'request.txt')}
    providers = default_providers()
    providers['qwen']['request_options'] = {'chat_template_kwargs': {'enable_thinking': False}}
    config = carrier.initialize(root, mode='offline', cases_root=carrier.CASES, case_ids=cases,
        budgets={case: fixed_budget_profile('S1') for case in cases}, stage=SCALABLE_STAGE,
        providers=providers, case_groups=case_groups,
        scene_grounding=True, b_validation_corrections=2,
        b={'image': PROPERTY_RUNTIME_IMAGE,
           'property_model_directory': str(REPO/'.cache/models/BAAI-bge-m3')} if property_runtime else None)
    task_count = sum(len(groups) for groups in case_groups.values())
    first_arm = 'F' if 'F' in case_groups['case-001'] else case_groups['case-001'][0]
    assert config['order'][0] == 'case-001-'+first_arm
    assert len(config['order']) == task_count and config['mode'] == 'offline'
    assert all(state['mode'] == 'real_runtime_fake_model' for state in carrier.status(root))
    config['fixture_scenarios'] = {'case-001-F': 'question'}
    write_json(root/'experiment.json', config)
    bindings_before = _runtime_bindings(config['configuration'])
    images = bindings_before['images']
    environment = _offline_environment()
    ledger = Ledger(root/'control.sqlite')
    commands = []
    rows = []
    observed_containers = {}
    service_output = (logs/'service.log').open('wb')
    service = subprocess.Popen(CLI+['serve', '--root', str(root)], cwd=REPO, env=environment,
                               stdout=service_output, stderr=subprocess.STDOUT)

    def call(action, *arguments, timeout=600):
        command = CLI+[action, '--root', str(root), *map(str, arguments)]
        log = logs/f'{len(commands):02d}-{action}.log'
        try:
            inspect_run = (property_runtime and action == 'run'
                           and ledger.snapshot(arguments[1])['status'] in {'ready', 'running'})
            if inspect_run:
                run_id = arguments[1]
                container_name = config['routes'][run_id]['container']
                with log.open('w', encoding='utf8') as output:
                    process = subprocess.Popen(command, cwd=REPO, env=environment, stdout=output,
                                               stderr=subprocess.STDOUT, text=True, encoding='utf8')
                    deadline = time.monotonic()+timeout
                    observation = None
                    while process.poll() is None and observation is None:
                        inspection = subprocess.run(['docker', 'inspect', container_name],
                            capture_output=True, text=True, encoding='utf8', timeout=15)
                        if inspection.returncode == 0:
                            candidate = json.loads(inspection.stdout)[0]
                            if candidate['State']['Running']:
                                observation = candidate
                                break
                        if time.monotonic() >= deadline:
                            process.kill()
                            process.wait(timeout=30)
                            raise subprocess.TimeoutExpired(command, timeout)
                        time.sleep(.2)
                    try:
                        process.wait(timeout=max(.1, deadline-time.monotonic()))
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=30)
                        raise
                assert observation is not None, run_id+' property worker was not observed in Linux.'
                assert observation['Image'] == images[PROPERTY_RUNTIME_IMAGE]
                mounts = {row['Destination']: row for row in observation['Mounts']}
                assert '/models/bge-m3' in mounts and not mounts['/models/bge-m3']['RW']
                observed_path = logs/f'{len(commands):02d}-{run_id}-container.json'
                write_json(observed_path, {'name': container_name, 'image': observation['Image'],
                    'state': observation['State'], 'mounts': observation['Mounts'],
                    'network_mode': observation['HostConfig']['NetworkMode']})
                observed_containers.setdefault(run_id, []).append(file_ref(observed_path))
                result = subprocess.CompletedProcess(command, process.returncode,
                    stdout=log.read_text(encoding='utf8'), stderr='')
            else:
                result = subprocess.run(command, cwd=REPO, env=environment, capture_output=True,
                                        text=True, encoding='utf8', timeout=timeout)
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout or b''
            stderr = error.stderr or b''
            if isinstance(stdout, bytes):
                stdout = stdout.decode('utf8', errors='replace')
            if isinstance(stderr, bytes):
                stderr = stderr.decode('utf8', errors='replace')
            log.write_text(stdout+'\nSTDERR\n'+stderr, encoding='utf8')
            pytest.fail(f'{action} exceeded its native-test deadline; retained log: {log}')
        log.write_text(result.stdout+'\nSTDERR\n'+result.stderr, encoding='utf8')
        commands.append({'action': action, 'arguments': list(map(str, arguments)),
                         'exit_code': result.returncode, 'log': file_ref(log)})
        assert result.returncode == 0, f'{action} CLI failed; retained log: {log}'
        return json.loads(result.stdout)

    try:
        _wait_service(root, service)
        for run_id in config['order']:
            case, arm = run_id.rsplit('-', 1)
            kind = executor(config, arm)
            initial = call('run', '--run-id', run_id)
            pending_binding = None
            if run_id == 'case-001-F':
                assert initial['status'] == 'awaiting_user', 'Qwen Harness did not retain its pending clarification.'
                assert not initial['activities'] and initial['artifact'] is None
                pending_binding = _volume_binding(config, run_id)
                assert pending_binding['model_profile'] == harness_profile(config, arm)
                assert pending_binding['scene_grounding_version'] == config['scene_grounding_version']
                assert pending_binding['max_validation_corrections'] == 2
                if property_runtime:
                    assert pending_binding['property_runtime_version'] == PROPERTY_RUNTIME_VERSION
                _stopped(config['routes'][run_id]['container'])
                paused = call('run', '--run-id', run_id)
                assert paused['status'] == 'awaiting_user'
                assert paused['usage']['calls'] == initial['usage']['calls']
                assert paused['active_elapsed_s'] == initial['active_elapsed_s']
                answer = tmp_path/'qwen-public-answer.json'
                write_json(answer, {'text': '窗宽915毫米。', 'event_id': 'native-qwen-public-width'})
                call('answer', '--run-id', run_id, '--answer-file', answer)
                state = call('run', '--run-id', run_id)
                assert state['usage']['calls'] > initial['usage']['calls']
                assert state['budget'] == initial['budget'] == fixed_budget_profile('S1')
            else:
                state = initial
            assert state['status'] == 'submitted', (run_id, state['status'])
            assert state['mode'] == 'real_runtime_fake_model' and not state['activities']
            assert state['budget'] == fixed_budget_profile('S1')
            assert state['usage']['coverage'] == 'complete' and state['usage']['unknown_calls'] == 0
            assert state['usage']['calls'] > 0 and state['usage']['known_total_tokens'] > 0
            assert all(row['state'] == 'completed' and not row['failed'] for row in ledger.calls(run_id))
            assert not any(event['kind'] == 'controller_request_rejected' for event in ledger.events(run_id))
            assert state['metadata']['runtime']['model_requested'] == config['models'][arm]
            artifact = Path(state['artifact']['path'])
            assert artifact == (root/'artifacts'/run_id/'result.ifc').resolve()
            assert sha256(artifact) == state['artifact']['sha256']
            assert list((root/'artifacts'/run_id).glob('*.ifc')) == [artifact]
            work = root/'workspaces'/run_id
            assert sha256(work/'model.ifc') == public_hashes[case, 'model.ifc']
            assert sha256(root/'inputs'/case/'model.ifc') == public_hashes[case, 'model.ifc']
            assert sha256(work/state['artifact']['submitted_path']) == state['artifact']['sha256']
            assert not (work/'private').exists()
            reopen = _reopen_frozen(artifact, validations, run_id)
            row = {'run_id': run_id, 'arm': arm, 'executor': kind, 'provider': GROUPS[arm][0],
                   'model': config['models'][arm], 'status': state['status'], 'mode': state['mode'],
                   'public_source': file_ref(carrier.CASES/case/'public/model.ifc'),
                   'artifact': file_ref(artifact), 'reopen': reopen, 'source_unchanged': True,
                   'calls': state['usage']['calls'], 'known_tokens': state['usage']['known_total_tokens']}
            if kind == 'harness':
                binding_path = root/'runtime'/run_id/'state/task.json'
                binding = read_json(binding_path)
                assert binding['model_profile'] == harness_profile(config, arm)
                assert binding['model'] == config['models'][arm]
                assert binding['scene_grounding_version'] == config['scene_grounding_version']
                assert binding['max_validation_corrections'] == 2
                if property_runtime:
                    assert binding['property_runtime_version'] == PROPERTY_RUNTIME_VERSION
                    assert state['metadata']['runtime']['image'] == PROPERTY_RUNTIME_IMAGE
                    assert observed_containers.get(run_id)
                    row['native_containers'] = observed_containers[run_id]
                if pending_binding is not None:
                    assert binding == pending_binding
                    row['clarification_resume_profile_preserved'] = True
                row['native_binding'] = file_ref(binding_path)
            elif kind == 'direct':
                native_commands = read_json(root/'runtime'/(run_id+'-commands.json'))
                assert native_commands, run_id + ' did not execute its Linux tools.'
                assert all(not item['state']['Running'] and item['state']['Pid'] == 0 for item in native_commands)
                assert all(item['network_mode'] == 'none' and item['image'] == images[IMAGE] for item in native_commands)
                row['native_commands'] = file_ref(root/'runtime'/(run_id+'-commands.json'))
            else:
                control = root/'runtime'/run_id
                native = read_json(control/'result.json')
                assert native['ok'] and native['result']['finish_reason'] != 'error'
                container = read_json(control/'container.json')
                assert not container['State']['Running'] and container['State']['Pid'] == 0
                assert not container['State']['OOMKilled'] and container['Image'] == images[carrier.DSH_IMAGE]
                versions = read_json(control/'versions.json')
                assert versions['deepseek-harness-sdk'] == versions['deepseek-harness-runtime-bin'] == '0.2.0rc1'
                assert versions['ifcopenshell'] == '0.8.5' and versions['python'].startswith('3.12.')
                row.update(native_versions=file_ref(control/'versions.json'),
                           native_container=file_ref(control/'container.json'))
            _stopped(config['routes'][run_id]['container'])
            rows.append(row)
            print('SCALABLE_NATIVE_COMPLETED '+run_id+' '+kind, flush=True)
        assert {row['arm'] for row in rows if row['run_id'].startswith('case-001-')} == set(case_groups['case-001'])
        assert len({row['artifact']['path'] for row in rows}) == task_count
        assert all(sha256(carrier.CASES/case/'public'/name) == value
                   for (case, name), value in public_hashes.items())
        final = call('status')
        assert {row['run_id'] for row in final} == set(config['order'])
        assert all(row['status'] == 'submitted' and not row['activities'] for row in final)
        call('stop')
        service.wait(timeout=45)
        assert service.returncode == 0
        assert read_json(root/'service.json')['state'] == 'stopped'
        _stopped(config['relay'])
        bindings_after = _runtime_bindings(config['configuration'])
        assert bindings_before == bindings_after, 'Native carrier/public bindings changed during this test.'
    finally:
        if service.poll() is None:
            for route in config['routes'].values():
                result = subprocess.run(['docker', 'inspect', route['container']], capture_output=True,
                                        text=True, encoding='utf8', timeout=30)
                if result.returncode == 0:
                    carrier.docker('stop', '--time', '2', route['container'])
                    _stopped(route['container'])
            carrier.request_service_stop(root)
            try:
                service.wait(timeout=45)
            except subprocess.TimeoutExpired:
                service.terminate()
                service.wait(timeout=30)
            result = subprocess.run(['docker', 'inspect', config['relay']], capture_output=True,
                                    text=True, encoding='utf8', timeout=30)
            if result.returncode == 0:
                carrier.docker('stop', '--time', '2', config['relay'])
                _stopped(config['relay'])
        service_output.close()
    timeout_stop = _native_timeout_check(tmp_path)
    evidence = tmp_path/receipt_name
    write_json(evidence, {'schema_version': 'repair-comparison-scalable-native-smoke/0.1',
        'nodeid': request.node.nodeid, 'test_file': file_ref(Path(__file__)),
        'experiment_root': str(root.resolve()), 'configuration': config['configuration'],
        'images': images, 'runs': rows, 'commands': commands,
        'runtime_bindings_before': bindings_before, 'runtime_bindings_after': bindings_after,
        'timeout_stop': timeout_stop, 'service_log': file_ref(logs/'service.log'),
        'real_models_called': False, 'real_credentials_used': False, 'all_passed': True,
        'scope': 'Keyless fake HTTP wiring and publication only; no live model scores or capability evidence.'})
    print('SCALABLE_NATIVE_RECEIPT '+str(evidence.resolve()), flush=True)


@pytest.mark.skipif(not NATIVE, reason='explicit keyless seven-group native Docker admission run')
def test_seven_groups_actual_linux_cli_and_qwen_profile_resume(tmp_path, request):
    _native_grid(tmp_path, request,
        case_groups={'case-001': list('ABCDEFG'), 'case-002': ['F']})


@pytest.mark.skipif(not NATIVE, reason='explicit keyless Harness property-image Docker admission run')
def test_harness_profiles_existing_property_image_and_qwen_resume(tmp_path, request):
    _native_grid(tmp_path, request, case_groups={'case-001': list('BEF')},
                 property_runtime=True, receipt_name='property-native-stage.json')


@pytest.mark.skipif(not NATIVE, reason='explicit keyless GPT Harness Docker admission run')
def test_gpt_harness_existing_property_runtime_public_cli(tmp_path, request):
    _native_grid(tmp_path, request, case_groups={'case-001': ['E'], 'case-002': ['E']},
                 property_runtime=True, receipt_name='property-native-stage.json')
