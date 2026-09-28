"""Frozen checks for 0.1 mm wall comparison and full-scene frame preservation."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import numpy as np
import pytest
import ifcopenshell
from text2ifc_compiler import compile_document
from text2ifc_ifc2text.wall_compare_v09 import WALL_TOLERANCE_MM, compare_wall_entities
from scripts.ifc2text.check_wall_context_v09 import merge_wall_representation


def graph():
    doc=json.loads(Path('tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    doc['schema_version']='bim-json/2.3'
    return doc


def wall(doc):
    return next(e for e in doc['entities'] if e['id']=='wall-1')


def compile_wall(doc,path):
    assert compile_document(doc,path).success
    model=ifcopenshell.open(str(path))
    return model,model.by_type('IfcWall')[0]


@pytest.mark.parametrize('shift,expected',[(0.,True),(.049,True),(.101,False),(20.,False)])
def test_world_position_tolerance_never_aligns_away_translation(tmp_path,shift,expected):
    a=graph(); b=copy.deepcopy(a)
    wall(b)['attributes']['ObjectPlacement']['origin'][0]+=shift
    ma,wa=compile_wall(a,tmp_path/'a.ifc');mb,wb=compile_wall(b,tmp_path/'b.ifc')
    r=compare_wall_entities(wa,wb)
    assert WALL_TOLERANCE_MM==.1
    assert r['tolerance_mm']==.1 and r['alignment']=='none'
    assert r['before_openings']['pass'] is expected


def test_opening_removed_is_detected_even_with_identical_outer_bounds(tmp_path):
    a=graph();b=copy.deepcopy(a)
    b['entities']=[e for e in b['entities'] if e['id'] not in {'opening-1','door-1'}]
    b['relationships']=[]  # Remove the void and its filling together; keep a valid IFC.
    ma,wa=compile_wall(a,tmp_path/'a.ifc');mb,wb=compile_wall(b,tmp_path/'b.ifc')
    r=compare_wall_entities(wa,wb)
    assert r['before_openings']['pass']
    assert not r['with_openings']['pass']
    assert any(s['distance_mm']>.1 for s in r['with_openings']['sections'] if s.get('distance_mm') is not None)


def test_rebase_preserves_host_frame_and_every_unrelated_record(tmp_path):
    a=graph();donor=copy.deepcopy(a)
    placement=wall(donor)['attributes']['ObjectPlacement']
    placement['origin']=[0.,0.,0.]
    placement['ref_direction']=[1.,1.,0.]
    wall(donor)['attributes']['Representation']['profile']={'kind':'polygon','points':[[0,-100],[4000,-100],[3900,100],[100,100],[0,-100]]}
    originals=copy.deepcopy((a,donor))
    merged=merge_wall_representation(a,'wall-1',donor,'wall-1',rebase=True)
    assert (a,donor)==originals
    assert wall(merged)['attributes']['ObjectPlacement']==wall(a)['attributes']['ObjectPlacement']
    assert merged['relationships']==a['relationships']
    assert [e for e in merged['entities'] if e['id']!='wall-1']==[e for e in a['entities'] if e['id']!='wall-1']
    md,wd=compile_wall(donor,tmp_path/'donor.ifc');mm,wm=compile_wall(merged,tmp_path/'merged.ifc')
    r=compare_wall_entities(wd,wm)
    assert r['before_openings']['pass']
    naive=merge_wall_representation(a,'wall-1',donor,'wall-1',rebase=False)
    mn,wn=compile_wall(naive,tmp_path/'naive.ifc')
    assert not compare_wall_entities(wd,wn)['before_openings']['pass']


def test_wrong_target_and_invalid_tolerance_rejected(tmp_path):
    with pytest.raises(ValueError):merge_wall_representation(graph(),'missing',graph(),'wall-1')
    m,w=compile_wall(graph(),tmp_path/'a.ifc')
    with pytest.raises(ValueError):compare_wall_entities(w,w,tolerance_mm=float('nan'))


def test_existing_material_contract_rejects_polygon_even_when_layer_sum_is_correct():
    from text2ifc_contract.materials import validate_materials
    doc=graph();w=wall(doc)
    w['materials']=[{'kind':'material_layer_set_usage','layer_set_name':'test','direction':'AXIS2','direction_sense':'POSITIVE','offset_from_reference_line':-100.,'layers':[{'name':'A','thickness':200.}]}]
    assert not validate_materials(doc)
    w['attributes']['Representation']['profile']={'kind':'polygon','points':[[-2500,-100],[2500,-100],[2400,100],[-2400,100],[-2500,-100]]}
    assert [i.code for i in validate_materials(doc)]==['MATERIAL_LAYER_THICKNESS_MISMATCH']


def test_existing_basic_filling_contract_explicitly_limits_host_to_rectangle():
    from text2ifc_contract.basic_filling import validate_basic_filling_document
    doc=graph();door=next(e for e in doc['entities'] if e['id']=='door-1')
    door['attributes']['Representation']={'kind':'basic_filling','template_id':'door-left','template_version':'text2ifc/basic-filling/1.0','width':900.,'height':2100.,'depth':100.}
    assert not validate_basic_filling_document(doc)
    wall(doc)['attributes']['Representation']['profile']={'kind':'polygon','points':[[-2500,-100],[2500,-100],[2400,100],[-2400,100],[-2500,-100]]}
    issues=validate_basic_filling_document(doc)
    assert len(issues)==1 and 'rectangular host' in issues[0].message


def test_wall_policy_does_not_silently_apply_20mm_to_walls():
    from text2ifc_ifc2text.wall_compare_v09 import compare_with_wall_policy
    w={'label':'W','storey':'S','bounds_mm':{'x':[0.,100.],'y':[0.,20.],'z':[0.,100.]}}
    source={'storeys':[{'label':'S','elevation_mm':0.,'walls':[w]}],'unassigned':{}}
    candidate=copy.deepcopy(source)
    candidate['storeys'][0]['walls'][0]['bounds_mm']['x']=[.2,100.2]
    report=compare_with_wall_policy(source,candidate)
    assert report['categories']['walls']['matched'][0]['geometry_outside_tolerance']
    assert report['categories']['walls']['matched'][0]['scalar_tolerance_mm']==.1
