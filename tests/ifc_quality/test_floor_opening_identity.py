"""Frozen host/identity/geometry family, compiled then independently reopened."""
from copy import deepcopy
import hashlib

import ifcopenshell
import pytest

from text2ifc_compiler import compile_document
from text2ifc_quality.generated_ifc import check_generated_ifc
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation


def _solid(identity, kind, x, y, z, width, depth, height):
    return {'id': identity, 'ifc_class': kind, 'attributes': {
        'Name': identity, 'ObjectPlacement': {'relative_to': 'project', 'origin': [x,y,z],
            'axis': [0,0,1], 'ref_direction': [1,0,0]},
        'Representation': {'kind': 'extruded_profile', 'profile': {'kind': 'rectangle', 'x': width, 'y': depth},
                           'depth': height, 'direction': [0,0,1]}},
        'property_sets': {}, 'provenance': {'source': 'test'}}


def _compile(tmp_path, openings=(('actual-cut', 'deck-a', 1000),), *, rotate=False):
    entities=[{'id': 'project','ifc_class': 'IfcProject','attributes': {'Name':'Fixture'},
               'property_sets':{},'provenance':{'source':'test'}},
              _solid('deck-a','IfcSlab',2000,2000,3000,4000,4000,200),
              _solid('deck-b','IfcSlab',2000,2000,7000,4000,4000,200)]
    relations=[]
    for identity,host,x in openings:
        entities.append(_solid(identity,'IfcOpeningElement',x,1500,3000,800,1000,200))
        relations.append({'id':f'void-{identity}','ifc_class':'IfcRelVoidsElement',
                          'attributes':{'RelatingBuildingElement':host,'RelatedOpeningElement':identity},
                          'provenance':{'source':'test'}})
    if rotate:
        for entity in entities[1:]:
            place=entity['attributes']['ObjectPlacement']; x,y,z=place['origin']
            place.update(origin=[-y,x,z], ref_direction=[0,1,0])
    doc={'schema_version':'bim-json/2.0','ifc_schema':'IFC2X3','units':{'length':'MILLIMETRE'},
         'entities':entities,'relationships':relations,'provenance':{'source':'test'}}
    path=tmp_path/'model.ifc'
    result=compile_document(doc,path)
    assert result.success,result
    return path


def _expect(identity='expected-cut', *, source='derived', rotate=False):
    bounds={'x':[.6,1.4],'y':[1,2],'z':[3,3.2]}
    if rotate:
        bounds={'x':[-2,-1],'y':[.6,1.4],'z':[3,3.2]}
    return {'schema_version':'text2ifc/design-geometry-expectation/1.1', 'walls':{},
            'floor_openings':{identity:{'bbox':bounds,'host_slab_id':'deck-a',
                                       'identity_source':source,'source_fact_refs':['/known_facts/floor_slabs/0/opening']}}}


@pytest.mark.parametrize('rotate',[False,True])
def test_missing_generated_identity_binds_only_unique_reopened_host_and_bounds(tmp_path,rotate):
    path=_compile(tmp_path,rotate=rotate); expectation=_expect(rotate=rotate)
    frozen=deepcopy(expectation); before=hashlib.sha256(path.read_bytes()).hexdigest()
    result=check_generated_ifc(path,expectation)
    assert result.success,result.issues
    assert result.metrics['floor_openings']['expected-cut']['binding_basis']=='unique_host_and_bounds'
    assert result.metrics['floor_openings']['expected-cut']['resolved_bim_json_id']=='actual-cut'
    assert expectation==frozen and hashlib.sha256(path.read_bytes()).hexdigest()==before


@pytest.mark.parametrize('source',['explicit',None])
def test_no_fallback_without_explicit_derived_policy(tmp_path,source):
    expectation=_expect(source=source)
    assert not check_generated_ifc(_compile(tmp_path),expectation).success


def test_legacy_contract_keeps_strict_identity_lookup(tmp_path):
    expectation=_expect(); expectation['schema_version']='text2ifc/design-geometry-expectation/1.0'
    assert not check_generated_ifc(_compile(tmp_path),expectation).success


@pytest.mark.parametrize('identity',['actual-cut','expected-cut'])
def test_wrong_host_never_matches_even_when_identity_and_bounds_match(tmp_path,identity):
    result=check_generated_ifc(_compile(tmp_path,((identity,'deck-b',1000),)),_expect())
    assert not result.success


def test_ambiguous_geometry_candidates_are_not_arbitrarily_selected(tmp_path):
    path=_compile(tmp_path,(('cut-a','deck-a',1000),('cut-b','deck-a',1000)))
    result=check_generated_ifc(path,_expect())
    assert not result.success
    assert 'FLOOR_OPENING_BINDING_AMBIGUOUS' in {i['code'] for i in result.issues}


def test_one_actual_opening_cannot_satisfy_two_expected_openings(tmp_path):
    expectation=_expect(); expectation['floor_openings']['other-cut']=deepcopy(expectation['floor_openings']['expected-cut'])
    result=check_generated_ifc(_compile(tmp_path),expectation)
    assert not result.success
    assert 'FLOOR_OPENING_BINDING_REUSED' in {i['code'] for i in result.issues}


