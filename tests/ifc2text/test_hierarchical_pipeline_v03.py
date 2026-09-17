from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_compiler import compile_document
from text2ifc_ifc2text.hierarchy import make_hierarchy_plan
from text2ifc_ifc2text.hierarchical_pipeline import run_hierarchical_writing
from text2ifc_ifc2text.observation import extract_description_facts, read_materials
from text2ifc_ifc2text.roundtrip_compare import compare_roundtrip

ROOT = Path(__file__).resolve().parents[2]


class Echo:
    def __init__(self, malformed=False):
        self.calls=0
        self.malformed=malformed

    def generate_candidate(self, *, session_id, prompt, schema, state):
        self.calls += 1
        batch,_ = json.JSONDecoder().raw_decode(prompt[prompt.index('{'):])
        result = {'schema_version':'text2ifc/ifc2text-layout/0.3',
                  'groups':[{'block_id':b['id'],'paragraphs':[[i['id']] for i in b['items']]} for b in batch['blocks']]}
        if self.malformed:
            result['groups'][0]['paragraphs']=[]
        return ProviderOutput(text=json.dumps(result),metadata={'evidence_class':'offline_fake'})


def source_fixture(tmp_path):
    document=json.loads((ROOT/'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    p=tmp_path/'source.ifc'
    assert compile_document(document,p).success
    return p


def test_actual_ifc_to_fake_model_grouping_to_complete_text_and_no_overwrite(tmp_path):
    source=source_fixture(tmp_path)
    before=source.read_bytes()
    facts=extract_description_facts(source)
    plan=make_hierarchy_plan(facts)
    provider=Echo()
    result=run_hierarchical_writing(plan=plan,output_dir=tmp_path/'writing',provider=provider,run_id='fixture',max_batch_chars=1200)
    text=Path(result['description_path']).read_text(encoding='utf-8')
    assert result['status']=='completed'
    assert result['mode']=='LLM_paragraph_grouping_with_deterministic_fact_sentences'
    assert provider.calls>1
    assert 'W001' in text and 'D001' in text and 'N001' in text
    assert source.read_bytes()==before
    assert result['component_counts']['slabs'] == 1
    assert result['component_counts']['coverings'] == 1
    assert '楼板 L001' in text and '覆盖层 C001' in text
    with pytest.raises(ValueError,match='ALREADY_EXISTS'):
        run_hierarchical_writing(plan=plan,output_dir=tmp_path/'writing',provider=provider,run_id='fixture')


def test_invalid_model_layout_stops_before_next_call_and_no_final_text(tmp_path):
    source=source_fixture(tmp_path)
    plan=make_hierarchy_plan(extract_description_facts(source))
    provider=Echo(malformed=True)
    with pytest.raises(Exception):
        run_hierarchical_writing(plan=plan,output_dir=tmp_path/'bad',provider=provider,run_id='bad',max_batch_chars=1200)
    assert provider.calls==1
    assert not (tmp_path/'bad'/'design-description.md').exists()
    assert json.loads((tmp_path/'bad'/'terminal.json').read_text())['status']=='failed'


def test_compare_different_guids_and_missing_moved_resized_real_ifc(tmp_path):
    source=source_fixture(tmp_path)
    original=source.read_bytes()
    candidate=tmp_path/'candidate.ifc'
    m=ifcopenshell.open(str(source))
    for e in m.by_type('IfcRoot'):
        e.GlobalId=ifcopenshell.guid.new()
    m.write(str(candidate))
    equal=compare_roundtrip(source,candidate)
    assert equal['status']['evaluated_scope_consistent'] is True
    assert equal['status']['reconstruction_consistent'] is None
    door=m.by_type('IfcDoor')[0]
    m.remove(door)
    m.write(str(candidate))
    missing=compare_roundtrip(source,candidate)
    assert len(missing['components']['doors']['missing'])==1
    assert missing['status']['reconstruction_consistent'] is False
    m=ifcopenshell.open(str(source))
    window=m.by_type('IfcWindow')[0]
    location=window.ObjectPlacement.RelativePlacement.Location
    v=list(location.Coordinates); v[0]+=400; location.Coordinates=v
    window.OverallWidth += 300
    m.write(str(candidate))
    shifted=compare_roundtrip(source,candidate)
    changed=shifted['components']['windows']['matched'][0]
    assert changed['center_delta_mm']>=399
    assert changed['dimension_deltas_mm']['overall_width_mm']==pytest.approx(300)
    assert shifted['alignment'].startswith('none')
    assert source.read_bytes()==original


def test_unknown_dimensions_are_not_zero_error(tmp_path):
    source=source_fixture(tmp_path)
    m=ifcopenshell.open(str(source))
    m.by_type('IfcWindow')[0].OverallWidth=None
    m.write(str(source))
    result=compare_roundtrip(source,source)
    assert result['unassessed']
    assert result['status']['evaluated_scope_consistent'] is None


def test_direct_and_inherited_materials_do_not_infer_from_names(tmp_path):
    p=source_fixture(tmp_path)
    m=ifcopenshell.open(str(p))
    wall=m.by_type('IfcWall')[0]
    wall.Name='Steel concrete name is not a material assignment'
    assert read_materials(wall,1.0)==[]
    material=m.create_entity('IfcMaterial',Name='Actual material')
    m.create_entity('IfcRelAssociatesMaterial',GlobalId=ifcopenshell.guid.new(),
                    OwnerHistory=wall.OwnerHistory,RelatedObjects=[wall],RelatingMaterial=material)
    actual=read_materials(wall,1.0)
    assert actual==[{'kind':'single_material','name':'Actual material','origin':'occurrence'}]


def test_generated_text_reaches_unchanged_public_generation_and_compare(tmp_path):
    # Frozen Provider outputs are labelled fixtures; no claim of model fidelity.
    fixture_root=ROOT/'dataset/processed/agent-demo/phase6.1-mimo-live/complete-room'
    candidate=json.loads((fixture_root/'generator/candidate.json').read_text(encoding='utf-8'))
    source=tmp_path/'original.ifc'
    assert compile_document(candidate,source).success
    before=source.read_bytes()
    plan=make_hierarchy_plan(extract_description_facts(source))
    writing=run_hierarchical_writing(plan=plan,output_dir=tmp_path/'writing',provider=Echo(),run_id='public')
    text=Path(writing['description_path']).read_text(encoding='utf-8')
    spec=importlib.util.spec_from_file_location('offline_fixture_bridge',ROOT/'tests/ifc2text/test_offline_public_bridge.py')
    fixtures=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_ifc2text.text2ifc_public import reconstruct_description_with_public_text2ifc
    provider=fixtures._SequenceLiveProvider([candidate,{
        'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
        'deterministic_gate_status':'passed','findings':[],
        'evidence_paths':['design-brief/design-brief.json','generator/candidate.json']}])
    with SessionStore.open(tmp_path/'generation/sessions.sqlite',artifact_root=tmp_path/'generation') as store:
        result=reconstruct_description_with_public_text2ifc(text,store=store,
            invoke_design_brief=fixtures._design_brief_invoker(store),provider_factory=lambda:provider)
        assert result['status']=='compiled'
        assert store.get_session(result['session_id']).original_input==text
        report=compare_roundtrip(source,result['ifc_path'])
        assert report['status']['files_readable'] is True
        assert report['summary']['missing_count']==0
    assert source.read_bytes()==before
