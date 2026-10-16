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
