"""Real public RepairAPI over fake HTTP; these are not model capability results."""
import importlib
import json
from pathlib import Path
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import shutil
import os
import subprocess
import uuid

import pytest

REPO = Path(__file__).resolve().parents[3]


def module():
    path = REPO / 'scripts/ifc_repair/repair_comparison/isolated_b.py'
    assert path.exists(), 'isolated B worker is not implemented'
    return importlib.import_module('scripts.ifc_repair.repair_comparison.isolated_b')


def test_bundle_contains_only_runtime_closure_and_registered_assets(tmp_path):
    m = module()
    bundle = tmp_path / 'runtime'
    inventory = m.build_runtime_bundle(REPO, bundle)
    assert 'src/text2ifc_ifc_repair/api.py' in inventory
    assert 'src/text2ifc_agent/openai_compat.py' in inventory
    assert 'prompts/agent/registry.json' in inventory
    assert 'isolated_b.py' in inventory
    assert not any(p.startswith(('dataset/', 'tests/', '.env', 'scripts/')) for p in inventory)
    assert not any('benchmark_evaluation' in p or 'repair_comparison/scoring' in p for p in inventory)
    assert m.verify_runtime_bundle(bundle) == inventory
    (bundle / 'private_gold.ifc').write_text('private', encoding='utf-8')
    with pytest.raises(ValueError, match='BUNDLE_INVENTORY'):
        m.verify_runtime_bundle(bundle)


def test_docker_contract_has_no_repo_or_secret_mount(tmp_path):
    m = module()
    bundle = tmp_path / 'runtime'
    m.build_runtime_bundle(REPO, bundle)
    workspace = tmp_path / 'work'
    workspace.mkdir()
    (workspace / 'model.ifc').write_text('test', encoding='utf-8')
    (workspace / 'task.txt').write_text('fix', encoding='utf-8')
    (workspace / 'output').mkdir()
    cfg = m.IsolatedBConfig(bundle, workspace, 'repair-b-test-state', 'repair-internal',
                            'http://host.docker.internal:8765/v1')
    command = m.IsolatedB(cfg).docker_argv()
    assert '--read-only' in command and '--cap-drop=ALL' in command
    assert '--user=65532:65532' in command and '--memory=8g' in command and '--cpus=4' in command
    assert '--security-opt=no-new-privileges' in command
    assert not any('docker.sock' in a or '.env' in a or 'api.deepseek.com' in a for a in command)
    assert not any(a == str(REPO) or f'source={REPO},' in a for a in command)
    assert not any('OPENAI_API_KEY' in a or 'DEEPSEEK_API_KEY' in a for a in command)
    mounts = [command[i+1] for i, value in enumerate(command) if value == '--mount']
    assert len(mounts) == 5
    assert sum('readonly' in a for a in mounts) == 3
    with pytest.raises(ValueError, match='GATEWAY'):
        m.IsolatedBConfig(bundle, workspace, 'repair-b-state', 'repair-internal', 'https://api.deepseek.com/v1')


def test_gateway_accepts_only_plain_or_exact_lower_hex_task_route():
    m = module()
    token = '0123456789abcdef' * 2
    base = 'http://repair-gateway:8000'
    assert m._gateway(base + '/v1') == base + '/v1'
    assert m._gateway(base + '/' + token + '/v1') == base + '/' + token + '/v1'
    assert m._gateway(base + '/' + token + '/v1/') == base + '/' + token + '/v1'
    for path in ('/' + token.upper() + '/v1', '/' + token[:-1] + '/v1',
                 '/' + token + 'a/v1', '/prefix/' + token + '/v1',
                 '/' + token + '/v1/extra', '/' + token + '//v1',
                 '/' + token + '%2fv1', '/v1//', '/v1?token=' + token,
                 '/' + token + '/v1#fragment'):
        with pytest.raises(ValueError, match='INTERNAL_GATEWAY_REQUIRED'):
            m._gateway(base + path)


def test_bundle_does_not_accept_symlinked_asset(tmp_path):
    m = module()
    root = tmp_path / 'repo'
    root.mkdir()
    outside = tmp_path / 'secret'
    outside.write_text('private', encoding='utf-8')
    link = root / 'asset.json'
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip('symlink privilege unavailable')
    with pytest.raises(ValueError, match='SYMLINK|ESCAPE'):
        m._checked_file(root, link)


