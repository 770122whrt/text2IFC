"""Human choice over unsupported components; no Provider before exact approval."""
import copy
import json
from pathlib import Path
import pytest
from tests.ifc2text.test_component_hosted_public_chain import hosted_document
from text2ifc_compiler.compiler import compile_document
from text2ifc_ifc2text.compact_pipeline import prepare_compact
from text2ifc_agent.session_store import SessionStore

@pytest.fixture
def sample(tmp_path):
    candidate,_,_=hosted_document('IfcWindow')
    source=tmp_path/'source.ifc'
    assert compile_document(candidate,source).success
    prepare_compact(source,tmp_path/'prepared',description_version='1.1',containment_policy='preserve_recorded')
    facts=json.loads((tmp_path/'prepared/source-facts.json').read_text(encoding='utf-8'))
    floor=facts['storeys'][0]
    extra=copy.deepcopy(floor['windows'][0]);extra.update(label='D099',ifc_class='IfcDoor',source_global_id='private-unsupported-guid')
    extra['component_detail']={'status':'unsupported','unsupported':[{'ifc_class':'IfcFacetedBrep','reason':'BRep cannot be reconstructed by straight extrusion','source_item_id':999,'impact':'whole door omitted only after approval'}]}
    floor['doors'].append(extra)
    # Its separate opening has the same shape for this review-only fixture.
    op=copy.deepcopy(floor['openings'][0]);op.update(label='O099',source_global_id='private-opening',filling='D099',filling_global_id=extra['source_global_id'])
    extra['opening']='O099';floor['openings'].append(op);floor['walls'][0]['openings'].append('O099')
    facts['capability']['door_count']=1;facts['capability']['opening_count']=2
    return facts,source

def api():
    from text2ifc_ifc2text.component_review import start_review,review_state,decide_review,approved_description
    return start_review,review_state,decide_review,approved_description

def test_pause_restart_then_explicit_exclusion_preserves_remainder(sample,tmp_path):
    start,state,decide,description=api();facts,source=sample;before=copy.deepcopy(facts);raw=source.read_bytes()
    db=tmp_path/'review.sqlite';art=tmp_path/'review'
    with SessionStore.open(db,artifact_root=art) as store:
        r=start(store=store,facts=facts)
        sid=r['session_id'];h=r['review_sha256']
        assert r['status']=='awaiting_human'
        assert 'D099' in r['question'] and 'BRep' in r['question'] and '开口' in r['question']
        with pytest.raises(ValueError,match='HUMAN_DECISION_REQUIRED'):description(store=store,session_id=sid)
        paused=decide(store=store,session_id=sid,review_sha256=h,action='pause',excluded_labels=[])
        assert paused['status']=='paused'
    with SessionStore.open(db,artifact_root=art) as store:
        assert state(store=store,session_id=sid)['status']=='paused'
        done=decide(store=store,session_id=sid,review_sha256=h,action='exclude_and_continue',excluded_labels=['D099'])
        assert done['status']=='approved_partial'
        packet=description(store=store,session_id=sid)
        text=packet['description'];scoped=packet['facts']
        assert '#### N001 部件几何' in text and '#### D099 部件几何' not in text
        assert '部分重建' in text and 'D099' in text
        assert 'private-unsupported-guid' not in text and 'source_item_id' not in text and str(source) not in text
        f=scoped['storeys'][0]
        assert f['doors']==[] and f['windows']==facts['storeys'][0]['windows']
        assert f['walls']==facts['storeys'][0]['walls']
        assert f['openings'][1]['filling'] is None and f['openings'][1]['filling_global_id'] is None
        op=copy.deepcopy(facts['storeys'][0]['openings'][1]);op.update(filling=None,filling_global_id=None)
        assert f['openings'][1]==op
        assert scoped['capability']['door_count']==0 and scoped['capability']['opening_count']==2
        count=len(store.list_events(sid))
        assert decide(store=store,session_id=sid,review_sha256=h,action='exclude_and_continue',excluded_labels=['D099'])==done
        assert len(store.list_events(sid))==count
    assert facts==before and source.read_bytes()==raw
    assert not list(art.rglob('*.ifc'))

@pytest.mark.parametrize('action,labels,hash_mode,error',[
    ('continue',[],False,'EXPLICIT_ACTION_REQUIRED'),
    ('exclude_and_continue',[],False,'EXACT_UNSUPPORTED_SET_REQUIRED'),
    ('exclude_and_continue',['D099','N001'],False,'EXACT_UNSUPPORTED_SET_REQUIRED'),
    ('exclude_and_continue',['D099','D099'],False,'EXACT_UNSUPPORTED_SET_REQUIRED'),
    ('exclude_and_continue',['D099'],True,'STALE_REVIEW'),
    ('pause',['D099'],False,'PAUSE_CANNOT_EXCLUDE'),
])
def test_ambiguous_stale_or_expanded_approval_never_authorizes(sample,tmp_path,action,labels,hash_mode,error):
    start,state,decide,description=api();facts,_=sample
    with SessionStore.open(tmp_path/'r.sqlite',artifact_root=tmp_path/'r') as store:
        r=start(store=store,facts=facts)
        with pytest.raises(ValueError,match=error):
            decide(store=store,session_id=r['session_id'],review_sha256='stale' if hash_mode else r['review_sha256'],action=action,excluded_labels=labels)
        assert state(store=store,session_id=r['session_id'])['status']=='awaiting_human'

