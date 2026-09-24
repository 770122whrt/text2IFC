"""Complete public chain with explicitly injected offline model responses."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import ifcopenshell

from tests.agent.test_component_requirements_v26 import component_brief
from tests.agent.test_phase6_5_staged_generation import SequenceProvider
from tests.compiler.test_component_geometry_v26 import document
from text2ifc_compiler.compiler import compile_document
from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker
from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config
from text2ifc_agent.session_store import SessionStore
from text2ifc_ifc2text.compact_pipeline import prepare_compact
from text2ifc_ifc2text.text2ifc_public import reconstruct_description_with_public_text2ifc


def fake_brief_invoker(root,brief,requests,finish_reason='stop'):
    def create(**kwargs):
        requests.append(kwargs)
        return {'id':'offline-component-brief','model':'offline-fixture',
            'choices':[{'index':0,'finish_reason':finish_reason,'message':{'role':'assistant','content':brief if isinstance(brief,str) else json.dumps(brief)}}],
            'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}}
    config=load_openai_compatible_runtime_config({'API_KEY':'offline-only',
        'OpenAI_BASE_URL':'https://offline.invalid','TEXT2IFC_MIMO_MODEL':'offline-fixture'})
    return make_openai_design_brief_invoker(config=config,run_dir=root,
        client_factory=lambda **_:SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))),
        design_brief_schema_version='text2ifc/design-brief/2.9')


@pytest.mark.parametrize('cls',['IfcDoor','IfcWindow'])
def test_source_text_public_brief_generator_reopen_with_offline_models(tmp_path,cls):
    candidate=document(cls)
    label='D001' if cls=='IfcDoor' else 'N001'
    candidate['entities'][-1]['id']=label
    source=tmp_path/'private-source.ifc'
    assert compile_document(candidate,source).success
    source_bytes=source.read_bytes()
    prepare_compact(source,tmp_path/'description',description_version='1.0',containment_policy='preserve_recorded')
    text=(tmp_path/'description/design-description-deterministic.md').read_text(encoding='utf-8')
    brief=component_brief()
    brief['known_facts']['semantic_requirements'][0]['entity_id']=label
    brief['original_request']=text
    collection='doors' if cls=='IfcDoor' else 'windows'
    brief['known_facts'].pop('doors')
    storey=next(e for e in candidate['entities'] if e['ifc_class']=='IfcBuildingStorey')
    brief['known_facts']['storeys']=[{'id':storey['id'],'elevation_mm':0}]
    brief['known_facts'][collection]=[{'id':label,'ifc_class':cls,'storey':storey['id'],
                                      'width_mm':850,'height_mm':1100,'installation':'standalone'}]
    audit={'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
        'deterministic_gate_status':'passed','findings':[],'evidence_paths':['generator/candidate.json']}
    generation=SequenceProvider([candidate,audit]);requests=[]
    root=tmp_path/'generation'
    with SessionStore.open(root/'sessions.sqlite',artifact_root=root) as store:
        # Deferred construction uses the session made by the public bridge.
        def invoke(transcript,index):
            session=store.list_sessions()[-1]
            return fake_brief_invoker(session.run_dir,brief,requests)(transcript,index)
        result=reconstruct_description_with_public_text2ifc(text,store=store,
            invoke_design_brief=invoke,provider_factory=lambda:generation,bim_json_schema_version='bim-json/2.6')
        assert result['status']=='compiled',result
        output=ifcopenshell.open(result['ifc_path'])
        assert len(output.by_type(cls))==1
        assert len(output.by_type(cls)[0].Representation.HasShapeAspects)==15
        assert (root/'final-acceptance.json').is_file()
        assert source.read_bytes()==source_bytes
        for request in requests:
            assert str(source) not in json.dumps(request)
        session=store.get_session(result['session_id'])
        saved=json.loads((session.run_dir/'design-brief.json').read_text(encoding='utf-8'))
        assert saved==brief
        # This file makes the transport substitution explicit alongside all traces.
        (root/'OFFLINE-FIXTURE.json').write_text(json.dumps({'evidence_class':'offline_injected_provider',
            'real_provider_calls':0,'not_a_capability_claim':True}),encoding='utf-8')


def unsupported_brief(request):
    brief=component_brief()
    brief.update(original_request=request,status='needs_clarification')
    brief['known_facts']['semantic_requirements']=[]
    brief['known_facts']['semantic_review']['component_geometry']['status']='not_specified'
    brief['unsupported_requests']=[{'id':'unsupported-handle','path':'/known_facts/doors/0',
        'message':'门把手含自由曲面 BRep，本版无法重建。','reason':'直线挤出无法表达该曲面。',
        'blocking':True,'requested_value':'BRep handle','evidence_refs':['schema:bim-json-v2:representation'], 'source_turns':['turn-user-001']}]
    brief['clarification_questions']=[{'id':'question-handle','text':'该把手暂不支持；请修改描述、讨论扩展，或停止。',
        'targets':['unsupported-handle'],'reason':'不能静默简化或省略。','evidence_refs':['schema:bim-json-v2:representation']}]
    return brief


def test_unsupported_returns_question_persists_and_waits_on_resume(tmp_path):
    from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop
    request='创建包含自由曲面 BRep 把手的门，几何必须一致。'
    brief=unsupported_brief(request);requests=[]
    with SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path) as store:
        def invoke(transcript,index):
            session=store.list_sessions()[-1]
            return fake_brief_invoker(session.run_dir,brief,requests)(transcript,index)
        result=reconstruct_description_with_public_text2ifc(request,store=store,invoke_design_brief=invoke,
            provider_factory=lambda:pytest.fail('Generator must not run while unsupported'))
        assert result['status']=='needs_clarification' and result['ifc_path'] is None
        session_id=result['session_id']
        assert any('把手暂不支持' in t.text for t in store.list_turns(session_id))
    # A fresh database connection restores the pending question without another call.
    with SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path) as store:
        result=run_design_brief_clarification_loop(store=store,session=session_id,
            invoke_design_brief=lambda *_:pytest.fail('No answer, no call'),user_answers=[])
        assert result.status=='needs_clarification' and len(requests)==1
        result=run_design_brief_clarification_loop(store=store,session=session_id,
            invoke_design_brief=invoke,user_answers=['继续，但保持原要求。'])
        assert result.status=='needs_clarification' and len(requests)==2
        assert any(t.text=='继续，但保持原要求。' for t in store.list_turns(session_id))
        assert not list(tmp_path.rglob('output.ifc'))


def test_missing_parameter_answer_resumes_to_ready_without_losing_parts(tmp_path):
    from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop
    request='创建已描述的框和14片叶片；窗框挤出深度待我补充。'
    missing=unsupported_brief(request)
    missing['unsupported_requests']=[]
    missing['missing_facts']=[{'id':'missing-depth','code':'COMPONENT_DEPTH_MISSING',
        'path':'/known_facts/semantic_requirements','message':'缺窗框挤出深度。','reason':'深度不能猜测。',
        'blocking':True,'evidence_refs':['schema:bim-json-v2:representation'],'source_turns':['turn-user-001']}]
    missing['clarification_questions']=[{'id':'question-depth','text':'窗框挤出深度是多少毫米？',
        'targets':['missing-depth'],'reason':'保留完整实体。','evidence_refs':['schema:bim-json-v2:representation']}]
    ready=component_brief();ready['original_request']=request
    requests=[]
    with SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path) as store:
        session=store.create_session(original_input=request)
        first=run_design_brief_clarification_loop(store=store,session=session.session_id,
            invoke_design_brief=fake_brief_invoker(session.run_dir,missing,requests),user_answers=[])
        assert first.status=='needs_clarification'
        session_id=session.session_id
    with SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path) as store:
        session=store.get_session(session_id)
        result=run_design_brief_clarification_loop(store=store,session=session_id,
            invoke_design_brief=fake_brief_invoker(session.run_dir,ready,requests),user_answers=['100毫米。'])
        assert result.status=='ready' and result.call_count==2
        assert any(t.text=='100毫米。' for t in store.list_turns(session_id))
        conversation=json.loads((session.run_dir/'calls/02-design-brief/conversation.json').read_text(encoding='utf-8'))
        assert conversation[-1]['question_ids']==['question-depth']
        saved=json.loads((session.run_dir/'design-brief.json').read_text(encoding='utf-8'))
        assert saved['known_facts']['semantic_requirements']==ready['known_facts']['semantic_requirements']


@pytest.mark.parametrize('payload,finish',[('{"schema_version":','stop'),('not-json','stop'),(None,'length')])
def test_malformed_or_truncated_brief_keeps_attempt_and_never_generates(tmp_path,payload,finish):
    from text2ifc_agent.openai_compat import OpenAICompatError
    requests=[]
    with SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path) as store:
        def invoke(transcript,index):
            session=store.list_sessions()[-1]
            brief=component_brief();brief['original_request']=transcript[0]['content']
            return fake_brief_invoker(session.run_dir,payload if payload is not None else brief,requests,finish)(transcript,index)
        with pytest.raises(OpenAICompatError):
            reconstruct_description_with_public_text2ifc('Create the described door.',store=store,
                invoke_design_brief=invoke,provider_factory=lambda:pytest.fail('Generator called'))
        assert len(requests)==1
        assert list(tmp_path.rglob('response.raw.json'))
        assert not list(tmp_path.rglob('output.ifc'))
