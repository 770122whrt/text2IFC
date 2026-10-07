"""Real DSH submission receiver checks; only upstream HTTP responses are fake.

The IFC is an authored public fixture. Copying it tests publication, not repair
quality. No production run, private benchmark, credentials or image is changed.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import httpx
import ifcopenshell
import ifcopenshell.validate
import pytest

from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.contracts import read_json, sha256, write_json
from scripts.ifc_repair.repair_comparison.formal_admission import capture_sources, file_ref
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from tests.ifc_repair.repair_comparison.dsh_fake_gateway import chunks
from tests.ifc_repair.repair_comparison.test_batch_workflow import _formal_public_inputs


RESPONSES = {
    'dsubmit-fenced': '已保留输入并生成唯一交付文件。\n\n```json\n{"submitted_ifc":"output/repaired.ifc"}\n```',
    'dsubmit-ambiguous': '存在两个提交声明。\n```json\n{"submitted_ifc":"output/repaired.ifc"}\n```\n'
                         '```json\n{"submitted_ifc":"output/other.ifc"}\n```',
    'dsubmit-plain': '{"submitted_ifc":"output/repaired.ifc"}',
}
SCENARIOS = {'dsubmit-fenced': 'fenced_with_prose',
             'dsubmit-ambiguous': 'duplicate_declarations', 'dsubmit-plain': 'bare_json'}
PRIVATE_MARKER = 'HOST_ONLY_SYNTHETIC_SENTINEL_NOT_MODEL_INPUT'


class SubmissionTransport:
    def __init__(self, root, config):
        self.root, self.counts = Path(root), {}

    def __call__(self, request):
        run_id = request.url.path.strip('/').split('/')[0]
        case, arm = run_id.rsplit('-', 1)
        assert arm == 'D' and case in RESPONSES
        body = json.loads(request.content)
        assert PRIVATE_MARKER not in json.dumps(body, ensure_ascii=False)
        step = self.counts.get(run_id, 0)
        self.counts[run_id] = step + 1
        if step == 0:
            code = """from pathlib import Path
