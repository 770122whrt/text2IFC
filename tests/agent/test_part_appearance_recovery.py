"""Scoped part cleanup must preserve geometry, requested channels and other objects."""
import copy
import json
import pytest
from tests.agent.test_unrequested_appearance import fixture
from tests.agent.test_semantic_scope_and_type_policy import _write
from tests.agent.test_semantic_authority_completeness import review
from tests.agent.test_phase6_5_staged_generation import SequenceProvider
from text2ifc_agent.live_pipeline import run_candidate_gate_stage
from text2ifc_agent.issue_normalizers import normalize_gate_sidecars
from text2ifc_agent.scoped_loop import run_scoped_changeset_round
from text2ifc_agent.candidate_index import build_candidate_index


@pytest.mark.parametrize('brief_version',['2.5','2.6'])
@pytest.mark.parametrize('keep_requested', [False, True])
@pytest.mark.parametrize('attack', ['none', 'geometry', 'erase_requested'])
def test_public_part_cleanup_is_scoped_and_atomic(tmp_path, keep_requested, attack, brief_version):
    candidate, brief, expected, filling = fixture()
    candidate['schema_version'] = 'bim-json/2.3' if brief_version=='2.6' else 'bim-json/2.2'; filling.pop('appearance')
    requested = {'frame': {'color': [.1, .2, .3]}}
    filling['part_appearance'] = {**copy.deepcopy(requested), 'panel': {'color': [.4, .5, .6], 'transparency': .8}}
    brief['schema_version'] = 'text2ifc/design-brief/'+brief_version
    brief['known_facts']['semantic_review'] = review(**({'appearance': True, 'template': True} if keep_requested else {}))
    if keep_requested:
        brief['known_facts']['semantic_requirements'] = [{'entity_id': filling['id'], 'part_appearance': requested,
            'template': {'template_id': 'door-left', 'template_version': 'text2ifc/basic-filling/1.0'}}]
    for name, payload in [('generator/candidate', candidate), ('design-brief', brief), ('expected-facts', expected)]:
        _write(tmp_path/(name+'.json'), payload)
    assert not run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='part-cleanup')['compile_reopen_success']
    before = copy.deepcopy(candidate); hashes = build_candidate_index(candidate)['component_hashes']
    class Provider:
        def generate_live(self, **kwargs):
            root = tmp_path/'round'
            scope = json.loads((root/'change-scope.json').read_text(encoding='utf-8'))
            rev = json.loads((root/'base-revision.json').read_text(encoding='utf-8'))
            edit = {'changes': {'/part_appearance': requested}} if keep_requested else {'remove_paths': ['/part_appearance']}
            if attack == 'geometry': edit.setdefault('changes', {})['/attributes/OverallWidth'] = 999
            if attack == 'erase_requested' and keep_requested: edit = {'remove_paths': ['/part_appearance']}
            payload = {'schema_version': kwargs['schema']['properties']['schema_version']['const'],
                'changeset_id':'part-cleanup', 'base_revision_id':rev['revision_id'],
                'base_candidate_hash':rev['candidate_hash'], 'expected_facts_hash':rev['expected_facts_hash'],
                'scope_id':scope['scope_id'], 'source_issue_ids':scope['source_issue_ids'],
                'operations':[{'operation_id':'part-edit', 'op':'update_entity', 'target_id':filling['id'],
                    'target_component_hash':hashes[filling['id']],
                    'evidence_refs':[i+':/actual' for i in scope['source_issue_ids']], **edit}]}
            return SequenceProvider([payload]).generate_live(**kwargs)
    result = run_scoped_changeset_round(provider=Provider(), output_dir=tmp_path/'round', case_id='part-cleanup',
        round_number=1, user_request='框保留指定色，其他通道遵循默认主题。', conversation=[],
        design_brief=brief, expected_facts=expected, candidate=candidate,
        issues=normalize_gate_sidecars(tmp_path), max_attempts=1)
    success = attack == 'none' or (attack == 'erase_requested' and not keep_requested)
    assert result['valid'] is success, result
    assert candidate == before
    if success:
        desired = copy.deepcopy(candidate); target = next(e for e in desired['entities'] if e['id'] == filling['id'])
        if keep_requested: target['part_appearance'] = requested
        else: target.pop('part_appearance')
        desired['entities'].sort(key=lambda e:e['id']); desired['relationships'].sort(key=lambda e:e['id'])
        assert result['candidate'] == desired
        assert result['preservation']['unrelated_component_preservation_rate'] == 1


