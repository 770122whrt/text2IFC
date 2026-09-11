"""Bounded real-experiment runner controls, exercised with fake Providers."""
import importlib.util
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from tests.agent.test_audit_context import _inputs
from tests.agent.test_design_review_audit import _audit, _context
from tests.agent.test_phase6_1_live import _RecordingLiveProvider, _write_auditable_case_dir
from text2ifc_agent.openai_compat import OpenAICompatError


def module():
    path = Path('dataset/processed/experiments/audit-token-pair-20260911/run_pair.py')
    spec = importlib.util.spec_from_file_location('audit_token_pair', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def setup(tmp_path):
    m = module()
    case = _write_auditable_case_dir(tmp_path / 'source')
    data = _inputs(review=True)
    data['DESIGN_REVIEW_CONTEXT'] = _context(case)
    data['EVIDENCE_PATHS'].append('design-review-context.json')
    path = tmp_path / 'frozen-input.json'
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    protocol = {'input_path': str(path), 'input_sha256': m.sha(path), 'case_dir': str(case),
                'order': ['full', 'deduplicated'],
                'limits': {'max_calls': 2, 'max_tokens': 500000, 'max_active_seconds': 900},
                'max_output_tokens': 65536}
    return m, protocol


def test_pair_records_actual_usage_and_never_changes_source(tmp_path):
    m, protocol = setup(tmp_path)
    result = m.execute(tmp_path/'live', protocol, lambda _: _RecordingLiveProvider(_audit()), evidence_class='fake')
    assert result['status'] == 'completed'
    assert len(result['arms']) == 2 and all(row['valid'] for row in result['arms'])
    assert result['budget_after']['calls_used'] == 2
    assert result['budget_after']['tokens_used_or_reserved'] == 600
    assert m.sha(Path(protocol['input_path'])) == protocol['input_sha256']
    for row in result['arms']:
        assert row['usage'] == {'input_tokens': 100, 'output_tokens': 200}
        assert (tmp_path/'live'/row['mode']/'response.raw.json').is_file()


@pytest.mark.parametrize('failure', ['truncated', 'missing_usage'])
def test_failure_is_preserved_stops_pair_and_keeps_conservative_budget(tmp_path, failure):
    m, protocol = setup(tmp_path)
    class Broken:
        def generate_live(self, **kwargs):
            details = {'failure_class': 'truncated', 'response': {'id': 'failed'}, 'content_text': '{'}
            if failure == 'truncated':
                details['usage'] = {'prompt_tokens': 321, 'completion_tokens': 400}
            raise OpenAICompatError('fixture', evidence=details)
    result = m.execute(tmp_path/'live', protocol, lambda _: Broken(), evidence_class='fake')
    assert result['status'] == 'stopped'
    assert result['budget_after']['calls_used'] == 1
    charged = result['budget_after']['tokens_used_or_reserved']
    assert charged == 721 if failure == 'truncated' else charged > 65536
    assert (tmp_path/'live/full/provider-error.json').is_file()
    assert json.loads((tmp_path/'live/full/response.raw.json').read_text())['id'] == 'failed'


@pytest.mark.parametrize('failure', ['tampered', 'existing_output'])
def test_preconditions_stop_before_provider_creation(tmp_path, failure):
    m, protocol = setup(tmp_path)
    output = tmp_path/'live'
    if failure == 'tampered':
        Path(protocol['input_path']).write_text('{}', encoding='utf-8')
    else:
        output.mkdir()
    def forbidden(_):
        raise AssertionError('Provider must not be created')
    with pytest.raises((ValueError, FileExistsError)):
        m.execute(output, protocol, forbidden, evidence_class='fake')


def test_false_resolved_claim_is_invalid_and_does_not_trigger_more_calls(tmp_path):
    m, protocol = setup(tmp_path)
    result = m.execute(tmp_path/'live', protocol, lambda _: _RecordingLiveProvider(_audit('resolved')), evidence_class='fake')
    assert result['status'] == 'stopped'
    assert result['budget_after']['calls_used'] == 1
    assert not result['arms'][0]['valid']
