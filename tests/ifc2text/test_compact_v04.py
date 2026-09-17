"""Compact text contracts: precision, no entity loss, immutable tables, model prose."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import pytest
from text2ifc_ifc2text.compact import compact_description, mm1, narrative_context, validate_narration


def facts():
    return {'source':{'path':'private/source.ifc'}, 'storeys':[{'label':'S01','name':'基准', 'elevation_mm':1234.56,
        'spaces':[], 'derived_spaces':[], 'walls':[{'label':'W001','source_global_id':'secret', 'storey':'S01',
        'axis_start_mm':[0,0,1234.56], 'axis_end_mm':[4000,0,1234.56], 'thickness_mm':200,'height_mm':3000,
        'bounds_mm':{'x':[0,4000],'y':[-100,100],'z':[1234.56,4234.56]},'materials':[]}],
        'doors':[], 'windows':[], 'openings':[], 'stairs':[], 'slabs':[], 'coverings':[]}],
        'unassigned':{},'issues':[], 'unrepresented_classes':{}}


def test_precision_mm_one_decimal_and_original_immutable():
    assert mm1(1234.56)=='1234.6'
    assert mm1(-0.01)=='0.0'
    assert mm1(None)=='未确认'
    f=facts(); before=copy.deepcopy(f)
    text=compact_description(f)
    assert f==before
    assert '1234.6' in text and '毫米' in text and 'private/source' not in text and 'secret' not in text
    assert text.count('|W001|')==1
    assert text.index('### 房间')<text.index('|墙体|')<text.index('### 材料')


def test_many_elements_no_cardinality_cutoff():
    f=facts(); w=f['storeys'][0]['walls'][0]
    f['storeys'][0]['walls']=[{**w,'label':f'W{n:03d}'} for n in range(1,181)]
    text=compact_description(f)
    assert '|W180|' in text
    assert sum(line.startswith('|W') for line in text.splitlines())==180


def test_unassigned_and_missing_materials_not_dropped():
    f=facts(); w=copy.deepcopy(f['storeys'][0]['walls'][0]); w['label']='W900'; w['storey']=None
    f['unassigned']={'walls':[w]}
    text=compact_description(f)
    assert '|W900|' in text and '归属未确认' in text and '材料关联未确认' in text


def test_narration_unknown_floor_and_added_numbers_rejected():
    ctx=narrative_context(facts())
    good={'overview':'本说明按楼层组织，房间信息未确认的部分直接列出构件。','storey_notes':[{'storey':'S01','text':'本层列出墙体位置和尺寸，材料关联保持未确认。'}]}
    validate_narration(good,ctx)
    bad=copy.deepcopy(good); bad['storey_notes'][0]['storey']='S99'
    with pytest.raises(ValueError): validate_narration(bad,ctx)
    bad=copy.deepcopy(good); bad['overview']='这栋楼高99999毫米。'
    with pytest.raises(ValueError): validate_narration(bad,ctx)


def test_opening_and_filling_relations_preserved_without_double_creation():
    f=facts(); s=f['storeys'][0]
    s['openings']=[{'label':'O001','host_wall':'W001','dimensions_mm':{'width':900,'height':2100,'depth':200},
        'host_position_mm':{'center_offset_mm':2000,'sill_height_mm':0,'normal_offset_mm':0},'filling':'D001'}]
    s['doors']=[{'label':'D001','opening':'O001','host_wall':'W001','overall_width_mm':900,'overall_height_mm':2100}]
    text=compact_description(f)
    assert sum(line.startswith('|O001|') for line in text.splitlines())==1
    assert sum(line.startswith('|D001|') for line in text.splitlines())==1
    assert '|W001|900.0×2100.0×200.0|2000.0,0.0,0.0|D001|' in text and '重复' in text
