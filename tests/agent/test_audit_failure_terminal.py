"""Audit transport failures must close public sessions without another model call."""
import json

import pytest

from text2ifc_agent.candidate_index import build_candidate_index
from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
from text2ifc_agent.providers import ProviderOutputError
from text2ifc_agent.session_store import SessionStore
from tests.agent.test_interactive_cli_generation import (
    PHASE6_1_COMPLETE, _SequenceLiveProvider, _write_ready_design_brief_call, _geometry_blocked_candidate,
)


@pytest.mark.parametrize('strategy',['legacy_full','staged'])
@pytest.mark.parametrize('round_number',[1,2])
@pytest.mark.parametrize('failure',['input_token_budget_exceeded','truncated_output'])
def test_audit_failure_closes_session_and_preserves_failed_attempt(tmp_path,monkeypatch,strategy,round_number,failure):
    store=SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path)
    session=store.create_session(original_input='Generate the specified rectangular room.')
    _write_ready_design_brief_call(session.run_dir)
    store.mark_session_status(session.session_id,'ready')
    good=json.loads((PHASE6_1_COMPLETE/'generator/candidate.json').read_text(encoding='utf-8'))
    candidate=_geometry_blocked_candidate(good) if round_number==2 else good
    if strategy=='staged':
        # Initial package authoring seam only; actual gates, Audit and persistence run.
        monkeypatch.setattr('text2ifc_agent.interactive_cli_flow.run_staged_generation',lambda **kw:{
            'valid':True,'candidate':candidate,'package_count':1,'provider_call_count':0,
            'status':'formal','package_records':[], 'revision':{'revision_id':'revision-00','sequence':0,
                'candidate_hash':build_candidate_index(candidate)['candidate_hash']}})
    def apply(**kw):
        return {'valid':True,'status':'applied','candidate':good,
            'revision':{'revision_id':'revision-01','sequence':1,'candidate_hash':build_candidate_index(good)['candidate_hash']},
            'preservation':{'unrelated_component_preservation_rate':1.0,'forbidden_drift_ids':[]},
            'issues':[],'scope':{'scope_id':'scope-revision-01'},
            'stage':{'status':'changeset','classification':'changeset','response_id':'offline-patch'}}
    monkeypatch.setattr('text2ifc_agent.interactive_cli_flow.run_scoped_changeset_round',apply)
    revise={'schema_version':'text2ifc/audit/2.0','recommendation':'revise','blocking':True,
        'deterministic_gate_status':'failed','findings':[{'code':'GEOMETRY_TRUE_POSITIVE',
        'message':'Wall geometry needs correction','evidence_path':'geometry-feedback.json'}],
        'evidence_paths':['geometry-feedback.json']}
    prior={}
    class FailingAudit:
        def __init__(self):self.calls=[]
        def generate_live(self,**kw):
            self.calls.append(kw)
            if kw['state']['stage']=='audit' and kw['session_id'].endswith(f'audit-{round_number:02d}'):
                archive=session.run_dir/'evaluation-rounds/round-01'
                prior.update({p.relative_to(archive):p.read_bytes() for p in archive.rglob('*') if p.is_file()})
                error=ProviderOutputError('offline injected Audit failure',details={
                    'provider':'offline','failure_class':failure,'transport_attempted':failure!='input_token_budget_exceeded'})
                if failure=='truncated_output':
                    error.live_result=_SequenceLiveProvider([{'partial':'received'}]).generate_live(**kw)
                raise error
            return _SequenceLiveProvider([candidate if kw['state']['stage']=='generate' else revise]).generate_live(**kw)
    provider=FailingAudit()
    try:
        result=run_ready_session_to_ifc(store=store,session=session.session_hash,
            provider_factory=lambda:provider,generation_strategy=strategy)
        assert result.status=='provider_failed' and result.ifc_path is None
        assert store.get_session(session.session_hash).status=='provider_failed'
        assert len(provider.calls)==(1 if strategy=='legacy_full' else 0)+round_number
        assert not (session.run_dir/'final-acceptance.json').exists()
        failure_dir=session.run_dir/'audit-failures'/f'attempt-{round_number:02d}'
        payload=json.loads((failure_dir/'provider-error.json').read_text(encoding='utf-8'))
        assert payload['failure_class']==failure
        assert (failure_dir/'response.raw.json').exists()==(failure=='truncated_output')
        assert not (failure_dir/'audit-report.json').exists()
        rendered=json.loads((failure_dir/'prompt-render-input.json').read_text(encoding='utf-8'))
        assert 'ifc_verification_feedback' in rendered['DETERMINISTIC_GATES']
        assert (session.run_dir/'issues.json').is_file()
        assert (session.run_dir/'route-decision.json').is_file()
        if prior:
            archive=session.run_dir/'evaluation-rounds/round-01'
            assert prior=={p.relative_to(archive):p.read_bytes() for p in archive.rglob('*') if p.is_file()}
        if failure=='input_token_budget_exceeded' and round_number==2 and strategy=='staged':
            from text2ifc_agent.live_pipeline import run_audit_report_stage
            saved={p.name:p.read_bytes() for p in failure_dir.iterdir()}
            with pytest.raises(ProviderOutputError):
                run_audit_report_stage(provider=provider,case_dir=session.run_dir,
                    case_id=session.session_hash,session_prefix='phase6.2',audit_call_index=2)
            assert saved=={p.name:p.read_bytes() for p in failure_dir.iterdir()}
            assert len(list((session.run_dir/'audit-failures').glob('*/provider-error.json')))==2
    finally:store.close()
    reopened=SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path)
    try:assert reopened.get_session(session.session_hash).status=='provider_failed'
    finally:reopened.close()
