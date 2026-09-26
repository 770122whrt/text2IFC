"""Same world opening under different local frames; retain real defect detection."""
import copy
import ifcopenshell
import numpy as np
import pytest
from tests.compiler.test_component_geometry_v26 import document, position
from text2ifc_compiler.compiler import compile_document


def opening_document():
    doc=document();doc['entities'].pop()
    storey=next(e['id'] for e in doc['entities'] if e['ifc_class']=='IfcBuildingStorey')
    doc['entities'].append(dict(id='host',ifc_class='IfcWall',property_sets={},
        attributes=dict(Name='Wall',ObjectPlacement=dict(relative_to=storey,**position()),
            Representation=dict(kind='extruded_profile',profile=dict(kind='rectangle',x=4000,y=500),
                                direction=[0,0,1],depth=3000)),provenance={'source':'test'}))
    doc['entities'].append(dict(id='opening',ifc_class='IfcOpeningElement',property_sets={},
        attributes=dict(Name='Opening',ObjectPlacement=dict(relative_to=storey,**position((730,-100,0))),
            Representation=dict(kind='extruded_profile',profile=dict(kind='rectangle',x=800,y=220),
                                direction=[0,0,1],depth=2050)),provenance={'source':'test'}))
    doc['relationships'].append(dict(id='void',ifc_class='IfcRelVoidsElement',
        attributes=dict(RelatingBuildingElement='host',RelatedOpeningElement='opening'),provenance={'source':'test'}))
    return doc


def pair(tmp_path,angle,shift=0,notch=False):
    source=opening_document();candidate=copy.deepcopy(source)
    a=candidate['entities'][-1]['attributes'];theta=np.deg2rad(angle)
    rotation=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
    points=[[-400,-110],[400,-110],[400,110],[-400,110],[-400,-110]]
    if notch:points=[[-400,-110],[400,-110],[400,110],[40,110],[40,50],[-40,50],[-40,110],[-400,110],[-400,-110]]
    a['Representation']['profile']=dict(kind='polygon',points=[(rotation.T@p).tolist() for p in points])
    a['ObjectPlacement']['ref_direction']=[np.cos(theta),np.sin(theta),0]
    a['ObjectPlacement']['origin'][0]+=shift
    for name,doc in [('source',source),('candidate',candidate)]:
        result=compile_document(doc,tmp_path/(name+'.ifc'));assert result.success,result
    return tmp_path/'source.ifc',tmp_path/'candidate.ifc'


@pytest.mark.parametrize('angle',[0,37,90,157])
def test_rotated_profile_frame_does_not_change_world_geometry(tmp_path,angle):
    from text2ifc_ifc2text.precision_compare_v13 import compare_roundtrip
    source,candidate=pair(tmp_path,angle);before=[p.read_bytes() for p in (source,candidate)]
    report=compare_roundtrip(source,candidate)
    row=report['categories']['openings']['matched'][0]
    assert row['opening_geometry']['pass'] and not row['geometry_outside_tolerance']
    assert row['opening_geometry']['sampled_surface_distance_mm']<1e-6
    assert 'profile_dimension_deltas_mm' in row
    if angle==90:
        from text2ifc_ifc2text.precision_compare_v12 import compare_roundtrip as old_compare
        old=old_compare(source,candidate)
        assert old['categories']['openings']['matched'][0]['geometry_outside_tolerance']
        assert old['categories']['openings']['missing']==report['categories']['openings']['missing']
    assert [p.read_bytes() for p in (source,candidate)]==before


@pytest.mark.parametrize('shift,expected',[(1.,True),(1.001,False),(-2.,False)])
def test_one_mm_boundary_is_not_relaxed(tmp_path,shift,expected):
    from text2ifc_ifc2text.precision_compare_v13 import compare_roundtrip
    source,candidate=pair(tmp_path,37,shift)
    row=compare_roundtrip(source,candidate)['categories']['openings']['matched'][0]
    assert row['opening_geometry']['pass'] is expected
    assert row['geometry_outside_tolerance'] is (not expected)


def test_same_bbox_does_not_hide_notch(tmp_path):
    from text2ifc_ifc2text.precision_compare_v13 import compare_roundtrip
    source,candidate=pair(tmp_path,90,notch=True)
    row=compare_roundtrip(source,candidate)['categories']['openings']['matched'][0]
    assert row['bbox_coordinate_max_delta_mm']<1e-6
    assert not row['opening_geometry']['pass'] and row['geometry_outside_tolerance']


def test_absent_geometry_is_unassessed_and_never_passes(tmp_path):
    from text2ifc_ifc2text.opening_compare_v13 import compare_opening_geometry
    source,candidate=pair(tmp_path,90)
    a=ifcopenshell.open(str(source)).by_type('IfcOpeningElement')[0]
    model=ifcopenshell.open(str(candidate));b=model.by_type('IfcOpeningElement')[0];b.Representation=None
    result=compare_opening_geometry(a,b)
    assert result['unassessed'] and not result['pass']


def test_source_units_are_converted_before_one_mm_comparison(tmp_path):
    import ifcopenshell.util.unit
    from text2ifc_ifc2text.opening_compare_v13 import compare_opening_geometry
    source,candidate=pair(tmp_path,37)
    original=ifcopenshell.open(str(source));converted=ifcopenshell.util.unit.convert_file_length_units(original,'METER')
    rebuilt=ifcopenshell.open(str(candidate))
    result=compare_opening_geometry(converted.by_type('IfcOpeningElement')[0],rebuilt.by_type('IfcOpeningElement')[0])
    assert result['pass'] and result['sampled_surface_distance_mm']<1e-6
