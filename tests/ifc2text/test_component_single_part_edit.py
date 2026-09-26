"""Offline public generation of a requested single-part edit; no live model claim."""
import copy,json
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
import numpy as np
import pytest
from tests.ifc2text.test_component_hosted_public_chain import hosted_document
from tests.compiler.test_component_geometry_v26 import position
from tests.agent.test_component_requirements_v26 import component_brief
from tests.agent.test_phase6_5_staged_generation import SequenceProvider
from tests.ifc2text.test_component_public_chain_v10 import fake_brief_invoker
from text2ifc_contract.component_geometry import expanded_parts
from text2ifc_compiler.compiler import compile_document
from text2ifc_ifc2text.compact_pipeline import prepare_compact
from text2ifc_ifc2text.text2ifc_public import reconstruct_description_with_public_text2ifc
from text2ifc_agent.session_store import SessionStore

@pytest.mark.parametrize('cls',['IfcDoor','IfcWindow'])
def test_public_single_part_edit_preserves_other_parts_and_host(tmp_path,cls):
    original,label,storey=hosted_document(cls)
    source=tmp_path/'source.ifc';assert compile_document(original,source).success
    raw=source.read_bytes()
    candidate=copy.deepcopy(original);rep=candidate['entities'][-1]['attributes']['Representation']
    rep['parts']=expanded_parts(rep);target=rep['parts'][-1]['id'];rep['parts'][-1]['placement']['origin'][2]+=10
    prepare_compact(source,tmp_path/'description',description_version='1.1',containment_policy='preserve_recorded')
    text=(tmp_path/'description/design-description-deterministic.md').read_text(encoding='utf-8')
    text+='\n\n本轮修改：仅将 '+label+' 的 '+target+' 沿构件局部 Z 轴上移 10 mm；其他部件、墙和开口保持。该修改替代此部件上文的位置。\n'
    brief=component_brief();brief['original_request']=text;k=brief['known_facts'];k.pop('doors')
    k['storeys']=[{'id':storey,'elevation_mm':0}]
    k['walls']=[{'id':'W001','ifc_class':'IfcWall','storey':storey,'height_mm':3000,'thickness_mm':200}]
    k['openings']=[{'id':'O001','ifc_class':'IfcOpeningElement','storey':storey,'host_wall':'W001'}]
    k['doors' if cls=='IfcDoor' else 'windows']=[{'id':label,'ifc_class':cls,'storey':storey,'width_mm':850,'height_mm':1100,
        'installation':'hosted','host_wall':'W001','opening':'O001','placement':position((-425,100,500))}]
    k['semantic_requirements'][0].update(entity_id=label,component_geometry=rep)
    audit={'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
        'deterministic_gate_status':'passed','findings':[],'evidence_paths':['generator/candidate.json']}
    provider=SequenceProvider([candidate,audit]);requests=[];root=tmp_path/'generation'
    with SessionStore.open(root/'sessions.sqlite',artifact_root=root) as store:
        def invoke(transcript,index):return fake_brief_invoker(store.list_sessions()[-1].run_dir,brief,requests)(transcript,index)
        result=reconstruct_description_with_public_text2ifc(text,store=store,invoke_design_brief=invoke,provider_factory=lambda:provider,bim_json_schema_version='bim-json/2.6')
    assert result['status']=='compiled',result
    left=ifcopenshell.open(str(source));right=ifcopenshell.open(result['ifc_path'])
    a=left.by_type(cls)[0];b=right.by_type(cls)[0]
    old={x.Name:x for x in a.Representation.HasShapeAspects};new={x.Name:x for x in b.Representation.HasShapeAspects}
    assert set(old)==set(new)
    settings=ifcopenshell.geom.settings()
    def vertices(aspect):
        return np.vstack([np.asarray(ifcopenshell.geom.create_shape(settings,i).verts).reshape(-1,3)*1000 for s in aspect.ShapeRepresentations for i in s.Items])
    for name in old:
        delta=vertices(new[name])-vertices(old[name])
        assert np.allclose(delta,[0,0,10] if name==target else [0,0,0],atol=1e-6,rtol=0)
    for kind in ['IfcWall','IfcOpeningElement']:
        x=ifcopenshell.geom.create_shape(settings,left.by_type(kind)[0]).geometry
        y=ifcopenshell.geom.create_shape(settings,right.by_type(kind)[0]).geometry
        assert np.allclose(x.verts,y.verts,atol=1e-9,rtol=0)
    assert len(b.FillsVoids)==1
    assert b.FillsVoids[0].RelatingOpeningElement.VoidsElements[0].RelatingBuildingElement.is_a('IfcWall')
    assert source.read_bytes()==raw
    assert all(str(source) not in json.dumps(r) for r in requests)