@contextmanager
def fake_http(intents):
    """Only the remote HTTP response is fake; default SDK and native B are real."""
    requests = []
    from scripts.ifc_repair.repair_comparison.ours_adapter import _draft, _section

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            assert self.path == '/v1/chat/completions'
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(body)
            prompt = body['messages'][0]['content']
            if '## Immutable bindings' in prompt:
                value = _draft(prompt, _section(prompt, 'Draft schema'))
            else:
                value = intents.pop(0) if len(intents) > 1 else intents[0]
            response = {'id': 'fake-http-' + str(len(requests)), 'model': body['model'],
                        'object': 'chat.completion', 'created': 0,
                        'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {
                            'role': 'assistant', 'content': value if isinstance(value, str) else json.dumps(value),
                            'reasoning_content': 'Deterministic fixture; no model inference.'}}],
                        'usage': {'prompt_tokens': 5, 'completion_tokens': 7, 'total_tokens': 12}}
            data = json.dumps(response).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_):
            pass

    # Windows system proxy settings otherwise proxy even loopback with no
    # HTTP_PROXY environment variable. Keep the real SDK, bypass only this peer.
    old_no_proxy = os.environ.get('NO_PROXY')
    os.environ['NO_PROXY'] = '127.0.0.1,localhost'
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1', requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
        if old_no_proxy is None:
            os.environ.pop('NO_PROXY', None)
        else:
            os.environ['NO_PROXY'] = old_no_proxy


def workspace(tmp_path):
    work = tmp_path / 'workspace'
    work.mkdir()
    public = REPO / 'dataset/processed/ifc-repair/repair-comparison/development/case-002/public'
    shutil.copyfile(public / 'model.ifc', work / 'model.ifc')
    shutil.copyfile(public / 'request.txt', work / 'task.txt')
    (work / 'output').mkdir()
    return work


def door_intent(work, *, complete=True):
    import ifcopenshell
    from scripts.ifc_repair.repair_comparison.inspection import geometry_snapshot
    from scripts.ifc_repair.repair_comparison.ours_adapter import fixture_intent
    model = ifcopenshell.open(str(work / 'model.ifc'))
    opening = next(o for o in model.by_type('IfcOpeningElement') if not o.HasFillings and o.VoidsElements
                   and abs(geometry_snapshot(o)['bounds_world_m'][2][0] - 3.1) < .001)
    params = {'fit_existing_opening': True}
    if complete:
        params['door'] = {'operation_type': 'SINGLE_SWING_LEFT', 'formal_enum_explicit': True}
    return fixture_intent('door', {'allowed_ifc_classes': ['IfcOpeningElement'], 'global_id': opening.GlobalId}, params)


def invoke(tmp_path, work, url, action='start', **binding):
    return module().worker_execute({'action': action, 'run_id': 'isolated-b-test', 'base_url': url,
                                    'evidence_class': 'deterministic_fake_http', **binding},
                                   workspace=work, state_root=tmp_path / 'state')


def test_native_http_complete_keeps_source_and_only_exports_published_ifc(tmp_path):
    work = workspace(tmp_path)
    original = (work / 'model.ifc').read_bytes()
    with fake_http([door_intent(work)]) as (url, requests):
        result = invoke(tmp_path, work, url)
        assert result['result']['successful_artifact_publishable'] is True, result
        assert result['artifact_relative'] == 'output/native-result.ifc'
        assert (work / result['artifact_relative']).is_file()
        assert len(requests) == 2
        assert all(r['model'] == 'deepseek-v4-flash' and r['max_tokens'] == 65536 for r in requests)
        assert all(r['thinking'] == {'type': 'enabled'} for r in requests)
        count = len(requests)
        assert invoke(tmp_path, work, url, 'read')['artifact_relative'] == result['artifact_relative']
        with pytest.raises(FileExistsError):
            invoke(tmp_path, work, url)
        assert len(requests) == count
    assert (work / 'model.ifc').read_bytes() == original
    assert result['evidence_class'] == 'deterministic_fake_http'
    raw = list((tmp_path / 'state').rglob('live-response.json')) + list((tmp_path / 'state').rglob('live-attempt-*.json'))
    assert raw and any('reasoning_content' in p.read_text(encoding='utf-8') for p in raw)