@pytest.mark.parametrize('change',['facts','source'])
def test_changed_input_blocks_resume(sample,tmp_path,change):
    start,state,decide,description=api();facts,source=sample
    with SessionStore.open(tmp_path/'r.sqlite',artifact_root=tmp_path/'r') as store:
        r=start(store=store,facts=facts);sid=r['session_id']
        if change=='facts':
            p=store.get_session(sid).run_dir/'component-review-facts.private.json'
            p.write_text('{}',encoding='utf-8')
        else:source.write_bytes(source.read_bytes()+b'\n')
        with pytest.raises(ValueError,match='CHANGED'):
            decide(store=store,session_id=sid,review_sha256=r['review_sha256'],action='exclude_and_continue',excluded_labels=['D099'])

@pytest.mark.parametrize('change',['unrepresented','wall','opening','missing_detail'])
def test_other_unsupported_content_cannot_be_hidden_by_door_exclusion(sample,tmp_path,change):
    start,state,decide,description=api();facts,_=sample
    if change=='unrepresented':facts['unrepresented_classes']={'IfcRoof':1}
    elif change=='wall':facts['storeys'][0]['walls'][0]['solid_detail']['status']='unsupported'
    elif change=='opening':facts['storeys'][0]['openings'][0]['opening_solid_detail']['status']='unsupported'
    else:facts['storeys'][0]['windows'][0].pop('component_detail')
    with SessionStore.open(tmp_path/'r.sqlite',artifact_root=tmp_path/'r') as store:
        r=start(store=store,facts=facts)
        assert r['other_blockers']
        with pytest.raises(ValueError,match='ADDITIONAL_UNSUPPORTED_CONTENT'):
            decide(store=store,session_id=r['session_id'],review_sha256=r['review_sha256'],action='exclude_and_continue',excluded_labels=['D099'])

def test_public_bridge_pause_makes_no_provider_call(sample,tmp_path):
    from text2ifc_ifc2text.component_review import reconstruct_reviewed_description
    start,_,decide,_=api();facts,_=sample
    def forbidden(*args,**kwargs):pytest.fail('Paused review must not invoke a model')
    with SessionStore.open(tmp_path/'r.sqlite',artifact_root=tmp_path/'r') as store:
        r=start(store=store,facts=facts)
        for pause in (False,True):
            if pause:decide(store=store,session_id=r['session_id'],review_sha256=r['review_sha256'],action='pause',excluded_labels=[])
            result=reconstruct_reviewed_description(store=store,session_id=r['session_id'],
                invoke_design_brief=forbidden,provider_factory=forbidden)
            assert result['status']==('paused' if pause else 'awaiting_human')
            assert result['ifc_path'] is None
        assert len(store.list_sessions())==1


