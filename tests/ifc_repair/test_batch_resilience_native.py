"""Real Linux A/D/E batch CLI, first-429 injection, genuine terminal evidence."""
from contextlib import closing
import csv
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

import pytest

from scripts.ifc_repair import batch_resilience as resilience
from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json, sha256
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from tests.ifc_repair.repair_comparison.test_scalable_native import _offline_environment


@pytest.mark.skipif(os.environ.get('REPAIR_RESILIENCE_DOCKER') != '1',
                    reason='explicit keyless operational transport acceptance')
def test_resilient_actual_linux_public_cli_retries_and_preserves_native_tools(tmp_path):
    before = sha256(carrier.REPO/resilience.MODULE)
    driver = tmp_path/'driver.py'
    driver.write_text('''import sys, threading
from pathlib import Path
import httpx
from scripts.ifc_repair import batch_resilience as operations
from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison import batch_workflow as batch
argv = sys.argv[1:]
root = Path(argv[argv.index('--root')+1])
if argv[0] == 'prepare':
    raise SystemExit(batch.main(argv))
operations.install(root, policy=operations.Policy(desktop_notifications=False))
if argv[0] != 'worker':
    batch.CLI = [sys.executable, __file__, 'worker']
    raise SystemExit(batch.main(argv))
base = carrier.WireGateway
def gateway(*args, **kwargs):
    transport = kwargs.get('transport')
    if not isinstance(transport, httpx.MockTransport):
        raise ValueError('KEYLESS_OFFLINE_TRANSPORT_REQUIRED')
    seen, lock = {}, threading.Lock()
    class BrokenBody(httpx.SyncByteStream):
        def __iter__(self):
            yield b'data: {"partial":true}\\n\\n'
            raise httpx.RemoteProtocolError('injected post-200 disconnect')
    def first_busy(request):
        key = request.url.path
        with lock:
            attempt = seen.get(key, 0)
            seen[key] = attempt+1
        if attempt == 0:
            return httpx.Response(429, json={'error': {'code':'rate_limit'}})
        if attempt == 1:
            return httpx.Response(200, stream=BrokenBody(),
                                  headers={'Content-Type':'text/event-stream'})
        return transport.handle_request(request)
    kwargs['transport'] = httpx.MockTransport(first_busy)
    return base(*args, **kwargs)
carrier.WireGateway = gateway
sys.argv = [sys.argv[0], *argv[1:]]
carrier.main()
''', encoding='utf8')
    inputs, root = tmp_path/'inputs', tmp_path/'batch'
    inputs.mkdir()
    for name, destination in [('model.ifc', 'case-001.ifc'), ('request.txt', 'case-001.txt')]:
        shutil.copyfile(carrier.CASES/'case-001/public'/name, inputs/destination)
    with (inputs/'inputs.csv').open('w', newline='', encoding='utf8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['case_id', 'ifc_path', 'request_path', 'level', 'primary_target_count', 'task_kind'])
        writer.writerow(['case-001', 'case-001.ifc', 'case-001.txt', 'S1', '1', 'geometry'])
    public_before = {path.name: sha256(path) for path in inputs.iterdir()}
    commands, environment = [], _offline_environment()
    environment['PYTHONPATH'] = str(carrier.REPO/'src')+os.pathsep+str(carrier.REPO)
    def call(arguments, *, timeout=1200):
        command = [sys.executable, str(driver), *arguments, '--root', str(root)]
        commands.append(command)
        log = tmp_path/f'command-{len(commands)}.log'
        with log.open('wb') as output:
            process = subprocess.Popen(command, cwd=carrier.REPO, env=environment,
                                       stdout=output, stderr=subprocess.STDOUT)
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                batch.pause(root)
                pytest.fail('Cooperative pause requested; unresolved owner/evidence retained at '+str(root))
        assert code == 0, 'Actual native public CLI failed; evidence retained at '+str(log)
        return log
    call(['prepare', '--dataset', str(inputs), '--input-format', 'pairs', '--scope', 'full',
          '--concurrency', '3', '--mode', 'offline', '--groups', 'A', 'D', 'E'])
    bindings_before = carrier.bindings(batch.plan(root)['configuration'])
    run_log = call(['run'])
    summary = json.loads(run_log.read_text(encoding='utf8'))
    assert summary['state'] == 'complete' and summary['status_counts'] == {'submitted': 3}
    assert summary['unknown_calls'] >= 3
    ledger = Ledger(root/'control.sqlite')
    with closing(sqlite3.connect(root/'control.sqlite')) as db:
        exports = {run: json.loads(raw) for run, raw in db.execute('SELECT run_id,summary FROM batch_exports')}
    def ref(path):
        return {'path': str(path.resolve()), 'sha256': sha256(path)}
    rows = []
    for state in batch._states(root):
        calls = ledger.calls(state['run_id'])
        assert state['mode'] == 'real_runtime_fake_model' and not state['activities']
        assert any(c['failed'] and c['response']['http_status'] == 429 for c in calls)
        assert any(c['failed'] and c['response']['http_status'] == 200
                   and c['response']['error_type'] == 'RemoteProtocolError' for c in calls)
        assert any(e['kind'] == 'provider_request_recovered' for e in ledger.events(state['run_id']))
        assert exports[state['run_id']]['common_format_validation']['passed']
        directory = root/'results'/state['case_id']/state['arm']
        assert {p.name for p in directory.iterdir()} == {'repaired.ifc', 'report.md'}
        assert (directory/'report.md').stat().st_size <= 65536
        rows.append({'arm': state['arm'], 'status': state['status'], 'artifact': ref(directory/'repaired.ifc')})
    bindings_after = carrier.bindings(batch.plan(root)['configuration'])
    assert bindings_before == bindings_after
    assert public_before == {path.name: sha256(path) for path in inputs.iterdir()}
    assert sha256(carrier.REPO/resilience.MODULE) == before
    assert read_json(root/'service.json')['state'] == 'stopped'
    baseline = read_json(carrier.REPO/'.tmp/repair-formal-1200-20261011/full/experiment.json')
    admission = read_json(Path(baseline['admission']))
    stop_ref = admission['native_receipts'][0]
    frozen_native = read_json(Path(stop_ref['path']))
    stop = frozen_native.get('timeout_stop', frozen_native.get('native_timeout_stop'))
    assert sha256(Path(stop_ref['path'])) == stop_ref['sha256'] and stop['quiescent']
    receipt = {'all_passed': True, 'real_models_called': False, 'real_credentials_used': False,
               'tested_arms': ['A', 'D', 'E'], 'first_429_recovered': True,
               'post_200_disconnect_recovered': True, 'runs': rows,
               'runtime_bindings_before': bindings_before, 'runtime_bindings_after': bindings_after,
               'timeout_stop': stop, 'reused_stop_evidence': stop_ref,
               'operations_module_sha256': before, 'operations_driver': ref(driver),
               'service_log': ref(run_log), 'operations_test_file': ref(Path(__file__)),
               'commands': commands, 'experiment_root': str(root)}
    write_json(tmp_path/'operations-native-stage.json', receipt)
