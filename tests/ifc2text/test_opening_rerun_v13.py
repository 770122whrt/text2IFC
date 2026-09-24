from scripts.ifc2text.rerun_openings_v13 import StageProvider
from text2ifc_agent.providers import resolve_provider_evidence_source


class Recorder:
    def __init__(self):
        self.calls = []

    def generate_live(self, **kwargs):
        self.calls.append(kwargs)
        return self


def test_stage_output_caps_do_not_lose_live_provider_identity():
    generator, audit = Recorder(), Recorder()
    provider = StageProvider(generator, audit)
    assert resolve_provider_evidence_source(provider) is generator
    assert provider.generate_live(state={'stage': 'generator'}, prompt='g') is generator
    assert provider.generate_live(state={'stage': 'audit'}, prompt='a') is audit
    assert len(generator.calls) == len(audit.calls) == 1


def test_stage_provider_runs_the_public_compile_audit_and_missing_material_route(tmp_path, monkeypatch):
    from tests.agent import test_interactive_cli_generation as fixtures
    from tests.agent.test_material_list_v25_route import test_public_v25_compiles_reopens_and_missing_name_fails_gate
    original = fixtures._SequenceLiveProvider
    instances = []

    def wrapped(payloads):
        sequence = original(payloads)
        instances.append(sequence)
        return StageProvider(sequence, sequence)

    monkeypatch.setattr(fixtures, '_SequenceLiveProvider', wrapped)
    test_public_v25_compiles_reopens_and_missing_name_fails_gate(tmp_path)
    assert len(instances) == 1
    assert len(instances[0].session_ids) == 2