def test_native_http_clarification_binding_survives_new_worker(tmp_path):
    work = workspace(tmp_path)
    with fake_http([door_intent(work, complete=False), door_intent(work)]) as (url, requests):
        first = invoke(tmp_path, work, url)
        question = first['result']['clarification']
        assert question and first['artifact_relative'] is None
        assert invoke(tmp_path, work, url, 'read')['result'] == first['result']
        with pytest.raises(ValueError, match='STALE'):
            invoke(tmp_path, work, url, 'answer', answer={'kind': 'cancel'}, clarification_id='stale',
                   expected_state_version=first['result']['state_version'])
        assert len(requests) == 1
        answer = {'kind': 'add_detail', 'detail': '离线测试：SINGLE_SWING_LEFT。'}
        final = invoke(tmp_path, work, url, 'answer', answer=answer,
                       clarification_id=question['clarification_id'], expected_state_version=first['result']['state_version'])
        assert final['result']['successful_artifact_publishable'], final
        assert len(requests) == 3
        with pytest.raises(ValueError, match='STALE'):
            invoke(tmp_path, work, url, 'answer', answer=answer,
                   clarification_id=question['clarification_id'], expected_state_version=first['result']['state_version'])
        assert len(requests) == 3


def test_native_http_candidate_answer_must_be_offered_and_cancel_keeps_usage(tmp_path):
    from scripts.ifc_repair.repair_comparison.ours_adapter import fixture_intent
    work = workspace(tmp_path)
    intent = fixture_intent('door', {'allowed_ifc_classes': ['IfcOpeningElement'], 'storey_name': 'Level 2'},
                            {'fit_existing_opening': True})
    with fake_http([intent]) as (url, requests):
        first = invoke(tmp_path, work, url)
        question = first['result']['clarification']
        assert question['candidates'], first
        binding = {'clarification_id': question['clarification_id'],
                   'expected_state_version': first['result']['state_version']}
        with pytest.raises(ValueError, match='NOT_OFFERED'):
            invoke(tmp_path, work, url, 'answer', answer={'kind': 'select_candidate', 'candidate_token': 'never-offered'}, **binding)
        assert invoke(tmp_path, work, url, 'read')['result'] == first['result']
        final = invoke(tmp_path, work, url, 'answer', answer={'kind': 'cancel'}, **binding)
        assert final['result']['status'] == 'cancelled' and final['artifact_relative'] is None
        assert len(requests) == 1  # no new inference, no reset or implicit retry


@pytest.mark.parametrize('mode', ['malformed', 'unsupported'])
def test_native_http_negative_results_never_export_staging(tmp_path, mode):
    work = workspace(tmp_path)
    original = (work / 'model.ifc').read_bytes()
    intent = door_intent(work)
    if mode == 'malformed':
        intent = '{truncated'
    else:
        intent['operations'] = []
        intent['unsupported_requests'] = [{'unsupported_id': 'u1', 'kind': 'unregistered_action',
                                           'operation_id': None, 'capability_id': 'unregistered_operation',
                                           'source': intent['provenance'][0]}]
    with fake_http([intent]) as (url, requests):
        result = invoke(tmp_path, work, url)
        assert result['result']['successful_artifact_publishable'] is False, result
        assert result['artifact_relative'] is None
        assert not list((work / 'output').glob('*.ifc'))
        assert requests
        assert result['result']['status'] == ('unsupported' if mode == 'unsupported' else 'provider_failed')
    assert (work / 'model.ifc').read_bytes() == original


def test_native_http_write_failure_rolls_back_without_publication(tmp_path, monkeypatch):
    import ifcopenshell
    work = workspace(tmp_path)
    before = (work / 'model.ifc').read_bytes()
    write = ifcopenshell.file.write
    injected = []

    def fail_after_candidate_write(model, path, *args, **kwargs):
        value = write(model, path, *args, **kwargs)
        if 'application-candidate.ifc-' in str(path):
            injected.append(str(path))
            raise OSError('deterministic offline write failure')
        return value

    monkeypatch.setattr(ifcopenshell.file, 'write', fail_after_candidate_write)
    with fake_http([door_intent(work)]) as (url, requests):
        result = invoke(tmp_path, work, url)
    assert injected, result
    assert result['artifact_relative'] is None
    assert result['result']['successful_artifact_publishable'] is False
    assert len(requests) == 2
    assert all(not Path(p).exists() for p in injected)
    assert (work / 'model.ifc').read_bytes() == before


