"""A false aggregate flag must be accompanied by its failed dynamic invariant."""
import pytest

from tests.agent.test_phase6_3_gate_audit_bundle import _write_gate_case, _write_ready_design_brief_call, _write_json
from text2ifc_agent.live_pipeline import run_audit_report_stage


def test_real_rendered_audit_prompt_contains_failed_dynamic_gate_and_issue(tmp_path):
    root = _write_gate_case(tmp_path)
    _write_ready_design_brief_call(root)
    _write_json(root/'generator/metrics.json', {})
    _write_json(root/'repair/metrics.json', {})
    _write_json(root/'semantic-coverage.json', {'valid': True, 'blocking_facts': []})
    _write_json(root/'geometry-feedback.json', {'success': True, 'issues': [], 'metrics': {}})

    class InspectPrompt:
        def generate_live(self, *, prompt, **kwargs):
            assert 'dynamic_entity_completeness' in prompt
            assert 'EXPECTED_ENTITY_MISSING' in prompt
            raise RuntimeError('captured_before_transport')

    with pytest.raises(RuntimeError, match='captured_before_transport'):
        run_audit_report_stage(provider=InspectPrompt(), case_dir=root, case_id='dynamic-failure')
