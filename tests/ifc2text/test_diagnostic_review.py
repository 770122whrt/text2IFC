"""Frozen failures: containment is not deletion; colocated voids need host context."""
from __future__ import annotations

import copy
import pytest


def item(label, x=0.0, *, floor='S01', host=None, width=500.0):
    value = {'label':label, 'storey':floor, 'source_global_id':'private-'+label,
             'bounds_mm':{'x':[x,x+width], 'y':[0.,200.], 'z':[0.,2000.]},
             'overall_width_mm':width, 'overall_height_mm':2000.,
             'materials':[], 'measurement_method':'reference_axis'}
    if host is not None:
        value['host_wall'] = host
    return value


def facts(**categories):
    return {'storeys':[{'label':'S01','elevation_mm':0.,**categories},
                       {'label':'S02','elevation_mm':3000.}], 'unassigned':{},
            'unrepresented_classes':{}}


def compare(a,b):
    from text2ifc_ifc2text.diagnostic_review import compare_observations
    return compare_observations(a,b)


def test_changed_containment_matches_geometry_and_reports_relation():
    a=facts(windows=[item('A',floor='S02')]); b=facts(windows=[item('B',floor='S01')])
    r=compare(a,b)
    assert r['summary']['missing']==r['summary']['extra']==0
    assert len(r['categories']['windows']['matched'])==1
    assert any(v['relation']=='storey' for v in r['relation_differences'])


def test_colocated_openings_match_host_not_label_or_iteration_order():
    a=facts(walls=[item('WA',0),item('WB',2000)],
            openings=[item('OA',1000,host='WA'),item('OB',1000,host='WB')])
    b=facts(walls=[item('X',0),item('Y',2000)],
            openings=[item('FIRST',1000,host='Y'),item('SECOND',1000,host='X')])
    r=compare(a,b)
    mapping={v['source']:v['candidate'] for v in r['categories']['openings']['matched']}
    assert mapping=={'OA':'SECOND','OB':'FIRST'}
    assert not r['relation_differences']


def test_material_reference_metadata_is_separate_from_substance():
    a=item('A'); b=item('B')
    a['materials']=[{'kind':'material_layer_set_usage','name':'source layer name',
        'layers':[{'name':' Brick ','thickness_mm':200}], 'offset_mm':100,'direction_sense':'NEGATIVE'}]
    b['materials']=[{'kind':'material_layer_set_usage','name':'new layer name',
        'layers':[{'name':'Brick','thickness_mm':200}], 'offset_mm':-100,'direction_sense':'POSITIVE'}]
    r=compare(facts(walls=[a]),facts(walls=[b]))
    match=r['categories']['walls']['matched'][0]
    assert match['material_content_difference'] is False
    assert match['material_association_metadata_difference'] is True
    b['materials'][0]['layers'][0]['name']='Concrete'
    assert compare(facts(walls=[a]),facts(walls=[b]))['summary']['material_content_differences']==1


def test_unknown_dimension_not_reported_as_correct():
    a=item('A'); b=item('B'); del a['overall_width_mm']; del b['overall_width_mm']
    r=compare(facts(windows=[a]),facts(windows=[b]))
    assert any('overall_width_mm' in v['fields'] for v in r['unassessed'])
    assert r['whole_building_equivalence_certified'] is False


def test_missing_extra_shift_and_size_are_detected():
    a=facts(doors=[item('A'),item('C',5000)])
    b=facts(doors=[item('B',100,width=600),item('D',10000)])
    r=compare(a,b)
    assert r['summary']['missing']==1 and r['summary']['extra']==1
    assert r['summary']['geometric_deviations']==1


def test_guid_changes_and_input_order_do_not_control_matching():
    a=facts(windows=[item('A'),item('C',900)])
    b=copy.deepcopy(a)
    for n,i in enumerate(b['storeys'][0]['windows']):
        i['label']='REBUILT'+str(n); i['source_global_id']='new-guid'+str(n)
    b['storeys'][0]['windows'].reverse()
    before=copy.deepcopy((a,b)); r=compare(a,b)
    assert r['summary']['geometric_deviations']==0
    assert (a,b)==before


def test_identical_duplicate_shapes_are_marked_ambiguous():
    r=compare(facts(windows=[item('A'),item('B')]),facts(windows=[item('C'),item('D')]))
    assert r['matching_ambiguities']


def test_same_bbox_different_room_outline_is_detected():
    a=item('A'); b=item('B')
    def fp(points):
        return {'status':'measured_projection','polygons':[{'exterior_xy_mm':points,'holes_xy_mm':[]}]}
    a['footprint']=fp([[0,0],[500,0],[500,200],[0,200],[0,0]])
    b['footprint']=fp([[0,0],[500,0],[500,100],[100,100],[100,200],[0,200],[0,0]])
    r=compare(facts(spaces=[a]),facts(spaces=[b]))
    assert r['categories']['spaces']['matched'][0]['outline_hausdorff_mm']>20
    assert r['summary']['geometric_deviations']==1