# This fixture runs as a separate network peer, never in the B runtime bundle.
FAKE_SERVER_SCRIPT = r'''
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
intents=json.loads(sys.stdin.readline())
def section(prompt, title):
    return json.JSONDecoder().raw_decode(prompt.split('## '+title,1)[1].strip())[0]
def draft(prompt):
    import re
    projection=section(prompt,'Resolved operation projection')
    bindings=dict(re.findall(r'^- ([^:]+): (.+)$',prompt.split('## Immutable bindings',1)[1].split('## Resolved operation projection',1)[0],re.MULTILINE))
    raw=projection['operations']
    assert isinstance(raw,list)
    keys=('operation_id','operation_type','target','parameters','evidence_refs','appearance')
    operations=[{k:op[k] for k in keys if k in op} for op in raw]
    scope=projection.get('scope') or {'target_ids':sorted({v for op in raw for v in (op.get('scope_ids') or op['target'].values())}),'forbidden_ids':[]}
    evidence=projection.get('evidence_refs') or sorted({v for op in raw for v in op['evidence_refs']})
    return dict(schema_version=section(prompt,'Draft schema')['$id'],draft_id='fake-http-draft',base_model_fingerprint=bindings['model'],source_request_hash=bindings['source request'],semantic_manifest_ref=bindings['semantic manifest ref'],semantic_manifest_sha256=bindings['semantic manifest hash'],semantic_summary=section(prompt,'Semantic group counts'),scope=scope,evidence_refs=evidence,preconditions=[],postconditions=[],operations=operations)
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        prompt=body['messages'][0]['content']
        if '## Immutable bindings' in prompt: value=draft(prompt)
        else: value=intents.pop(0) if len(intents)>1 else intents[0]
        response={'id':'offline-only','model':body['model'],'object':'chat.completion','created':0,'choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':value if isinstance(value,str) else json.dumps(value),'reasoning_content':'Deterministic fake HTTP.'}}],'usage':{'prompt_tokens':5,'completion_tokens':7,'total_tokens':12}}
        data=json.dumps(response).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self,*args): pass
print('FAKE_READY',flush=True)
HTTPServer(('0.0.0.0',8000),Handler).serve_forever()
'''


@pytest.mark.skipif(os.environ.get('B_ISOLATED_DOCKER') != '1', reason='explicit local Docker admission run only')
def test_container_real_sdk_full_chain_and_restart_clarification(tmp_path):
    """The actual worker CLI, Linux state volume, internal network and native API."""
    m = module()
    bundle = tmp_path / 'runtime'
    m.build_runtime_bundle(REPO, bundle)
    work = workspace(tmp_path)
    before = (work / 'model.ifc').read_bytes()
    suffix = uuid.uuid4().hex[:12]
    network, peer, volume = 'repair-b-test-' + suffix, 'repair-b-fake-' + suffix, 'repair-b-state-' + suffix
    cfg = m.IsolatedBConfig(bundle, work, volume, network, 'http://repair-gateway:8000/v1',
                            container_name='repair-b-worker-' + suffix, timeout_seconds=240)
    worker = m.IsolatedB(cfg)
    subprocess.run(['docker', 'network', 'create', '--internal', network], check=True, capture_output=True)
    worker.prepare_state_volume()
    process = subprocess.Popen(['docker', 'run', '--rm', '-i', '--name', peer, '--network', network,
                                '--network-alias', 'repair-gateway', '--read-only', '--user=65532:65532',
                                '--cap-drop=ALL', '--memory=256m', '--cpus=1', '--pids-limit=32',
                                cfg.image, 'python', '-u', '-c', FAKE_SERVER_SCRIPT],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding='utf-8')
    try:
        process.stdin.write(json.dumps([door_intent(work, complete=False), door_intent(work)]) + '\n')
        process.stdin.flush()
        assert process.stdout.readline().strip() == 'FAKE_READY'
        first = worker.start('docker-b-test')
        assert first['ok'], first
        question = first['result']['clarification']
        assert question, first
        assert worker.read('docker-b-test')['result'] == first['result']
        final = worker.answer('docker-b-test', answer={'kind': 'add_detail', 'detail': 'SINGLE_SWING_LEFT'},
                              clarification_id=question['clarification_id'], expected_state_version=first['result']['state_version'])
        assert final['ok'] and final['result']['successful_artifact_publishable'], final
        assert (work / final['artifact_relative']).is_file()
        assert worker.read('docker-b-test')['result'] == final['result']
        repeated = worker.start('docker-b-test')
        assert repeated['ok'] is False
        export = worker.export_state(tmp_path / 'evidence')
        assert (export / 'task.json').is_file()
        assert list((export / 'native').rglob('state.json'))
        assert (work / 'model.ifc').read_bytes() == before
    finally:
        worker.stop()
        subprocess.run(['docker', 'kill', peer], capture_output=True, timeout=30)
        process.communicate(timeout=30)
        subprocess.run(['docker', 'network', 'rm', network], capture_output=True, timeout=30)
        # Keep the small Linux evidence volume available for diagnosing failures.
        (tmp_path / 'state-volume.txt').write_text(volume, encoding='utf-8')