@pytest.mark.parametrize('x',[1001,1020,1100,2500])
def test_same_size_different_position_does_not_bind(tmp_path,x):
    assert not check_generated_ifc(_compile(tmp_path,(('actual-cut','deck-a',x),)),_expect()).success


def test_multiple_openings_on_one_host_bind_independently(tmp_path):
    path=_compile(tmp_path,(('cut-a','deck-a',1000),('cut-b','deck-a',2700)))
    expectation=_expect(); second=deepcopy(expectation['floor_openings']['expected-cut'])
    second['bbox']['x']=[2.3,3.1]; expectation['floor_openings']['expected-other']=second
    result=check_generated_ifc(path,expectation)
    assert result.success,result.issues
    assert len(result.metrics['floor_openings'])==2


@pytest.mark.parametrize('duplicate',['actual-cut','deck-a'])
def test_duplicate_reopened_identities_fail_closed(tmp_path,duplicate):
    path=_compile(tmp_path,(('actual-cut','deck-a',1000),('cut-b','deck-a',2700)))
    model=ifcopenshell.open(str(path)); old='cut-b' if duplicate=='actual-cut' else 'deck-b'
    for prop in model.by_type('IfcPropertySingleValue'):
        if prop.Name=='BimJsonId' and prop.NominalValue.wrappedValue==old:
            prop.NominalValue.wrappedValue=duplicate
    model.write(str(path))
    result=check_generated_ifc(path,_expect('actual-cut'))
    assert not result.success


@pytest.mark.parametrize('explicit',[False,True])
@pytest.mark.parametrize('version',['1.1','1.2'])
def test_geometry_projection_versions_source_identity_and_singular_provenance(explicit,version):
    opening={'bounds':{'x':[600,1400],'y':[1000,2000]}}
    if explicit: opening['id']='chosen-cut'
    brief={'known_facts':{'floor_slabs':[{'id':'deck-a','storey':'level-a','top_elevation_mm':3200,
                 'thickness_mm':200,'bounds':{'x':[0,4000],'y':[0,4000]},'opening':opening}]}}
    facts={'storeys':[{'id':'level-a','elevation_mm':3200}],'slabs':deepcopy(brief['known_facts']['floor_slabs'])}
    original=deepcopy(facts)
    result=build_design_geometry_expectation(case_id='fixture',design_brief=brief,expected_facts=facts,
        schema_version=f'text2ifc/design-geometry-expectation/{version}')
    assert result['schema_version']==f'text2ifc/design-geometry-expectation/{version}'
    record=next(iter(result['floor_openings'].values()))
    assert record['identity_source']==('explicit' if explicit else 'derived')
    assert record['source_fact_refs']==['/known_facts/floor_slabs/0/opening']
    assert original==facts


@pytest.mark.parametrize('problem',['duplicate', 'missing_bounds'])
def test_projection_never_silently_drops_an_opening_obligation(problem):
    opening={'id':'explicit-cut','bounds':{'x':[600,1400],'y':[1000,2000]}}
    if problem=='missing_bounds': opening.pop('bounds')
    slab={'id':'deck-a','storey':'level-a','top_elevation_mm':3200,
          'thickness_mm':200,'bounds':{'x':[0,4000],'y':[0,4000]},'openings':[opening]}
    slabs=[slab]
    if problem=='duplicate':
        second=deepcopy(slab); second['id']='deck-b'; slabs.append(second)
    brief={'known_facts':{'floor_slabs':slabs}}
    facts={'slabs':deepcopy(slabs)}
    result=build_design_geometry_expectation(case_id='fixture',design_brief=brief,expected_facts=facts)
    assert result['unresolved'], 'Every supplied obligation must be represented or explicitly blocked'


def test_explicit_identity_matches_correct_host_and_geometry(tmp_path):
    result=check_generated_ifc(_compile(tmp_path),_expect('actual-cut',source='explicit'))
    assert result.success,result.issues
    assert result.metrics['floor_openings']['actual-cut']['binding_basis']=='explicit_identity'


@pytest.mark.parametrize('host',['deck-a','deck-b'])
def test_v12_retains_floor_opening_host_check(tmp_path,host):
    expectation=_expect('actual-cut',source='explicit')
    expectation['schema_version']='text2ifc/design-geometry-expectation/1.2'
    result=check_generated_ifc(_compile(tmp_path,(('actual-cut',host,1000),)),expectation)
    assert result.success == (host=='deck-a')


@pytest.mark.parametrize('delta,valid',[(.0996,True),(.1,False),(.1004,False)])
def test_v12_space_gate_uses_strict_point_one_mm(tmp_path,delta,valid):
    path=_compile(tmp_path)
    expectation={'schema_version':'text2ifc/design-geometry-expectation/1.2','walls':{},'tolerance':.0001,
        'spaces':{'deck-a':{'bbox':{'x':[delta/1000,4+delta/1000],'y':[0,4],'z':[3,3.2]}}}}
    assert check_generated_ifc(path,expectation).success == valid
