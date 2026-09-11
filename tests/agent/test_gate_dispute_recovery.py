"""Gate/expectation problems must not authorize candidate mutation or retries."""
import json
from types import SimpleNamespace

import pytest

from text2ifc_agent.feedback_loop import plan_feedback_round
from text2ifc_agent.issue_normalizers import normalize_audit_findings, normalize_gate_sidecars
from text2ifc_agent.interactive_cli_flow import _attempt_geometry_repair_after_audit


@pytest.mark.parametrize('code,classification', [
    ('gate_dispute', None), ('GATE_DISPUTE', None),
    ('MISSING_STAIR_OPENING', 'gate_dispute'),
    ('WALL_BBOX_MISMATCH', 'gate_dispute'),
])
def test_structured_audit_dispute_stops_even_with_candidate_error(code, classification):
    finding = {'code': code, 'message': 'Evaluator applicability needs review.'}
    if classification:
        finding['classification'] = classification
    findings = [finding, {'code': 'EXPECTED_STAIR_MISSING', 'message': 'Missing stair.'}]
    for records in [findings, list(reversed(findings))]:
        issues = normalize_audit_findings({'findings': records, 'blocking': True})
        result = plan_feedback_round(source_stage='audit', issues=issues, previous_issue_count=None, current_feedback_round=0)
        assert result['route'] == 'gate_issue'
        assert result['retry_allowed'] is False
        assert result['attempted_action'] == 'stop_gate_review'
        assert result['route_decision']['final_status'] == 'blocked'


@pytest.mark.parametrize('source', ['geometry', 'summary', 'both'])
def test_incomplete_expectation_cannot_repair_candidate(tmp_path, source):
    incomplete = {'code': 'GEOMETRY_EXPECTATION_INCOMPLETE',
                  'path': '/known_facts/storeys/1/walls/interior/0',
                  'actual': {'reason': 'shared_boundary_not_unique_or_wall_thickness_missing'}}
    missing = {'code': 'MISSING_STAIR_OPENING', 'path': '/floor_openings/stair-opening'}
    if source in {'geometry', 'both'}:
        (tmp_path/'geometry-feedback.json').write_text(json.dumps({'success': False, 'issues': [missing, incomplete]}))
    if source in {'summary', 'both'}:
        (tmp_path/'gate-summary.json').write_text(json.dumps({'overall_status': 'failed', 'gates': [
            {'name': 'geometry', 'status': 'failed', 'issues': [missing, incomplete]}]}))
    issues = normalize_gate_sidecars(tmp_path)
    result = plan_feedback_round(source_stage='audit', issues=issues, previous_issue_count=None, current_feedback_round=0)
    assert result['route'] == 'gate_issue'
    assert not result['retry_allowed']
    assert any(i.owner == 'gate' and not i.retryable for i in issues)


@pytest.mark.parametrize('code', ['WALL_BBOX_MISMATCH', 'EXPECTED_STAIR_MISSING', 'MISSING_HOST'])
def test_real_candidate_errors_still_allow_bounded_repair(code):
    issues = normalize_audit_findings({'findings': [{
        'code': code, 'classification': 'candidate_geometry_issue',
        'message': 'A confirmed candidate defect, not a gate_dispute.'}], 'blocking': True})
    result = plan_feedback_round(source_stage='audit', issues=issues, previous_issue_count=None, current_feedback_round=0)
    assert result['route'] == 'regenerate_json'
    assert result['retry_allowed']


def test_informational_dispute_does_not_block_accepted_run():
    issues = normalize_audit_findings({'findings': [{
        'code': 'GATE_DISPUTE', 'severity': 'info', 'message': 'Historical resolved dispute.'}]})
    result = plan_feedback_round(source_stage='audit', issues=issues, previous_issue_count=None, current_feedback_round=0)
    assert result['route'] == 'accepted'


@pytest.mark.parametrize('route,retry', [
    ('gate_issue', False), ('ask_user', True), ('provider_retry', True),
    ('blocked_as_unsupported', False), ('regenerate_json', False),
])
def test_legacy_fallback_cannot_bypass_an_existing_stop_decision(tmp_path, route, retry):
    (tmp_path/'route-decision.json').write_text(json.dumps({'route': route, 'retry_allowed': retry}))
    (tmp_path/'audit').mkdir()
    (tmp_path/'audit/audit-report.json').write_text(json.dumps({'recommendation': 'revise', 'blocking': True}))
    (tmp_path/'geometry-feedback.json').write_text(json.dumps({'success': False, 'issues': [
        {'code': 'WALL_BBOX_MISMATCH', 'message': 'Repairable defect coexists with stop reason.'}]}))
    def forbidden_provider():
        pytest.fail('A refused recovery route must not instantiate a provider')
    assert _attempt_geometry_repair_after_audit(
        store=None, stored_session=SimpleNamespace(run_dir=tmp_path),
        provider_factory=forbidden_provider, repair_attempt_count=0) is None
