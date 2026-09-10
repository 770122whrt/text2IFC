"""Keep source, compiler/reopen and real geometry failures on distinct routes."""
import copy
import json
from pathlib import Path

import pytest

from text2ifc_agent.issue_normalizers import normalize_gate_sidecars, normalize_reopen_result, normalize_validation_issues
from text2ifc_agent.live_pipeline import run_candidate_gate_stage
from tests.agent.test_semantic_scope_and_type_policy import _write


@pytest.mark.parametrize('code', ['SEMANTIC_MATERIAL_INCOMPLETE', 'SEMANTIC_PROPERTY_INCOMPLETE',
    'SEMANTIC_SCOPE_INVALID', 'SEMANTIC_TARGET_REQUIRED', 'SEMANTIC_AUTHORITY_INCOMPLETE',
    'REQUEST_APPEARANCE_INVALID', 'REQUEST_APPEARANCE_UNSUPPORTED_FIELD'])
def test_source_extraction_failures_keep_brief_ownership_at_all_feedback_boundaries(tmp_path, code):
    detail={'code':code,'path':'/known_facts/semantic_requirements/0','message':'Invalid source value'}
    _write(tmp_path/'gate-summary.json',{'overall_status':'failed','gates':[
        {'name':'ifc_compile_reopen','status':'failed','issues':[detail]}]})
    for issue in [*normalize_validation_issues([detail],source='semantic_validation'),
                  *normalize_reopen_result({'success':False,'input_issues':[detail]}),
                  *normalize_gate_sidecars(tmp_path)]:
        assert issue.owner=='design_brief'
        assert issue.suggested_route=='revise_design_brief'
        assert code in issue.evidence


@pytest.mark.parametrize('code',['IFC_SEMANTIC_MISMATCH','IFC_SCHEMA_ERROR','IFC_EXPRESS_RULE','IFC_OUTPUT_ERROR'])
def test_native_reopen_errors_do_not_authorize_candidate_geometry_edits(tmp_path,code):
    detail={'code':code,'path':'opaque-component','message':'Requested Brick; reopened IFC contains None'}
    _write(tmp_path/'ifc-verification.json',{'success':False,'ifc_issues':[detail]})
    _write(tmp_path/'gate-summary.json',{'overall_status':'failed','gates':[
        {'name':'ifc_compile_reopen','status':'failed','issues':[detail]}]})
    issues=normalize_gate_sidecars(tmp_path)
    assert issues
    assert all(i.owner=='compiler' and i.suggested_route=='runtime_blocked' and not i.retryable for i in issues)
    assert detail['message'] in issues[0].evidence


def test_legacy_generic_compile_failure_is_not_a_geometry_repair_request(tmp_path):
    _write(tmp_path/'geometry-feedback.json',{'success':False,'issues':[
        {'code':'COMPILE_REOPEN_FAILED','path':'/output.ifc','message':'Legacy compile failure'}]})
    issues=normalize_gate_sidecars(tmp_path)
    assert issues[0].owner=='compiler' and issues[0].suggested_route=='runtime_blocked'


def test_real_geometry_error_still_allows_scoped_correction(tmp_path):
    _write(tmp_path/'geometry-feedback.json',{'success':False,'issues':[
        {'code':'WALL_BBOX_MISMATCH','entity_ids':['wall-elsewhere'],'message':'Wall is displaced'}]})
    issues=normalize_gate_sidecars(tmp_path)
    assert issues[0].owner=='generator' and issues[0].suggested_route=='regenerate_json'


@pytest.mark.parametrize('upstream',['missing','passed'])
def test_geometry_skip_claim_requires_a_real_failed_upstream_check(tmp_path,upstream):
    from text2ifc_agent.gate_audit_bundle import _geometry_gate
    _write(tmp_path/'geometry-feedback.json',{'success':False,'execution_status':'not_run',
        'blocked_by':'ifc-verification.json','issues':[]})
    if upstream=='passed':_write(tmp_path/'ifc-verification.json',{'success':True,'ifc_issues':[]})
    assert _geometry_gate(tmp_path)['status']=='failed'


def test_actual_source_gate_explains_why_geometry_was_not_evaluated(tmp_path):
    candidate=json.loads((Path(__file__).parents[1]/'contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    candidate['schema_version']='bim-json/2.1'
    for row in candidate['entities']:row['materials'],row['property_sets']=[],{}
    wall=next(row for row in candidate['entities'] if row['ifc_class']=='IfcWall')
    brief={'schema_version':'text2ifc/design-brief/2.1','known_facts':{
        'semantic_requirements':[{'entity_id':wall['id'],'material':{}}]}}
    original=copy.deepcopy(candidate)
    _write(tmp_path/'generator/candidate.json',candidate)
    _write(tmp_path/'design-brief.json',brief)
    result=run_candidate_gate_stage(case_dir=tmp_path,output_dir=tmp_path,case_id='source-grammar')
    assert not result['valid'] and not result['compile_reopen_success']
    assert result['geometry_feedback']['execution_status']=='not_run'
    assert result['geometry_feedback']['issues']==[]
    assert result['geometry_feedback']['blocked_by']=='ifc-verification.json'
    geometry=next(g for g in result['gate_summary']['gates'] if g['name']=='geometry')
    assert geometry['status']=='skipped'
    assert any(i['code']=='SEMANTIC_MATERIAL_INCOMPLETE' for i in result['ifc_verification']['input_issues'])
    assert candidate==original and not (tmp_path/'output.ifc').exists()
    assert not any(i.owner=='generator' for i in normalize_gate_sidecars(tmp_path))


def test_public_native_mismatch_stops_even_when_audit_claims_acceptance(tmp_path,monkeypatch):
    from text2ifc_compiler.compiler import CompilationResult
    from text2ifc_compiler.verification import IfcValidationIssue
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    from tests.agent.test_interactive_cli_generation import (
        PHASE6_1_COMPLETE, _write_ready_design_brief_call, _SequenceLiveProvider,
    )
    store=SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path)
    session=store.create_session(original_input='Generate the confirmed room.')
    _write_ready_design_brief_call(session.run_dir)
    store.mark_session_status(session.session_id,'ready')
    candidate=json.loads((PHASE6_1_COMPLETE/'generator/candidate.json').read_text(encoding='utf-8'))
    native_error=IfcValidationIssue(code='IFC_SEMANTIC_MISMATCH',entity='opaque-wall',
        attribute='material',message='Requested Brick; reopened IFC contains None')
    # Inject at the native compiler result seam; all later gates/routing are real.
    monkeypatch.setattr('text2ifc_agent.live_pipeline.compile_document',
        lambda *args,**kw:CompilationResult(ifc_issues=(native_error,)))
    accepted={'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
        'deterministic_gate_status':'passed','findings':[],'evidence_paths':['ifc-verification.json']}
    provider=_SequenceLiveProvider([candidate,accepted])
    try:
        result=run_ready_session_to_ifc(store=store,session=session.session_hash,provider_factory=lambda:provider)
        assert result.status=='audit_blocked' and result.ifc_path is None
        assert len(provider.session_ids)==2
        assert not list(session.run_dir.glob('changeset-round-*'))
        route=json.loads((session.run_dir/'route-decision.json').read_text(encoding='utf-8'))
        assert route['route']=='runtime_blocked' and not route['retry_allowed']
        inputs=json.loads((session.run_dir/'audit/prompt-render-input.json').read_text(encoding='utf-8'))
        assert native_error.message in json.dumps(inputs['DETERMINISTIC_GATES']['ifc_verification_feedback'])
        assert not (session.run_dir/'final-acceptance.json').exists()
    finally:store.close()
