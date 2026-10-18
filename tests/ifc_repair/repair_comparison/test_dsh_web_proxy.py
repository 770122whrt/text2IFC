"""Public-page proxy, opt-in SDK environment and frozen batch configuration."""
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import threading

import pytest


def test_public_proxy_rejects_nonpublic_dns_and_pins_public_addresses(monkeypatch):
    from scripts.ifc_repair.repair_comparison.dsh import web_proxy
    def addresses(*ips):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, 443)) for ip in ips]
    monkeypatch.setattr(web_proxy.socket, 'getaddrinfo', lambda *a, **k: addresses('1.1.1.1'))
    assert web_proxy.public_addresses('example.invalid', 443) == [(socket.AF_INET, ('1.1.1.1', 443))]
    for ips in [('127.0.0.1',), ('192.168.1.5',), ('169.254.169.254',), ('1.1.1.1', '10.0.0.5')]:
        monkeypatch.setattr(web_proxy.socket, 'getaddrinfo', lambda *a, ips=ips, **k: addresses(*ips))
        with pytest.raises(ValueError, match='PUBLIC'):
            web_proxy.public_addresses('example.invalid', 443)


@pytest.mark.parametrize('target', ['http://user:secret@example.invalid/', 'file:///tmp/page',
    'http://example.invalid:8000/', '/local-page', 'http://127.0.0.1/', 'http://example.invalid/#part'])
def test_public_proxy_rejects_unoffered_urls(target):
    from scripts.ifc_repair.repair_comparison.dsh.web_proxy import http_target
    with pytest.raises(ValueError):
        http_target(target)


def test_proxy_forwards_real_http_bytes_without_client_credentials(monkeypatch):
    from scripts.ifc_repair.repair_comparison.dsh import web_proxy
    seen = []
    class Origin(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, dict(self.headers)))
            body = b'<html><h1>OFFLINE_PUBLIC_PAGE_BODY</h1></html>'
            self.send_response(200); self.send_header('Content-Length', str(len(body)))
            self.end_headers(); self.wfile.write(body)
        def log_message(self, *args):
            pass
    class Proxy(web_proxy.WebProxyMixin, BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
    origin = ThreadingHTTPServer(('127.0.0.1', 0), Origin)
    proxy = ThreadingHTTPServer(('127.0.0.1', 0), Proxy)
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (origin, proxy)]
    for thread in threads: thread.start()
    monkeypatch.setenv('REPAIR_WEB_PROXY', '1')
    # Fake only origin transport; the proxy's parsing and streaming are real.
    monkeypatch.setattr(web_proxy, 'open_public_socket', lambda host, port: socket.create_connection(origin.server_address, timeout=5))
    client = http.client.HTTPConnection(*proxy.server_address, timeout=5)
    try:
        client.request('GET', 'http://example.invalid/page?x=1', headers={
            'Authorization': 'must-not-forward', 'Proxy-Authorization': 'must-not-forward',
            'Cookie': 'must-not-forward', 'User-Agent': 'offline-test'})
        response = client.getresponse()
        assert response.status == 200 and b'OFFLINE_PUBLIC_PAGE_BODY' in response.read()
        assert seen[0][0] == '/page?x=1'
        assert seen[0][1]['Host'] == 'example.invalid'
        assert not {'Authorization', 'Proxy-Authorization', 'Cookie'} & set(seen[0][1])
    finally:
        client.close()
        for server in (proxy, origin): server.shutdown(); server.server_close()
        for thread in threads: thread.join(timeout=5)


def test_proxy_is_disabled_without_explicit_opt_in(monkeypatch):
    from scripts.ifc_repair.repair_comparison.dsh.web_proxy import WebProxyMixin
    monkeypatch.delenv('REPAIR_WEB_PROXY', raising=False)
    for method, path in [('do_GET', 'http://example.invalid/'), ('do_CONNECT', 'example.invalid:443')]:
        handler = object.__new__(WebProxyMixin)
        handler.path = path; statuses = []
        handler.send_error = statuses.append
        getattr(handler, method)()
        assert statuses == [403]


