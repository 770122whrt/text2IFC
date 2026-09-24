"""Both hosted product families through actual public APIs with offline models."""
import copy
import json

import ifcopenshell
import pytest

from tests.compiler.test_component_geometry_v26 import document,position
from tests.agent.test_component_requirements_v26 import component_brief
from tests.agent.test_phase6_5_staged_generation import SequenceProvider
from tests.ifc2text.test_component_public_chain_v10 import fake_brief_invoker
from text2ifc_compiler.compiler import compile_document
from text2ifc_agent.session_store import SessionStore
from text2ifc_ifc2text.compact_pipeline import prepare_compact
from text2ifc_ifc2text.text2ifc_public import reconstruct_description_with_public_text2ifc
from text2ifc_ifc2text.precision_compare_v12 import compare_roundtrip


def hosted_document(cls):
    candidate=document(cls);label='D001' if cls=='IfcDoor' else 'N001'
    for entity in candidate['entities'][:-1]:
        placement=entity.get('attributes',{}).get('ObjectPlacement')
        if placement:placement['origin']=[0,0,0]
    product=candidate['entities'][-1];product['id']=label
    storey=next(e['id'] for e in candidate['entities'] if e['ifc_class']=='IfcBuildingStorey')
    def prism(identity,kind,parent,origin,x,y,depth):
        return {'id':identity,'ifc_class':kind,'attributes':{'Name':identity,
            'ObjectPlacement':{'relative_to':parent,**position(origin)},
            'Representation':{'kind':'extruded_profile','profile':{'kind':'rectangle','x':x,'y':y},'depth':depth,'direction':[0,0,1]}},
            'property_sets':{},'provenance':{'source':'offline-fixture'}}
    wall=prism('W001','IfcWall',storey,(0,0,0),3000,200,3000)
    opening=prism('O001','IfcOpeningElement','W001',(0,0,500),850,200,1100)
    product['attributes']['ObjectPlacement']={'relative_to':'O001',**position((-425,100,0))}
    candidate['entities'][-1:-1]=[wall,opening]
    candidate['relationships']=[
        {'id':'cut','ifc_class':'IfcRelVoidsElement','attributes':{'RelatingBuildingElement':'W001','RelatedOpeningElement':'O001'},'provenance':{'source':'offline-fixture'}},
        {'id':'fill','ifc_class':'IfcRelFillsElement','attributes':{'RelatingOpeningElement':'O001','RelatedBuildingElement':label},'provenance':{'source':'offline-fixture'}}]
    return candidate,label,storey


@pytest.mark.parametrize('cls',['IfcDoor','IfcWindow'])
@pytest.mark.parametrize('reverse_frame', [False, True])
def test_hosted_text_loop_preserves_cut_filling_geometry_and_world_placement(tmp_path,cls,reverse_frame):
    candidate,label,storey=hosted_document(cls)
    if reverse_frame:
        candidate['entities'][-1]['attributes']['ObjectPlacement'].update(origin=[425,-100,0],ref_direction=[-1,0,0])
    source=tmp_path/'source.ifc';result=compile_document(candidate,source);assert result.success,result
    before=source.read_bytes()
    prepare_compact(source,tmp_path/'description',description_version='1.1',containment_policy='preserve_recorded')
    text=(tmp_path/'description/design-description-deterministic.md').read_text(encoding='utf-8')
    brief=component_brief();brief['original_request']=text
    facts=brief['known_facts'];facts.pop('doors')
    facts['storeys']=[{'id':storey,'elevation_mm':0}]
    facts['walls']=[{'id':'W001','ifc_class':'IfcWall','storey':storey,'height_mm':3000,'thickness_mm':200}]
    facts['openings']=[{'id':'O001','ifc_class':'IfcOpeningElement','storey':storey,'host_wall':'W001'}]
    facts['doors' if cls=='IfcDoor' else 'windows']=[{'id':label,'ifc_class':cls,'storey':storey,'width_mm':850,'height_mm':1100,
        'installation':'hosted','host_wall':'W001','opening':'O001',
        'placement':{**position((425,-100,500) if reverse_frame else (-425,100,500)),
                     'ref_direction':[-1,0,0] if reverse_frame else [1,0,0]}}]
    facts['semantic_requirements'][0]['entity_id']=label
    audit={'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
           'deterministic_gate_status':'passed','findings':[],'evidence_paths':['generator/candidate.json']}
    provider=SequenceProvider([candidate,audit]);requests=[];root=tmp_path/'generation'
    with SessionStore.open(root/'sessions.sqlite',artifact_root=root) as store:
        def invoke(transcript,index):
            return fake_brief_invoker(store.list_sessions()[-1].run_dir,brief,requests)(transcript,index)
        result=reconstruct_description_with_public_text2ifc(text,store=store,invoke_design_brief=invoke,
            provider_factory=lambda:provider,bim_json_schema_version='bim-json/2.6')
        assert result['status']=='compiled',result
        output=ifcopenshell.open(result['ifc_path']);filling=output.by_type(cls)[0]
        assert len(filling.FillsVoids)==1
        assert filling.FillsVoids[0].RelatingOpeningElement.VoidsElements[0].RelatingBuildingElement.is_a('IfcWall')
        comparison=compare_roundtrip(source,result['ifc_path'])
        assert comparison['summary']=={'matched':3,'missing':0,'extra':0,'geometric_deviations':0,
            'material_content_differences':0,'material_metadata_differences':0,'relation_differences':0,
            'storey_elevation_deviations':0,'missing_storeys':0,'extra_storeys':0}
        assert comparison['components']['walls']['matched'][0]['wall_geometry']['pass']
        category='doors' if cls=='IfcDoor' else 'windows'
        assert comparison['components'][category]['matched'][0]['filling_geometry']['pass']
        # The source has no native Axis representation: legacy intrinsic wall
        # dimension fields remain unassessed even though actual cut/uncut Body
        # checks pass. Preserve that limitation instead of rewriting the score.
        assert comparison['unassessed']==[{'category':'walls','source':'W001','candidate':'W001',
            'fields':['length_mm','thickness_mm','height_mm']}]
        assert source.read_bytes()==before
        assert all(str(source) not in json.dumps(r) for r in requests)
        assert (root/'final-acceptance.json').exists()
