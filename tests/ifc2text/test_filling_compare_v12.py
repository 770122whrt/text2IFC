"""Source/output Body comparison must see internal geometry, not only its box."""
import copy

import ifcopenshell
import ifcopenshell.util.unit
import pytest

from tests.compiler.test_component_geometry_v26 import document, rep, position
from text2ifc_compiler.compiler import compile_document


def product(tmp_path,doc,name):
    path=tmp_path/(name+'.ifc')
    result=compile_document(doc,path)
    assert result.success,result
    model=ifcopenshell.open(str(path))
    return model,model.by_type('IfcWindow')[0],path


@pytest.mark.parametrize('change,passed',[('unchanged',True),('filled-hole',False),('missing-slat',False),
    ('angle',False),('half-mm',True),('one-mm',True),('over-one-mm',False)])
def test_actual_full_body_detects_internal_changes_and_preserves_tolerance(tmp_path,change,passed):
    from text2ifc_ifc2text.filling_compare_v12 import compare_filling_geometry
    source_doc=document();rep(source_doc)['parts'][1]['repeat']['count']=3
    candidate=copy.deepcopy(source_doc)
    if change=='filled-hole':rep(candidate)['definitions'][0]['profile'].pop('holes')
    elif change=='missing-slat':rep(candidate)['parts'][1]['repeat']['count']=2
    elif change=='angle':rep(candidate)['parts'][1]['placement']['ref_direction']=[0,-1,0]
    elif change in {'half-mm','one-mm','over-one-mm'}:
        candidate['entities'][-1]['attributes']['ObjectPlacement']['origin'][0]={'half-mm':.5,'one-mm':1.,'over-one-mm':1.0001}[change]
    a,source,_=product(tmp_path,source_doc,'source');b,target,_=product(tmp_path,candidate,'candidate')
    before_a=a.to_string();before_b=b.to_string()
    result=compare_filling_geometry(source,target)
    assert result['pass']==passed,result
    assert not result['unassessed']
    assert a.to_string()==before_a and b.to_string()==before_b


def test_equivalent_partition_and_metre_units_compare_as_same_occupied_geometry(tmp_path):
    from text2ifc_ifc2text.filling_compare_v12 import compare_filling_geometry
    doc=document();r=rep(doc)
    r['definitions']=[{'id':'box','profile':{'kind':'rectangle','x':20,'y':10},
                      'position':position(),'direction':[0,0,1],'depth':100}]
    r['parts']=[{'id':'panel','role':'panel','geometry_refs':['box'],'placement':position()}]
    a,source,_=product(tmp_path,doc,'source')
    a=ifcopenshell.util.unit.convert_file_length_units(a,'METER');source=a.by_type('IfcWindow')[0]
    candidate=copy.deepcopy(doc);r=rep(candidate)
    other=copy.deepcopy(r['definitions'][0]);other['id']='box2';r['definitions'].append(other)
    r['parts'][0]['geometry_refs'].append('box2')
    for definition,offset in zip(r['definitions'],[-5,5]):
        definition['profile']['x']=10;definition['position']['origin'][0]=offset
    b,target,_=product(tmp_path,candidate,'candidate')
    result=compare_filling_geometry(source,target)
    assert result['pass'],result


def test_unknown_body_item_is_unassessed_instead_of_filtered_out(tmp_path):
    from text2ifc_ifc2text.filling_compare_v12 import compare_filling_geometry
    a,source,_=product(tmp_path,document(),'source')
    b,target,_=product(tmp_path,document(),'candidate')
    body=source.Representation.Representations[0]
    body.Items=(*body.Items,a.createIfcBlock(a.createIfcAxis2Placement3D(
        a.createIfcCartesianPoint((0.,0.,0.)),None,None),10.,10.,10.))
    result=compare_filling_geometry(source,target)
    assert result['unassessed'] and result['pass'] is False
    assert 'IfcBlock' in result['reason']


def test_building_comparator_includes_internal_filling_geometry(tmp_path):
    from text2ifc_ifc2text.precision_compare_v12 import compare_roundtrip
    a,source,source_path=product(tmp_path,document(),'source')
    candidate=document();rep(candidate)['definitions'][0]['profile'].pop('holes')
    b,target,target_path=product(tmp_path,candidate,'candidate')
    result=compare_roundtrip(source_path,target_path)
    row=result['categories']['windows']['matched'][0]
    assert row['bbox_coordinate_max_delta_mm']<1e-6
    assert not row['filling_geometry']['pass'] and row['geometry_outside_tolerance']
    assert result['status']['evaluated_scope_consistent'] is False
