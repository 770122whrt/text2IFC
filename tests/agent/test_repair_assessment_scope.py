"""A routing decision is never a certificate that geometry was checked."""
import json
import pytest
from text2ifc_agent.live_pipeline import run_repair_stage
from text2ifc_agent.gate_audit_bundle import write_gate_summary, validate_gate_summary_binding
from tests.agent.test_phase6_1_live import _write_valid_generator_source
from tests.agent.test_phase6_3_gate_audit_bundle import _write_gate_case, _write_json


@pytest.mark.parametrize('feedback', [None, []])
def test_no_repair_route_reports_only_supplied_feedback(tmp_path, feedback):
    source = _write_valid_generator_source(tmp_path/'generator')
    result = run_repair_stage(provider_factory=lambda:pytest.fail('no provider needed'),
        output_dir=tmp_path/'repair', generator_source_dir=source, case_id='route-scope',
        geometry_feedback=feedback)
    assert result['route']=='no_repair_needed'
    route=json.loads((tmp_path/'repair/route.json').read_text(encoding='utf-8'))
    metrics=json.loads((tmp_path/'repair/metrics.json').read_text(encoding='utf-8'))
    assert route['schema_version']=='text2ifc/repair-route/1.1'
    assert route['assessment_scope']==metrics['assessment_scope']
    assert route['assessment_scope']['geometry_feedback_supplied'] is (feedback is not None)
    assert route['assessment_scope']['geometry_pass_certified'] is False
    assert route['assessment_scope']['geometry_issue_count_basis']=='supplied_feedback_only'


def test_supplied_unrepairable_geometry_is_recorded_and_stays_blocked(tmp_path):
    source=_write_valid_generator_source(tmp_path/'generator')
    result=run_repair_stage(provider_factory=lambda:pytest.fail('unsupported feedback cannot call provider'),
        output_dir=tmp_path/'repair',generator_source_dir=source,case_id='unrepairable',
        geometry_feedback=[{'code':'GEOMETRY_EXPECTATION_INCOMPLETE','path':'/outline'}])
    route=json.loads((tmp_path/'repair/route.json').read_text(encoding='utf-8'))
    assert result['route']=='blocked_failure'
    assert route['geometry_issue_count']==1
    assert route['assessment_scope']['geometry_feedback_supplied'] is True
    assert route['assessment_scope']['geometry_pass_certified'] is False


@pytest.mark.parametrize('route', ['no_repair_needed','repair_attempted','blocked_failure'])
def test_route_pass_is_scoped_and_cannot_override_current_geometry(tmp_path, route):
    root=_write_gate_case(tmp_path)
    _write_json(root/'repair/route.json', {'schema_version':'text2ifc/repair-route/1.0',
        'route':route,'geometry_issue_count':0})
    summary=write_gate_summary(case_dir=root,case_id='old-route-current-geometry')
    gates={g['name']:g for g in summary['gates']}
    assert 'not a geometry pass' in gates['repair_route']['basis']
    assert gates['repair_route']['status']==('blocked' if route=='blocked_failure' else 'passed')
    assert gates['geometry']['status']=='failed'
    assert summary['overall_status']!='passed'
    assert not validate_gate_summary_binding(case_dir=root,summary=summary)
    _write_json(root/'generator/candidate.json',{'changed':True})
    assert validate_gate_summary_binding(case_dir=root,summary=summary)
