"""Official DSH web_search/runtime/relay; only remote HTTP responses are fake."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import httpx
import pytest

from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.contracts import read_json, sha256, write_json
from scripts.ifc_repair.repair_comparison.formal_admission import capture_sources, file_ref
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from tests.ifc_repair.repair_comparison.dsh_fake_gateway import chunks
from tests.ifc_repair.repair_comparison.test_batch_workflow import _formal_public_inputs

FIXTURE_URL = 'https://example.invalid/ifc-search-fixture'


class SearchTransport:
    def __init__(self, root, config):
        self.root, self.step = Path(root), 0

    def __call__(self, request):
        body = json.loads(request.content)
        if request.url.path.endswith('/search/messages'):
            assert body['tools'][0]['type'] == 'web_search_20250305'
            value = {'id': 'offline-search', 'type': 'message', 'role': 'assistant',
                'model': body['model'], 'stop_reason': 'end_turn', 'content': [
                    {'type': 'web_search_tool_result', 'tool_use_id': 'server-search',
                     'content': [{'type': 'web_search_result', 'url': FIXTURE_URL,
                                  'title': 'Synthetic search transport result'}]}],
                'usage': {'input_tokens': 7, 'cache_read_input_tokens': 3, 'output_tokens': 2}}
            result = httpx.Response(200, json=value)
        else:
            if self.step == 0:
                events = chunks(tool=('web_search', {'queries': ['buildingSMART IFC documentation']}, 'native-web-search'))
            elif self.step == 1:
                assert FIXTURE_URL in json.dumps(body)
                command = "python - <<'FIXTURE'\nfrom pathlib import Path\nimport shutil,ifcopenshell\nassert not Path('private').exists()\nifcopenshell.open('model.ifc')\nPath('output').mkdir(exist_ok=True)\nshutil.copyfile('model.ifc','output/repaired.ifc')\nprint('PUBLIC_COPY_OK')\nFIXTURE"
                events = chunks(tool=('bash', {'command': command, 'description': 'Offline public submission copy',
                    'timeoutMs': 120000}, 'native-copy'))
            else:
                assert self.step == 2 and 'PUBLIC_COPY_OK' in json.dumps(body)
                events = chunks(text='{"submitted_ifc":"output/repaired.ifc"}')
            self.step += 1
            result = httpx.Response(200, headers={'Content-Type': 'text/event-stream'}, content=''.join(
                'event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n' for e in events).encode())
        path = self.root/'runtime/search-upstream.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf8') as handle:
            handle.write(json.dumps({'url': str(request.url), 'request': body,
                'response': result.text, 'evidence_class': 'deterministic_fake_http'})+'\n')
        return result


def search_fixture_cli():
    from tests.ifc_repair.repair_comparison import test_batch_workflow as base
    base._FormalHTTPTransport = SearchTransport
    base._formal_fixture_cli()


class QATransport:
    """Fake only external HTTP; the SDK/runtime and native search remain real."""
    def __init__(self, fetch=False):
        self.step, self.fetch = 0, fetch
        self.url = 'http://example.invalid/qa-source' if fetch else FIXTURE_URL

    def __call__(self, request):
        body = json.loads(request.content)
        if body.get('tools', [{}])[0].get('type') == 'web_search_20250305':
            assert body['tools'][0]['type'] == 'web_search_20250305'
            return httpx.Response(200, json={'id': 'offline-qa-search', 'type': 'message',
                'role': 'assistant', 'model': body['model'], 'stop_reason': 'end_turn',
                'content': [{'type': 'web_search_tool_result', 'tool_use_id': 'qa-search',
                    'content': [{'type': 'web_search_result', 'url': self.url,
                        'title': 'Synthetic QA source, no live model'}]}],
                'usage': {'input_tokens': 7, 'cache_read_input_tokens': 3, 'output_tokens': 2}})
        text = json.dumps(body, ensure_ascii=False)
        assert 'submitted_ifc' not in text and 'As of' in text
        if self.step == 0:
            events = chunks(tool=('web_search', {'queries': ['offline model release fixture']}, 'qa-search'))
        elif self.step == 1 and self.fetch:
            assert self.url in text
            events = chunks(tool=('web_fetch', {'url': self.url}, 'qa-fetch'))
        else:
            assert self.step == (2 if self.fetch else 1) and self.url in text
            if self.fetch: assert 'OFFLINE-PAGE-BODY' in text
            events = chunks(text='OFFLINE_FINAL_ANSWER: synthetic model released on 2000-01-01. Source: '+self.url)
        self.step += 1
        return httpx.Response(200, headers={'Content-Type': 'text/event-stream'}, content=''.join(
            'event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n' for e in events).encode())


def qa_fixture_cli():
    from scripts.ifc_repair.repair_comparison.dsh import qa as subject
    original = subject.WireGateway
    fetch = '--web-access' in sys.argv
    fake = QATransport(fetch)
    subject.WireGateway = lambda *args, **kwargs: original(
        *args, **kwargs, transport=httpx.MockTransport(fake))
    if not fetch:
        raise SystemExit(subject.main())
    # Fake the proxy's remote origin connection only. Keep the production SDK
    # proxy environment, relay, native tool and HTML conversion unchanged.
    root = Path(sys.argv[sys.argv.index('--root')+1])
    fixture = root.parent/'page-origin-transport.py'
    proxy_source = carrier.REPO/'scripts/ifc_repair/repair_comparison/dsh/web_proxy.py'
    origin = '''
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
class _FakeOrigin(BaseHTTPRequestHandler):
    def do_GET(self):
        assert self.path == '/qa-source'
        body = b'<html><h1>OFFLINE-PAGE-BODY</h1><p>Synthetic release date: 2000-01-01.</p></html>'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self, *args): pass
_origin = ThreadingHTTPServer(('127.0.0.1', 0), _FakeOrigin)
threading.Thread(target=_origin.serve_forever, daemon=True).start()
def open_public_socket(host, port):
    assert host == 'example.invalid' and port == 80
    return socket.create_connection(_origin.server_address, timeout=5)
'''
    fixture.write_text(proxy_source.read_text(encoding='utf8')+origin, encoding='utf8')
    actual_docker = subject.carrier.docker
    def docker_with_fake_origin(*args, **kwargs):
        if args[0] == 'create' and '--env=REPAIR_WEB_PROXY=1' in args:
            args = tuple('type=bind,source='+str(fixture.resolve())+',target=/opt/web_proxy.py,readonly'
                if isinstance(arg, str) and 'target=/opt/web_proxy.py,' in arg else arg for arg in args)
        return actual_docker(*args, **kwargs)
    subject.carrier.docker = docker_with_fake_origin
    raise SystemExit(subject.main())


@pytest.mark.skipif(os.environ.get('REPAIR_FORMAL_DOCKER') != '1', reason='explicit keyless native DSH full Q&A validation')
@pytest.mark.parametrize('web_access', [None, 'proxy'])
def test_native_qa_returns_final_answer_after_consuming_search(tmp_path, web_access):
    root = tmp_path/'full-qa'
    argv = [sys.executable, '-c', 'from tests.ifc_repair.repair_comparison.test_dsh_search_native_seam import qa_fixture_cli; qa_fixture_cli()',
        'qa', '--mode', 'offline', '--root', str(root)]
    if web_access: argv += ['--web-access', web_access]
    result = subprocess.run(argv, cwd=carrier.REPO, capture_output=True, text=True, encoding='utf8', timeout=360)
    (tmp_path/'public-cli.log').write_text(result.stdout+'\n'+result.stderr, encoding='utf8')
    assert result.returncode == 0, (result.stdout[-1600:], result.stderr[-1600:])
    report = read_json(root/'result.json')
    assert report['status'] == 'completed' and report['answer'].startswith('OFFLINE_FINAL_ANSWER')
    assert report['root_requests'] == (3 if web_access else 2) and report['search_requests'] == 1
    if web_access:
        assert report['pages'][0]['ok'] and 'OFFLINE-PAGE-BODY' in report['pages'][0]['excerpt']
    assert report['search_results_consumed'] and report['container_stopped']
    assert report['private_material_not_mounted'] and report['public_question_unchanged']
    assert report['source_bindings_unchanged'] and report['usage']['unknown_calls'] == 0
    assert report['usage']['known_total_tokens'] == (66 if web_access else 48)
    state = Ledger(root/'control.sqlite').snapshot('dsh-full-qa-D')
    assert not state['activities'] and state['status'] == 'no_output' and state['artifact'] is None
    control = read_json(root/'runtime/container.json')
    assert not control['State']['Running'] and control['State']['Pid'] == 0
    assert control['Image'] == report['image_id']
    versions = read_json(root/'runtime/versions.json')
    assert versions['deepseek-harness-sdk'] == versions['deepseek-harness-runtime-bin'] == '0.2.0rc1'
    assert set(p.name for p in (root/'workspace').iterdir()) == {'task.txt'}
    print('DSH_QA_NATIVE_REPORT', str((root/'result.json').resolve()), flush=True)


@pytest.mark.skipif(os.environ.get('REPAIR_FORMAL_DOCKER') != '1', reason='explicit keyless native DSH search validation')
def test_native_search_shares_task_budget_and_keeps_credentials_on_host(tmp_path):
    sources = capture_sources('admission')
    expected_image = carrier.docker('image','inspect',carrier.DSH_IMAGE,'--format','{{.Id}}')
    cases, _, _ = _formal_public_inputs(tmp_path/'authored')
    case = cases/'native-search/public'
    shutil.copytree(cases/'synthetic-001/public', case)
    budgets = tmp_path/'budgets.json'
    write_json(budgets, {'native-search': {'tokens': 1500000, 'calls': 8,
        'active_seconds': 300, 'tool_seconds': 120, 'extensions': []}})
    root = tmp_path/'experiment'
    argv = [sys.executable, '-c', 'from tests.ifc_repair.repair_comparison.test_dsh_search_native_seam import search_fixture_cli; search_fixture_cli()']
    commands = []
    def call(action, *extra, timeout=400):
        result = subprocess.run([*argv, action, '--root', str(root), *map(str, extra)],
            cwd=carrier.REPO, capture_output=True, text=True, encoding='utf8', timeout=timeout)
        log = tmp_path/f'{len(commands):02d}-{action}.log'
        log.write_text(result.stdout+'\n'+result.stderr, encoding='utf8')
        commands.append({'action': action, 'exit_code': result.returncode, 'log': file_ref(log)})
        assert result.returncode == 0, (action, result.stdout[-1600:], result.stderr[-1600:])
        return json.loads(result.stdout)
    config = call('init', '--mode', 'offline', '--cases-root', cases,
        '--case-ids', 'native-search', '--budgets', budgets, '--stage', carrier.FORMAL_STAGE, '--d-web-search')
    log_handle = (tmp_path/'service.log').open('wb')
    service = subprocess.Popen([*argv, 'serve', '--root', str(root)], cwd=carrier.REPO,
        stdout=log_handle, stderr=subprocess.STDOUT)
    report = {'schema_version': 'repair-comparison-d-search-native-seam/0.1',
              'real_models_called': False, 'source_bindings': sources, 'checks': {}, 'commands': commands}
    evidence = tmp_path/'search-native-seam.json'
    try:
        deadline = time.monotonic()+90
        while not (root/'service.json').exists() or read_json(root/'service.json').get('state') != 'running':
            assert service.poll() is None and time.monotonic() < deadline, 'Native fake service startup failed'
            time.sleep(.3)
        state = call('run', '--run-id', 'native-search-D')
        assert state['status'] == 'submitted' and not state['activities'], state
        assert state['usage']['calls'] == 4 and state['usage']['unknown_calls'] == 0
        ledger = Ledger(root/'control.sqlite')
        search_calls = [c for c in ledger.calls('native-search-D') if c['metadata']['stage'] == 'web_search']
        assert len(search_calls) == 1 and not search_calls[0]['failed']
        assert all(c['state'] == 'completed' for c in ledger.calls('native-search-D'))
        control = root/'runtime/native-search-D'
        container = read_json(control/'container.json')
        assert not container['State']['Running'] and container['State']['Pid'] == 0
        assert container['Image'] == expected_image
        versions = read_json(control/'versions.json')
        assert versions['deepseek-harness-sdk'] == '0.2.0rc1'
        assert versions['deepseek-harness-runtime-bin'] == '0.2.0rc1'
        assert versions['ifcopenshell'] == '0.8.5'
        runtime = read_json(control/'runtime.json')
        assert 'api_key' not in runtime.get('web_search', {})
        assert FIXTURE_URL in (root/'runtime/search-upstream.jsonl').read_text(encoding='utf8')
        source = case/'model.ifc'
        assert sha256(Path(state['artifact']['path'])) == sha256(source)
        assert sha256(root/'workspaces/native-search-D/model.ifc') == sha256(source)
        call('stop')
        service.wait(timeout=40)
        assert capture_sources('admission') == sources
        report.update(configuration=config['configuration'], run_id=state['run_id'],
            checks={'native_web_search': True, 'structured_result_consumed': True,
                'shared_task_budget': True, 'private_material_not_mounted': True,
                'container_stopped': True, 'public_source_unchanged': True,
                'fixed_runtime_versions': True, 'image_binding': True},
            container=file_ref(control/'container.json'), native_result=file_ref(control/'result.json'),
            runtime_versions=file_ref(control/'versions.json'), image_id=expected_image,
            upstream_records=file_ref(root/'runtime/search-upstream.jsonl'),
            usage=state['usage'], experiment_root=str(root.resolve()))
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        write_json(evidence, report)
        if service.poll() is None:
            call('stop')
            service.wait(timeout=45)
        log_handle.close()
    print('DSH_SEARCH_NATIVE_SEAM', str(evidence.resolve()), flush=True)