def test_reviewed_partial_model_reaches_real_public_compiler_and_is_idempotent(tmp_path):
    from tests.compiler.test_component_geometry_v26 import position
    from tests.agent.test_component_requirements_v26 import component_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    from tests.ifc2text.test_component_public_chain_v10 import fake_brief_invoker
    from text2ifc_ifc2text.component_review import reconstruct_reviewed_description
    from text2ifc_ifc2text.precision_compare_v12 import compare_roundtrip
    start,_,decide,description=api()
    candidate,label,storey=hosted_document('IfcWindow')
    source=tmp_path/'source.ifc';assert compile_document(candidate,source).success
    prepare_compact(source,tmp_path/'prepared',description_version='1.1',containment_policy='preserve_recorded')
    facts=json.loads((tmp_path/'prepared/source-facts.json').read_text(encoding='utf-8'))
    # Synthetic unsupported standalone sibling tests review, not extraction fidelity.
    extra=copy.deepcopy(facts['storeys'][0]['windows'][0])
    extra.update(label='D099',ifc_class='IfcDoor',source_global_id='private-extra',opening=None,host_wall=None)
    extra['component_detail']={'status':'unsupported','unsupported':[{'ifc_class':'IfcFacetedBrep','reason':'Unsupported boundary representation'}]}
    facts['storeys'][0]['doors'].append(extra)
    root=tmp_path/'generation';requests=[]
    with SessionStore.open(root/'sessions.sqlite',artifact_root=root) as store:
        r=start(store=store,facts=facts)
        decide(store=store,session_id=r['session_id'],review_sha256=r['review_sha256'],action='exclude_and_continue',excluded_labels=['D099'])
        text=description(store=store,session_id=r['session_id'])['description']
        brief=component_brief();brief['original_request']=text;k=brief['known_facts'];k.pop('doors')
        k['storeys']=[{'id':storey,'elevation_mm':0}]
        k['walls']=[{'id':'W001','ifc_class':'IfcWall','storey':storey,'height_mm':3000,'thickness_mm':200}]
        k['openings']=[{'id':'O001','ifc_class':'IfcOpeningElement','storey':storey,'host_wall':'W001'}]
        k['windows']=[{'id':label,'ifc_class':'IfcWindow','storey':storey,'width_mm':850,'height_mm':1100,
            'installation':'hosted','host_wall':'W001','opening':'O001','placement':position((-425,100,500))}]
        k['semantic_requirements'][0]['entity_id']=label
        audit={'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
               'deterministic_gate_status':'passed','findings':[],'evidence_paths':['generator/candidate.json']}
        provider=SequenceProvider([candidate,audit])
        def invoke(transcript,index):
            return fake_brief_invoker(next(s for s in store.list_sessions() if s.original_input==text).run_dir,brief,requests)(transcript,index)
        opts=dict(store=store,session_id=r['session_id'],invoke_design_brief=invoke,
                  provider_factory=lambda:provider,bim_json_schema_version='bim-json/2.6')
        result=reconstruct_reviewed_description(**opts)
        assert result['status']=='compiled' and result['partial_reconstruction']
        assert result['excluded_labels']==['D099']
        assert reconstruct_reviewed_description(**opts)==result
        assert len(requests)==1 and len(store.list_sessions())==2
        comparison=compare_roundtrip(source,result['ifc_path'])
        assert comparison['summary']['geometric_deviations']==0
        assert comparison['components']['windows']['matched'][0]['filling_geometry']['pass']
        assert all('private-extra' not in json.dumps(v) and str(source) not in json.dumps(v) for v in requests)


def test_campaign_requires_review_before_using_partial_text(sample,tmp_path):
    from scripts.ifc2text.component_campaign import frozen_text,digest
    start,_,decide,description=api();facts,source=sample
    db=tmp_path/'r.sqlite'
    with SessionStore.open(db,artifact_root=tmp_path/'r') as store:
        r=start(store=store,facts=facts)
        text=tmp_path/'description.md';text.write_text('arbitrary',encoding='utf-8')
        case={'source':str(source),'source_sha256':digest(source),'text':str(text),'text_sha256':digest(text),
              'component_review':{'database':str(db),'session_id':r['session_id'],'review_sha256':r['review_sha256']}}
        with pytest.raises(ValueError,match='HUMAN_DECISION_REQUIRED'):frozen_text(case)
        decide(store=store,session_id=r['session_id'],review_sha256=r['review_sha256'],action='exclude_and_continue',excluded_labels=['D099'])
        with pytest.raises(ValueError,match='REVIEW_DESCRIPTION_CHANGED'):frozen_text(case)
        text.write_text(description(store=store,session_id=r['session_id'])['description'],encoding='utf-8');case['text_sha256']=digest(text)
        assert frozen_text(case)==text.read_text(encoding='utf-8')
        case['component_review']['review_sha256']='stale'
        with pytest.raises(ValueError,match='STALE_REVIEW'):frozen_text(case)


def test_cli_show_pause_and_export_use_the_saved_review(sample,tmp_path,capsys):
    from scripts.ifc2text.component_review_cli import main
    start,_,_,_=api();facts,_=sample;db=tmp_path/'r.sqlite'
    with SessionStore.open(db,artifact_root=tmp_path/'r') as store:r=start(store=store,facts=facts)
    common=['--database',str(db),'--session',r['session_id']]
    assert main(['show',*common])==0
    assert 'D099' in capsys.readouterr().out
    assert main(['decide',*common,'--review-sha256',r['review_sha256'],'--action','pause'])==0
    with pytest.raises(ValueError,match='HUMAN_DECISION_REQUIRED'):main(['export',*common,'--output',str(tmp_path/'public')])
    assert not (tmp_path/'public').exists()
    assert main(['decide',*common,'--review-sha256',r['review_sha256'],'--action','exclude_and_continue','--exclude','D099'])==0
    assert main(['export',*common,'--output',str(tmp_path/'public')])==0
    assert '部分重建' in (tmp_path/'public/design-description.md').read_text(encoding='utf-8')
    assert json.loads((tmp_path/'public/refusals.json').read_text(encoding='utf-8'))[0]['label']=='D099'
    with pytest.raises(FileExistsError):main(['export',*common,'--output',str(tmp_path/'public')])

