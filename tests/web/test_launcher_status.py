"""The operator's config command diagnoses settings without starting or stopping services."""
import importlib.util
import json
from pathlib import Path


def test_config_command_uses_redacted_status_without_contacting_service(monkeypatch, capsys):
    from text2ifc_web import live_runtime
    path = Path(__file__).resolve().parents[2] / 'ui/ifc-viewer/api_launcher.py'
    spec = importlib.util.spec_from_file_location('ui_api_launcher_status_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    status = {'configured': False, 'provider_key': 'deepseek', 'model': None,
              'missing': ['DEEPSEEK_API_KEY', 'OPENAI_BASE_URL', 'TEXT2IFC_DEEPSEEK_MODEL'],
              'api_key_configured': False, 'base_url_configured': False}
    monkeypatch.setattr(live_runtime, 'provider_configuration_status', lambda root: status)

    def forbidden():
        raise AssertionError('Config diagnosis must not contact, launch, or restart a service')

    monkeypatch.setattr(module, 'health', forbidden)
    module.main('config-status')
    assert json.loads(capsys.readouterr().out) == status


def test_configured_loopback_ports_allow_ui_posts_without_widening_origins(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from text2ifc_web import live_runtime
    import uvicorn

    monkeypatch.setenv('IFC_VIEWER_PORT', '4278')
    monkeypatch.setenv('TEXT2IFC_API_PORT', '4280')
    path = Path(__file__).resolve().parents[2] / 'ui/ifc-viewer/api_launcher.py'
    spec = importlib.util.spec_from_file_location('ui_api_launcher_ports_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.RUNTIME = tmp_path / 'runtime'
    monkeypatch.setattr(live_runtime, 'local_live_factory', lambda root: (None, {'mode': 'prepare_only'}))
    captured = {}
    monkeypatch.setattr(uvicorn, 'run', lambda app, **kwargs: captured.update(app=app))
    module.main('serve')

    with TestClient(captured['app'], base_url='http://127.0.0.1:4280') as client:
        for host in ('127.0.0.1', 'localhost'):
            for port in (4278, 4280):
                response = client.post('/api/repair-requests/prepare', json={}, headers={'Origin': f'http://{host}:{port}'})
                assert response.status_code == 422, response.text
        for origin in ('http://127.0.0.1:5278', 'http://example.invalid:4278', 'null'):
            response = client.post('/api/repair-requests/prepare', json={}, headers={'Origin': origin})
            assert response.status_code == 403
            assert response.json()['error']['code'] == 'ORIGIN_NOT_ALLOWED'