@pytest.mark.parametrize('brief_version',['2.5','2.6'])
def test_new_brief_clarification_resumes_after_reopen_without_replaying_call(tmp_path,brief_version):
    from types import SimpleNamespace
    from tests.agent.test_interactive_cli_flow import _brief
    from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker, run_design_brief_clarification_loop
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config
    from text2ifc_agent.session_store import SessionStore
    request = '创建6米乘4米房间和墙体。房门左单开，框为深灰色；整门又要求白色，请确认如何表达。'
    first = _brief(original_request=request, status='needs_clarification')
    ready = _brief(original_request=request, status='ready', source_turns=['turn-user-001', 'turn-user-003'])
    for b in (first, ready):
        b['schema_version'] = 'text2ifc/design-brief/'+brief_version
        b['known_facts'].update(plan_constraints=[], semantic_review=review(appearance=True, template=True))
        b['known_facts']['semantic_requirements'] = [{'entity_id':'door-request',
            'template':{'template_id':'door-left','template_version':'text2ifc/basic-filling/1.0'},
            'part_appearance':{'frame':{'color':[.1,.2,.3]}}}]
    first['known_facts']['semantic_requirements'][0]['appearance'] = {'color':[1,1,1]}
    first['missing_facts'][0].update(code='PART_APPEARANCE_CONFLICT', path='/known_facts/semantic_requirements',
        message='整门白色与深灰框冲突。', reason='整件与部件样式需要确定一种表达。')
    first['clarification_questions'][0].update(text='保留深灰框，取消整门统一白色吗？', reason='解决整件和部件外观冲突。')
    for e in ready['known_facts']['semantic_review'].values(): e['source_turns'] = ['turn-user-001', 'turn-user-003']
    payloads = [first, ready]; sent = []
    def create(**kwargs):
        sent.append(kwargs)
        result={'id':f'fake-clarification-{len(sent)}','model':'fake',
            'choices':[{'finish_reason':'stop','message':{'content':json.dumps(payloads.pop(0))}}],
            'usage':{'prompt_tokens':10,'completion_tokens':20,'total_tokens':30}}
        return SimpleNamespace(model_dump=lambda:result)
    config=load_openai_compatible_runtime_config({'TEXT2IFC_PROVIDER':'deepseek','API_KEY':'fake-key',
        'OPENAI_BASE_URL':'https://example.invalid','TEXT2IFC_DEEPSEEK_MODEL':'fake'})
    store=SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path)
    session=store.create_session(original_input=request)
    def invoker():
        return make_openai_design_brief_invoker(config=config, run_dir=session.run_dir,
            design_brief_schema_version='text2ifc/design-brief/'+brief_version,
            client_factory=lambda **_:SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    result=run_design_brief_clarification_loop(store=store,session=session.session_hash,invoke_design_brief=invoker(),user_answers=[])
    assert result.status=='needs_clarification'
    path=session.run_dir/'calls/01-design-brief/response.raw.json'; original=path.read_bytes()
    store.close();store=SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path)
    result=run_design_brief_clarification_loop(store=store,session=session.session_hash,invoke_design_brief=invoker(),
        user_answers=['保留深灰框，取消整门白色。'])
    assert result.status=='ready',result
    assert len(sent)==2 and path.read_bytes()==original
    assert (session.run_dir/'calls/02-design-brief/design-brief.json').is_file()
    assert not list(session.run_dir.rglob('output.ifc'))
    ledger=json.loads((session.run_dir/'generation-budget.json').read_text(encoding='utf-8'))
    assert len(ledger['attempts'])==2 and sum(a['tokens_charged'] for a in ledger['attempts'])==60
    store.close()