import shutil
import ifcopenshell
assert not Path('/workspace/private').exists()
assert not Path('/private').exists()
assert not Path('/repo').exists()
source=Path('model.ifc')
before=source.read_bytes()
model=ifcopenshell.open(str(source))
assert model.schema=='IFC2X3' and len(model.by_type('IfcProject'))==1
Path('output').mkdir(exist_ok=True)
shutil.copyfile(source,'output/repaired.ifc')
"""
            if case == 'dsubmit-ambiguous':
                code += "shutil.copyfile(source,'output/other.ifc')\n"
            code += "assert source.read_bytes()==before\nprint('DSUBMIT_NATIVE_COPY_AND_REOPEN_OK')\n"
            command = "python - <<'PUBLIC_FIXTURE'\n" + code + 'PUBLIC_FIXTURE'
            events = chunks(tool=('bash', {'command': command,
                'description': 'Offline receiver fixture: open and copy public IFC',
                'timeoutMs': 120000}, 'public-copy-' + case))
        else:
            assert step == 1, 'No retries or selecting another answer in this fixture.'
            results = [block for message in body['messages']
                       for block in message.get('content', []) if isinstance(block, dict)
                       and block.get('type') == 'tool_result'
                       and block.get('tool_use_id') == 'public-copy-' + case]
            assert len(results) == 1
            assert 'DSUBMIT_NATIVE_COPY_AND_REOPEN_OK' in json.dumps(results[0])
            events = chunks(text=RESPONSES[case])
        content = ''.join('event: ' + event['type'] + '\ndata: ' + json.dumps(event) + '\n\n'
                          for event in events).encode()
        path = self.root/'runtime/dsubmission-upstream.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf8') as handle:
            handle.write(json.dumps({'run_id': run_id, 'step': step, 'request': body,
                'response_status': 200, 'response_body': content.decode(),
                'evidence_class': 'deterministic_controller_upstream'}, ensure_ascii=False) + '\n')
        return httpx.Response(200, headers={'Content-Type': 'text/event-stream'}, content=content)


def submission_fixture_cli():
    from tests.ifc_repair.repair_comparison import test_batch_workflow as base
    base._FormalHTTPTransport = SubmissionTransport
    base._formal_fixture_cli()


def _native_valid(path):
    model = ifcopenshell.open(str(path))
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(model, logger, express_rules=True)
    assert not logger.statements, logger.statements[:3]


@pytest.mark.skipif(os.environ.get('REPAIR_FORMAL_DOCKER') != '1', reason='explicit keyless native DSH receiver validation')
def test_d_submission_real_native_fenced_ambiguous_and_plain(tmp_path):
    before = capture_sources('admission')
    helper_bindings = [file_ref(Path(__file__).with_name(name)) for name in
                       ('test_batch_workflow.py', 'dsh_fake_gateway.py', 'demo_http_fixture.py')]
    public_cases, _, _ = _formal_public_inputs(tmp_path/'authored')
    cases = tmp_path/'cases'
    ids = list(RESPONSES)
    budgets = {}
    for case in ids:
        target = cases/case/'public'
        shutil.copytree(public_cases/'synthetic-001/public', target)
        (target/'request.txt').write_text('这是提交接收器的离线测试。保留输入 IFC 不变，生成副本并声明唯一最终 IFC。', encoding='utf8')
        (target.parent/'private').mkdir()
        (target.parent/'private/sentinel.txt').write_text(PRIVATE_MARKER, encoding='utf8')
        _native_valid(target/'model.ifc')
        budgets[case] = {'tokens': 2500000, 'calls': 8, 'active_seconds': 300,
                         'tool_seconds': 120, 'extensions': []}
    budget_path = tmp_path/'budgets.json'
    write_json(budget_path, budgets)
    root = tmp_path/'experiment'
    logs = tmp_path/'logs'
    logs.mkdir()
    command = [sys.executable, '-c', 'from tests.ifc_repair.repair_comparison.test_d_submission_native_seam import submission_fixture_cli; submission_fixture_cli()']
    commands = []

    def call(action, *arguments, timeout=600):
        argv = command + [action, '--root', str(root), *map(str, arguments)]
        result = subprocess.run(argv, cwd=carrier.REPO, capture_output=True, text=True,
                                encoding='utf8', timeout=timeout)
        log = logs/f'{len(commands):02d}-{action}.log'
        log.write_text(result.stdout + '\nSTDERR\n' + result.stderr, encoding='utf8')
        commands.append({'argv': argv, 'exit_code': result.returncode, 'log': file_ref(log)})
        assert result.returncode == 0, (action, result.stdout[-2000:], result.stderr[-2000:])
        return json.loads(result.stdout)

    config = call('init', '--mode', 'offline', '--cases-root', cases, '--case-ids', *ids,
                  '--budgets', budget_path, '--stage', carrier.FORMAL_STAGE)
    report = {'schema_version': 'repair-comparison-d-submission-native-seams/0.1',
              'real_models_called': False, 'source_bindings': before,
              'configuration': config['configuration'], 'images': carrier.bindings(config['configuration'])['images'],
              'fixture_helpers': helper_bindings,
              'runs': [], 'checks': {}, 'scope': 'Receiver publication only; copying a synthetic public IFC is not model repair evidence.',
              'validation_location': 'Host independent IfcOpenShell native schema/EXPRESS; official DSH container opens and copies IFC without evaluator dependencies.'}
    evidence = tmp_path/'dsubmission-native-seams.json'
    write_json(evidence, report)
    service_log = (logs/'service.log').open('wb')
    service = subprocess.Popen(command + ['serve', '--root', str(root)], cwd=carrier.REPO,
                               stdout=service_log, stderr=subprocess.STDOUT)
    ledger = Ledger(root/'control.sqlite')
    try:
        deadline = time.monotonic() + 90
        while not (root/'service.json').exists() or read_json(root/'service.json').get('state') != 'running':
            assert service.poll() is None and time.monotonic() < deadline, 'Fixture service did not start.'
            time.sleep(.25)
        for case in ids:
            run_id = case + '-D'
            source = cases/case/'public/model.ifc'
            source_hash = sha256(source)
            state = call('run', '--run-id', run_id, timeout=360)
            expected = 'runtime_error' if case == 'dsubmit-ambiguous' else 'submitted'
            assert state['status'] == expected, state
            assert state['mode'] == 'real_runtime_fake_model' and not state['activities']
            assert state['usage']['calls'] == 2 and state['usage']['unknown_calls'] == 0
            assert all(c['state'] == 'completed' and not c['failed'] for c in ledger.calls(run_id))
            events = ledger.events(run_id)
            assert sum(e['kind'] == 'started' for e in events) == 1
            assert sum(e['kind'] == 'd_native_started' for e in events) == 1
            assert not any(e['kind'] == 'controller_request_rejected' for e in events)
            workspace = root/'workspaces'/run_id
            assert sha256(source) == source_hash == sha256(workspace/'model.ifc')
            assert sha256(Path(state['metadata']['input_dir'])/'model.ifc') == source_hash
            assert not (workspace/'private').exists()
            assert (cases/case/'private/sentinel.txt').read_text(encoding='utf8') == PRIVATE_MARKER
            control = root/'runtime'/run_id
            native = read_json(control/'result.json')
            assert native['ok'] and native['result']['finish_reason'] != 'error'
            assert native['result']['final_response'] == RESPONSES[case]
            container = read_json(control/'container.json')
            assert not container['State']['Running'] and container['State']['Pid'] == 0
            assert not container['State']['OOMKilled']
            assert container['Image'] == report['images'][carrier.DSH_IMAGE]
            assert {m['Destination'] for m in container['Mounts']} == {'/workspace', '/opt/carrier', '/state'}
            bindings = {m['Destination']: m for m in container['Mounts']}
            workspace_suffix = '/' + workspace.resolve().relative_to(carrier.REPO).as_posix().lower()
            assert bindings['/workspace']['Source'].replace('\\', '/').lower().endswith(workspace_suffix)
            assert not bindings['/opt/carrier']['RW']
            _native_valid(workspace/'output/repaired.ifc')
            assert sha256(workspace/'output/repaired.ifc') == source_hash
            if expected == 'submitted':
                artifact = Path(state['artifact']['path'])
                assert sha256(artifact) == state['artifact']['sha256'] == source_hash
                assert len(list((root/'artifacts'/run_id).glob('*.ifc'))) == 1
                _native_valid(artifact)
            else:
                assert state['artifact'] is None
                assert not (root/'artifacts'/run_id).exists() or not list((root/'artifacts'/run_id).glob('*.ifc'))
                assert sha256(workspace/'output/other.ifc') == source_hash
                assert 'ONE_EXPLICIT_IFC_REQUIRED' in str([e for e in events if e['kind'] == 'terminal'])
            row = {'family': 'D', 'run_id': run_id, 'scenario': SCENARIOS[case],
                   'experiment_root': str(root.resolve()), 'expected_status': expected,
                   'public_source': file_ref(source), 'container_state': file_ref(control/'container.json'),
                   'native_result': file_ref(control/'result.json'), 'notifications': file_ref(control/'notifications.jsonl'),
                   'source_unchanged': True, 'native_schema_express_errors': 0, 'private_isolation_checked': True}
            if state['artifact']:
                row['artifact'] = file_ref(Path(state['artifact']['path']))
                row.update(reopen=True, native_schema_express=True,
                    native_validation={'passed': True, 'express_rules': True, 'diagnostic_count': 0,
                                       'file': row['artifact'], 'location': 'host_independent_ifcopenshell'})
            report['runs'].append(row)
            write_json(evidence, report)
        call('stop')
        service.wait(timeout=40)
        assert capture_sources('admission') == before, 'Source changed during receiver native seam.'
        assert helper_bindings == [file_ref(Path(row['path'])) for row in helper_bindings]
        report.update(commands=commands, upstream_records=file_ref(root/'runtime/dsubmission-upstream.jsonl'),
                      checks={'fenced_unique_submitted': True, 'ambiguous_declarations_rejected': True,
                              'legacy_plain_json_submitted': True, 'actual_tools_and_official_sdk_runtime': True})
        write_json(evidence, report)
        print('DSUBMISSION_NATIVE_SEAMS', str(evidence.resolve()), flush=True)
    except BaseException as error:
        report.update(error=f'{type(error).__name__}: {error}', commands=commands)
        write_json(evidence, report)
        raise
    finally:
        if service.poll() is None:
            service.terminate()
            service.wait(timeout=30)
            for name in [r['container'] for r in config['routes'].values()] + [config['relay']]:
                inspection = subprocess.run(['docker', 'inspect', name], capture_output=True, text=True)
                if inspection.returncode == 0:
                    carrier.docker('stop', '--time', '2', name)
                    if name == config['relay']:
                        carrier.docker('rm', name)
            subprocess.run(['docker', 'network', 'rm', config['network']], capture_output=True)
        service_log.close()


def seal_d_submission_evidence(evidence, suite_receipt, output):
    """Seal only after the real pytest process succeeds; preserve earlier files."""
    from scripts.ifc_repair.repair_comparison.formal_admission import validate_revision_suite, validate_revision_seams
    validate_revision_suite(suite_receipt, phase='green')
    receipt = read_json(Path(suite_receipt))
    target = 'tests/ifc_repair/repair_comparison/test_d_submission_native_seam.py'
    assert target in receipt['command']
    report = read_json(Path(evidence))
    assert 'error' not in report and len(report['runs']) == 3
    assert report['source_bindings'] == capture_sources('admission')
    assert report['images'] == carrier.bindings(report['configuration'])['images']
    assert report['real_models_called'] is False
    assert report['fixture_helpers'] == [file_ref(Path(row['path'])) for row in report['fixture_helpers']]
    assert {(r['scenario'], r['expected_status']) for r in report['runs']} == {
        ('fenced_with_prose', 'submitted'), ('duplicate_declarations', 'runtime_error'), ('bare_json', 'submitted')}
    for row in report['runs']:
        root = Path(row['experiment_root'])
        state = Ledger(root/'control.sqlite').snapshot(row['run_id'])
        assert state['status'] == row['expected_status'] and not state['activities']
        for key in ('public_source', 'container_state', 'native_result', 'notifications'):
            assert row[key] == file_ref(Path(row[key]['path']))
        container = read_json(Path(row['container_state']['path']))
        assert not container['State']['Running'] and container['State']['Pid'] == 0
        if state['artifact']:
            assert row['artifact'] == file_ref(Path(state['artifact']['path']))
        else:
            assert row['scenario'] == 'duplicate_declarations'
    report['suite_receipt'] = file_ref(Path(suite_receipt))
    validate_revision_seams(report, current_bindings=carrier.bindings(report['configuration']), families={'D'})
    assert not Path(output).exists(), 'Never overwrite prior evidence.'
    write_json(Path(output), report)
    return report