def test_https_connect_relays_opaque_bytes_and_closes(monkeypatch):
    import io
    from scripts.ifc_repair.repair_comparison.dsh import web_proxy
    monkeypatch.setenv('REPAIR_WEB_PROXY', '1')
    client, incoming = socket.socketpair()
    upstream, origin = socket.socketpair()
    monkeypatch.setattr(web_proxy, 'open_public_socket', lambda host, port: upstream)
    handler = object.__new__(web_proxy.WebProxyMixin)
    handler.path = 'example.invalid:443'; handler.connection = incoming
    handler.wfile = io.BytesIO(); statuses = []
    handler.send_response = lambda status, *args: statuses.append(status)
    handler.end_headers = lambda: None
    thread = threading.Thread(target=handler.do_CONNECT, daemon=True)
    thread.start()
    try:
        client.settimeout(5); origin.settimeout(5)
        client.sendall(b'opaque-client-bytes')
        assert origin.recv(100) == b'opaque-client-bytes'
        origin.sendall(b'opaque-server-bytes')
        assert client.recv(100) == b'opaque-server-bytes'
    finally:
        client.close(); origin.close(); thread.join(timeout=5); incoming.close()
    assert not thread.is_alive() and statuses == [200] and handler.close_connection


@pytest.mark.parametrize('path, error, expected', [
    ('example.invalid:22', None, 403), ('user:secret@example.invalid:443', None, 403),
    ('localhost:443', ValueError('PUBLIC_DESTINATION_REQUIRED'), 403),
    ('example.invalid:443', OSError('DNS_FAILED'), 502),
])
def test_connect_rejects_bad_authority_and_failed_upstream(monkeypatch, path, error, expected):
    from scripts.ifc_repair.repair_comparison.dsh import web_proxy
    monkeypatch.setenv('REPAIR_WEB_PROXY', '1')
    def open_socket(*args):
        raise error or AssertionError('invalid authority reached upstream')
    monkeypatch.setattr(web_proxy, 'open_public_socket', open_socket)
    handler = object.__new__(web_proxy.WebProxyMixin); handler.path = path
    statuses = []; handler.send_error = statuses.append
    handler.do_CONNECT()
    assert statuses == [expected]


def test_sdk_proxy_is_opt_in_and_model_gateway_stays_direct(tmp_path):
    from scripts.ifc_repair.repair_comparison.dsh.native_worker import runtime_environment
    from scripts.ifc_repair.repair_comparison.isolated_dsh import NativeDSH
    args = dict(name='proxy-unit', state_volume='proxy-unit-state', network='proxy-internal',
        base_url='http://repair-gateway:8000/'+'a'*32, model='deepseek-v4-flash', session_id='proxy-unit')
    config = {'base_url': args['base_url']}
    assert 'HTTPS_PROXY' not in runtime_environment(config)
    environment = runtime_environment({**config, 'web_access': 'proxy'})
    assert environment['HTTPS_PROXY'] == environment['HTTP_PROXY'] == 'http://repair-gateway:8000'
    assert environment['NO_PROXY'] == 'repair-gateway,localhost,127.0.0.1'
    work = tmp_path/'work'; work.mkdir()
    native = NativeDSH(work, tmp_path/'control', **args, web_access='proxy')
    assert json.loads((native.control/'runtime.json').read_text())['web_access'] == 'proxy'
    assert not any('api_key' in arg or '.env' in arg for arg in native.docker_argv())
    with pytest.raises(ValueError, match='WEB_ACCESS'):
        NativeDSH(work, tmp_path/'bad', **args, web_access='unknown')


def test_batch_web_access_is_frozen_and_cannot_drift(tmp_path):
    from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
    from scripts.ifc_repair.repair_comparison.budget import fixed_budget_profile
    args = dict(cases_root=tmp_path, case_ids=['example'],
        budgets={'example': fixed_budget_profile('S1')}, stage=carrier.FORMAL_STAGE)
    assert 'd_web_access' not in carrier.batch_configuration(**args)
    configuration = carrier.batch_configuration(**args, d_web_access='proxy')
    persisted = {'mode': 'offline', **configuration, 'configuration': configuration,
                 'routes': {name: {} for name in configuration['order']}}
    assert carrier.validate_configuration(persisted) == configuration
    persisted.pop('d_web_access')
    with pytest.raises(ValueError, match='CONFIGURATION_CHANGED'):
        carrier.validate_configuration(persisted)
    with pytest.raises(ValueError, match='WEB_ACCESS'):
        carrier.batch_configuration(**args, d_web_access=True)


def test_qa_matches_network_admission_before_any_credentials(tmp_path, monkeypatch):
    from scripts.ifc_repair.repair_comparison.dsh import qa as subject
    assert 'web_fetch and shell networking are unavailable' in subject.qa_question(None)
    assert 'Read relevant official pages with web_fetch' in subject.qa_question('proxy')
    monkeypatch.setattr(subject, 'verify_qa_admission', lambda path: {'web_access': None})
    with pytest.raises(ValueError, match='WEB_ACCESS_ADMISSION'):
        subject.qa(tmp_path/'live', mode='live', admission=tmp_path/'receipt.json', web_access='proxy')
    assert not (tmp_path/'live').exists()
