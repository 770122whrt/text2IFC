"""Exact redundant copies may be folded; conflicts must remain errors."""
import copy
import json
import pytest

from tests.agent.test_component_requirements_v26 import component_brief
from text2ifc_agent.design_brief import validate_design_brief


def duplicate_brief(cls='IfcDoor'):
    brief=component_brief();known=brief['known_facts'];known.pop('doors',None)
    collection='doors' if cls=='IfcDoor' else 'windows'
    row={'id':'filling-1','ifc_class':cls,'storey':'S1','installation':'standalone','width_mm':850,'height_mm':1100}
    known[collection]=[copy.deepcopy(row)]
    known['storeys']=[{'id':'S1','elevation_mm':0,collection:[copy.deepcopy(row)]}]
    return brief,collection


@pytest.mark.parametrize('cls',['IfcDoor','IfcWindow'])
def test_exact_flat_copy_folds_to_the_same_explicit_storey_without_losing_facts(cls):
    from text2ifc_agent.brief_duplicate_normalization import normalize_brief_duplicates
    brief,collection=duplicate_brief(cls);before=copy.deepcopy(brief)
    assert any(i.code=='SEMANTIC_ROLE_IDENTITY_AMBIGUOUS' for i in validate_design_brief(brief))
    normalized,changes=normalize_brief_duplicates(brief)
    assert len(changes)==1 and collection not in normalized['known_facts']
    assert normalized['known_facts']['storeys']==before['known_facts']['storeys']
    assert normalized['known_facts']['semantic_requirements']==before['known_facts']['semantic_requirements']
    assert validate_design_brief(normalized)==[]
    assert brief==before
    assert normalize_brief_duplicates(normalized)==(normalized,[])


@pytest.mark.parametrize('fault',['dimension','storey','missing-storey','missing-field','extra-field','two-nested','two-flat','legacy','not-ready','boolean'])
def test_nonidentical_or_ambiguous_duplicates_are_not_silently_folded(fault):
    from text2ifc_agent.brief_duplicate_normalization import normalize_brief_duplicates
    brief,collection=duplicate_brief();row=brief['known_facts'][collection][0]
    if fault=='dimension':row['width_mm']=900
    elif fault=='storey':row['storey']='S2'
    elif fault=='missing-storey':row.pop('storey')
    elif fault=='missing-field':row.pop('height_mm')
    elif fault=='extra-field':row['name']='Extra information'
    elif fault=='two-nested':brief['known_facts']['storeys'][0][collection].append(copy.deepcopy(row))
    elif fault=='two-flat':brief['known_facts'][collection].append(copy.deepcopy(row))
    elif fault=='legacy':brief['schema_version']='text2ifc/design-brief/2.8'
    elif fault=='not-ready':brief['status']='needs_clarification'
    elif fault=='boolean':
        row['width_mm']=True
        brief['known_facts']['storeys'][0][collection][0]['width_mm']=1
    normalized,changes=normalize_brief_duplicates(brief)
    assert not changes and normalized==brief


def test_actual_public_invoker_preserves_raw_duplicate_and_accepts_normalized_brief(tmp_path):
    from tests.ifc2text.test_component_public_chain_v10 import fake_brief_invoker
    from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop
    from text2ifc_agent.session_store import SessionStore
    brief,collection=duplicate_brief();requests=[]
    with SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path) as store:
        session=store.create_session(original_input=brief['original_request'])
        result=run_design_brief_clarification_loop(store=store,session=session.session_id,
            invoke_design_brief=fake_brief_invoker(session.run_dir,brief,requests),user_answers=())
        assert result.status=='ready' and len(requests)==1
        call=session.run_dir/'calls/01-design-brief'
        assert json.loads((call/'raw-parsed-output.json').read_text(encoding='utf-8'))==brief
        trace=json.loads((call/'normalization.json').read_text(encoding='utf-8'))
        assert len(trace['changes'])==1
        saved=json.loads((session.run_dir/'design-brief.json').read_text(encoding='utf-8'))
        assert collection not in saved['known_facts']
        assert saved['known_facts']['semantic_requirements']==brief['known_facts']['semantic_requirements']


def test_stage_api_uses_same_normalization_and_preserves_original_response(tmp_path):
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from tests.agent.test_semantic_authority_completeness import valid_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case,_=valid_brief();brief,collection=duplicate_brief()
    result=run_design_brief_stage(provider=SequenceProvider([brief]),output_dir=tmp_path/'brief',case=case,
        design_brief_schema_version='text2ifc/design-brief/2.9')
    assert result['valid'],result
    assert json.loads((tmp_path/'brief/raw-parsed-output.json').read_text(encoding='utf-8'))==brief
    accepted=json.loads((tmp_path/'brief/design-brief.json').read_text(encoding='utf-8'))
    assert collection not in accepted['known_facts']
